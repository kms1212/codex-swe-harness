import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from harness_v0.core import Ledger
from harness_v0.permissions import decide

ROOT = Path(__file__).resolve().parents[1]


class InstructionTests(unittest.TestCase):
    def _installer(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("install_global", ROOT / "scripts/install_global.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_platform_fragments_and_merge(self):
        installer = self._installer()
        for system, selected in (("Darwin", "macos.md"), ("Linux", "linux.md")):
            rendered, fragments = installer.render_instructions(ROOT, system, "revision-one")
            self.assertEqual(fragments, ["common.md", selected])
            self.assertIn("Global SWE harness", rendered)
            self.assertEqual("`/tmp`" in rendered, system == "Darwin")
            first = installer.merge_instructions("My own instruction.\n", rendered)
            self.assertIn("My own instruction.", first)
            self.assertEqual(installer.merge_instructions(first, rendered), first)
            update, _ = installer.render_instructions(ROOT, system, "revision-two")
            second = installer.merge_instructions(first, update)
            self.assertIn("revision-two", second)
            self.assertNotIn("revision-one", second)
            self.assertEqual(second.count(installer.START), 1)
        with self.assertRaises(ValueError):
            installer.os_fragment("Plan9")

    def test_clean_install_reinstall_update_and_revision(self):
        installer = self._installer()
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "source"
            home = base / "codex"
            source.mkdir()
            files = subprocess.check_output(["git", "-C", str(ROOT), "ls-files", "-co", "--exclude-standard"], text=True).splitlines()
            for name in files:
                src = ROOT / name
                if src.is_file():
                    dest = source / name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(src.read_bytes())
            subprocess.run(["git", "init", "-q", str(source)], check=True)
            subprocess.run(["git", "-C", str(source), "add", "."], check=True)
            subprocess.run(["git", "-C", str(source), "-c", "user.name=CI", "-c", "user.email=ci@example.test", "commit", "-qm", "initial"], check=True)
            home.mkdir()
            (home / "AGENTS.md").write_text("Personal instruction.\n")
            first = installer.install(source, home, "Darwin")
            first_content = (home / "AGENTS.md").read_text()
            self.assertEqual(first["host_os"], "Darwin")
            self.assertEqual(first["revision"], subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip())
            second = installer.install(source, home, "Darwin")
            self.assertEqual(first_content, (home / "AGENTS.md").read_text())
            self.assertEqual(second["revision"], first["revision"])
            self.assertIn("PermissionRequest", json.loads((home / "hooks.json").read_text())["hooks"])
            (source / "runtime/instructions/macos.md").write_text("Updated macOS instruction.\n")
            subprocess.run(["git", "-C", str(source), "add", "."], check=True)
            subprocess.run(["git", "-C", str(source), "-c", "user.name=CI", "-c", "user.email=ci@example.test", "commit", "-qm", "update"], check=True)
            third = installer.install(source, home, "Darwin")
            final = (home / "AGENTS.md").read_text()
            self.assertNotEqual(third["revision"], first["revision"])
            self.assertIn("Updated macOS instruction.", final)
            self.assertIn("Personal instruction.", final)
            self.assertNotIn("because Codex sandbox", final)
            self.assertEqual(third["revision"], json.loads((home / "harness-v0/installation.json").read_text())["revision"])
            for name, expected in third["modules"].items():
                self.assertEqual(expected, installer.sha(Path(third["installed_package"]) / name))


class PermissionTests(unittest.TestCase):
    def test_live_delegation_and_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = Ledger(Path(directory))
            ledger.create("parent-thread", "task", "task")
            ledger.update("work_items", {"work_item_id": "work-1", "parent_id": "parent-thread", "objective": "child work", "owner": "child-thread", "status": "ACTIVE", "dependencies": [], "produced_changes": [], "verification_refs": [], "evidence_refs": [], "remaining_issues": [], "integration_notes": ""})
            ledger.update("delegated_work", {"id": "work-1", "work_item_id": "work-1", "owner": "child-thread", "expected_result": "answer", "return_destination": "parent-thread", "status": "DISPATCHED", "result_refs": [], "consumed_refs": [], "integration_refs": [], "aliases": ["/root/child", "child"], "return_aliases": ["/root"]})
            base = {"hook_event_name": "PermissionRequest", "tool_name": "mcp__codex_app__send_message_to_thread", "session_id": "parent-thread", "tool_use_id": "request-1"}
            outgoing = {**base, "tool_input": {"threadId": "child-thread", "prompt": "Please check this."}}
            self.assertEqual(decide(outgoing, ledger)["hookSpecificOutput"]["decision"], {"behavior": "allow"})
            returned = {**base, "agent_id": "child-thread", "tool_use_id": "request-2", "tool_input": {"threadId": "parent-thread", "prompt": "Checked; here is the result."}}
            self.assertIsNotNone(decide(returned, ledger))
            self.assertIsNotNone(decide({**base, "tool_name": "collaborationsend_message", "tool_input": {"target": "child", "message": "Follow up"}}, ledger))
            self.assertIsNotNone(decide({**base, "tool_name": "collaborationsend_message", "agent_id": "child-thread", "tool_input": {"target": "/root", "message": "Result"}}, ledger))
            self.assertIsNone(decide({**base, "tool_input": {"threadId": "stranger", "prompt": "hello"}}, ledger))
            self.assertIsNone(decide({**base, "tool_input": {"threadId": "child-thread"}}, ledger))
            self.assertIsNone(decide({**base, "tool_input": "broken"}, ledger))
            events = [e for e in ledger.events() if e["kind"] == "delegated_communication_approved"]
            self.assertEqual([e["data"]["request_id"] for e in events[:2]], ["request-1", "request-2"])
            ledger.transition("delegated_work", "work-1", {"status": "RETURNED", "result_refs": ["request-2"]}, ["request-2"])
            self.assertIsNone(decide(outgoing, ledger))


if __name__ == "__main__":
    unittest.main()
