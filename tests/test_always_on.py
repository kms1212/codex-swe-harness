"""Native lifecycle events must activate the core without harness commands."""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from harness_v0 import always_on
from harness_v0.core import Ledger


class AlwaysOnTests(unittest.TestCase):
    def test_preexisting_instruction_edit_is_not_routed_after_unrelated_code_change(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            project.mkdir()
            subprocess.run(["git", "init", "-q", str(project)], check=True)
            (project / "code.py").write_text("value = 1\n")
            subprocess.run(["git", "-C", str(project), "add", "code.py"], check=True)
            subprocess.run(["git", "-C", str(project), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.test", "commit", "-qm", "base"], check=True)
            (project / "AGENTS.md").write_text("Preexisting local instruction\n")
            base = {"session_id": "test-session-dirty-instruction", "cwd": str(project), "turn_id": "turn-1"}
            with patch.object(always_on, "STATE_HOME", root / "sessions"), patch.object(always_on, "ARCHIVE_HOME", root / "archive"):
                always_on.handle({**base, "hook_event_name": "UserPromptSubmit", "prompt": "Update code only"})
                (project / "code.py").write_text("value = 2\n")
                always_on.handle({**base, "hook_event_name": "PostToolUse", "tool_name": "Bash", "tool_use_id": "edit-1",
                                  "tool_input": {"command": "write code.py"}, "tool_response": {"exit_code": 0, "output": "updated"}})
                always_on.handle({**base, "hook_event_name": "Stop", "stop_hook_active": False})
                ledger = Ledger(root / "sessions" / base["session_id"])
                self.assertEqual(ledger.read()["completion_state"]["instruction_recomposition_required"], [])
                self.assertFalse(any(event["kind"] == "review_requested" for event in ledger.events()))

    def test_pasted_request_attachment_content_enters_ledger(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            attached = root / ".codex/attachments/1234/Pasted text.txt"
            attached.parent.mkdir(parents=True)
            attached.write_text("The substantive SWE request.\n")
            prompt = f"## Request: {attached}\nPasted text contains the user's request."
            with patch.object(always_on.Path, "home", return_value=root):
                resolved = always_on._resolved_request(prompt)
            self.assertIn("The substantive SWE request.", resolved)
            self.assertIn(prompt, resolved)

    def test_preexisting_dirty_files_do_not_create_review_for_read_only_turn(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            project.mkdir()
            subprocess.run(["git", "init", "-q", str(project)], check=True)
            (project / "preexisting.txt").write_text("fixture\n")
            base = {"session_id": "test-session-read-only", "cwd": str(project), "turn_id": "turn-1"}
            with patch.object(always_on, "STATE_HOME", root / "sessions"), patch.object(always_on, "ARCHIVE_HOME", root / "archive"):
                always_on.handle({**base, "hook_event_name": "UserPromptSubmit", "prompt": "Inspect the existing fixture"})
                always_on.handle({**base, "hook_event_name": "PostToolUse", "tool_name": "Bash", "tool_use_id": "read-1",
                                  "tool_input": {"command": "cat preexisting.txt"}, "tool_response": {"exit_code": 0, "output": "fixture"}})
                self.assertIsNone(always_on.handle({**base, "hook_event_name": "Stop", "stop_hook_active": False}))
                ledger = Ledger(root / "sessions" / base["session_id"])
                self.assertFalse(any(event["kind"] == "review_requested" for event in ledger.events()))

    def test_native_spawn_response_string_binds_communication_alias(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = {"session_id": "test-session-alias", "cwd": str(root), "turn_id": "turn-1"}
            with patch.object(always_on, "STATE_HOME", root / "sessions"), patch.object(always_on, "ARCHIVE_HOME", root / "archive"):
                always_on.handle({**base, "hook_event_name": "UserPromptSubmit", "prompt": "Delegate work"})
                always_on.handle({**base, "hook_event_name": "PostToolUse", "tool_name": "collaborationspawn_agent", "tool_use_id": "spawn-1",
                                  "tool_input": {"task_name": "child"}, "tool_response": '{"task_name":"/root/child"}'})
                always_on.handle({**base, "hook_event_name": "SubagentStart", "agent_id": "child-uuid", "agent_type": "default"})
                delegated = Ledger(root / "sessions" / base["session_id"]).read()["delegated_work"][0]
                self.assertEqual(delegated["aliases"], ["/root/child", "child"])
                self.assertEqual(delegated["return_aliases"], ["/root"])

    def test_default_session_home_is_portable_tmp(self):
        self.assertEqual(str(always_on.STATE_HOME), "/tmp/harness-v0-sessions")

    def test_ledger_inspection_does_not_shadow_passing_test(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = {"session_id": "test-session-789", "cwd": str(root), "turn_id": "turn-1"}
            with patch.object(always_on, "STATE_HOME", root / "sessions"), patch.object(always_on, "ARCHIVE_HOME", root / "archive"):
                always_on.handle({**base, "hook_event_name": "UserPromptSubmit", "prompt": "Run a test"})
                for token, command, response in (
                    ("test-pass", "python3 -m unittest discover -v", "Ran 1 test in 0.001s\n\nOK\n"),
                    ("inspect", "python3 - <<'PY'\nprint('test verification_chronology')\nPY", "test verification_chronology"),
                    ("fixture", "cat > /tmp/record.json <<'JSON'\n{\"command_or_tool\":\"python3 -m unittest\"}\nJSON", ""),
                ):
                    always_on.handle({**base, "hook_event_name": "PostToolUse", "tool_name": "Bash", "tool_use_id": token,
                                      "tool_input": {"command": command}, "tool_response": response})
                entries = Ledger(root / "sessions" / base["session_id"]).read()["verification_chronology"]
                self.assertEqual([entry["scope"] for entry in entries], ["test", "tool:Bash", "tool:Bash"])
                self.assertEqual(entries[0]["status"], "PASS")

    def test_natural_prompt_tool_review_and_continuation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            project.mkdir()
            subprocess.run(["git", "init", "-q", str(project)], check=True)
            session = "test-session-123"
            base = {"session_id": session, "cwd": str(project), "turn_id": "turn-1"}
            with patch.object(always_on, "STATE_HOME", root / "sessions"), patch.object(always_on, "ARCHIVE_HOME", root / "archive"):
                start = always_on.handle({**base, "hook_event_name": "SessionStart", "source": "startup"})
                self.assertIn("SessionStart", start["hookSpecificOutput"]["hookEventName"])
                prompt = always_on.handle({**base, "hook_event_name": "UserPromptSubmit", "prompt": "Create a useful note file"})
                self.assertIn("ledger", prompt["hookSpecificOutput"]["additionalContext"])
                ledger = Ledger(root / "sessions" / session)
                self.assertEqual(ledger.read()["original_request"], "Create a useful note file")
                (project / "NOTE.md").write_text("# Note\nUseful content.\n")
                always_on.handle({**base, "hook_event_name": "PostToolUse", "tool_name": "Bash", "tool_use_id": "tool-1",
                    "tool_input": {"command": "cat NOTE.md"}, "tool_response": {"exit_code": 0, "output": "Useful content."}})
                self.assertEqual(len(ledger.read()["verification_chronology"]), 1)
                self.assertTrue((ledger.directory / "raw-tools/tool-1.json").is_file())
                completion = ledger.read()["completion_state"]
                completion["candidate_revision"] = "declared-content-revision"
                ledger.replace("completion_state", completion)
                review_prompt = always_on.handle({**base, "hook_event_name": "Stop", "stop_hook_active": False})
                self.assertEqual(review_prompt["decision"], "block")
                self.assertIn("fresh built-in subagent", review_prompt["reason"])
                state = ledger.read()
                package_hash = state["completion_state"]["pending_review_hash"]
                self.assertTrue(package_hash)
                package_file = next(ledger.directory.glob("*-review-*.json"))
                package = json.loads(package_file.read_text())
                self.assertIn("Useful content.", package["candidate_result"]["aggregate_diff"])
                self.assertEqual(ledger.read()["completion_state"]["candidate_revision"], "declared-content-revision")
                always_on.handle({**base, "hook_event_name": "SubagentStart", "agent_id": "/root/reviewer", "agent_type": "default"})
                self.assertEqual(ledger.read()["work_items"], [])
                result = {"review_id": "native-review-1", "package_hash": package_hash, "reviewer_adapter": "builtin_subagent",
                    "findings": [], "overall_completion_risk": "low", "unresolved_unknowns": []}
                always_on.handle({**base, "hook_event_name": "SubagentStop", "agent_id": "/root/reviewer", "agent_type": "default",
                    "last_assistant_message": json.dumps(result)})
                self.assertIsNone(ledger.read()["completion_state"]["pending_review_hash"])
                self.assertEqual(ledger.read()["reviews"][-1]["review_id"], "native-review-1")
                self.assertTrue(ledger.read()["reviews"][-1]["artifact_fingerprint"])
                self.assertTrue((root / "archive" / session / "state.json").is_file())
                gate = always_on.handle({**base, "hook_event_name": "Stop", "stop_hook_active": False})
                self.assertEqual(gate["decision"], "block")
                self.assertIn("CONTINUE", gate["reason"])
                shutil.rmtree(ledger.directory)
                always_on.handle({**base, "hook_event_name": "SessionStart", "source": "resume"})
                self.assertEqual(Ledger(root / "sessions" / session).read()["reviews"][-1]["review_id"], "native-review-1")

    def test_native_work_return_and_test_result_are_recorded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            project.mkdir()
            base = {"session_id": "test-session-456", "cwd": str(project), "turn_id": "turn-1"}
            with patch.object(always_on, "STATE_HOME", root / "sessions"), patch.object(always_on, "ARCHIVE_HOME", root / "archive"):
                always_on.handle({**base, "hook_event_name": "UserPromptSubmit", "prompt": "Build a Python program with tests"})
                ledger = Ledger(root / "sessions" / base["session_id"])
                always_on.handle({**base, "hook_event_name": "SubagentStart", "agent_id": "child-123", "agent_type": "default"})
                state = ledger.read()
                self.assertEqual(state["work_items"][0]["status"], "ACTIVE")
                self.assertEqual(state["delegated_work"][0]["status"], "DISPATCHED")
                always_on.handle({**base, "hook_event_name": "SubagentStop", "agent_id": "child-123", "agent_type": "default",
                    "last_assistant_message": "Reviewed the edge cases and returned suggestions."})
                state = ledger.read()
                self.assertEqual(state["work_items"][0]["status"], "DONE")
                self.assertEqual(state["delegated_work"][0]["status"], "RETURNED")
                self.assertEqual(state["delegated_work"][0]["result_refs"], ["subagent:child-123"])
                always_on.handle({**base, "hook_event_name": "PostToolUse", "tool_name": "Bash", "tool_use_id": "tests-pass",
                    "tool_input": {"command": "python3 -m unittest discover -s tests -v"},
                    "tool_response": "Ran 3 tests in 0.001s\n\nOK\n"})
                always_on.handle({**base, "hook_event_name": "PostToolUse", "tool_name": "Bash", "tool_use_id": "tests-fail",
                    "tool_input": {"command": "python3 -m unittest discover -s tests -v"},
                    "tool_response": "Ran 3 tests in 0.001s\n\nFAILED (failures=1)\n"})
                self.assertEqual([item["status"] for item in ledger.read()["verification_chronology"][-2:]], ["PASS", "FAIL"])
                self.assertTrue(all(item["expensive"] and item["target_identity"] for item in ledger.read()["verification_chronology"][-2:]))


if __name__ == "__main__":
    unittest.main()
