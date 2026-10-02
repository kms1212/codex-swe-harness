import tempfile
import unittest
import subprocess
from pathlib import Path

from harness import always_on
from harness.completion import evaluate_completion
from harness.core import Ledger
from harness.instructions import instruction_paths


class InstructionRecompositionTests(unittest.TestCase):
    def test_instruction_owner_detection_and_existing_principle_noop(self):
        self.assertEqual(instruction_paths(["AGENTS.md", "runtime/instructions/macos.md", "src/foo.py", "docs/guide.md"]),
                         ["AGENTS.md", "runtime/instructions/macos.md"])
        with tempfile.TemporaryDirectory() as directory:
            ledger = Ledger(Path(directory))
            ledger.create("task", "Apply incident evidence", "The current principle already covers it")
            always_on._observe_instruction_changes(ledger, "same-content", [])
            self.assertEqual(ledger.read()["completion_state"]["instruction_recomposition_required"], [])

    def test_changed_instruction_needs_full_review_and_active_consumer_check(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = Ledger(Path(directory))
            ledger.create("task", "Recompose instructions", "Integrate a new requirement")
            always_on._observe_instruction_changes(ledger, "content-a", ["AGENTS.md"])
            state = ledger.read()
            self.assertEqual(state["completion_state"]["instruction_recomposition_required"], ["AGENTS.md"])
            self.assertIn("INSTRUCTION_RECOMPOSITION_MISSING", [x["code"] for x in evaluate_completion(state)["reasons"]])
            ledger.update("evidence", {"evidence_id": "whole-file", "producer": "test", "operation": "read complete file", "observable_result": "coherent", "scope": "instructions", "chronology_index": 1, "artifact_refs": ["AGENTS.md"]})
            ledger.update("instruction_changes", {"artifact": "AGENTS.md", "target_identity": "content-a", "candidate_revision": "content-a", "requirement": "Generalize test choice", "owner": "root AGENTS.md", "outcome": "integrated", "existing_principle": "Verification and tests", "integration": "Rewrote the existing section", "displaced_guidance": ["incident-specific test rule"], "whole_file_review_ref": "whole-file", "active_check_ref": "fresh-session", "installation_required": True, "installed_revision": "commit-a"})
            self.assertIn("INSTRUCTION_ACTIVE_CHECK_MISSING", [x["code"] for x in evaluate_completion(ledger.read())["reasons"]])
            ledger.update("verification_chronology", {"chronology_index": 1, "action": "consumer read", "command_or_tool": "new Codex session", "scope": "instructions", "observable_result": "loaded", "evidence_ref": "fresh-session", "status": "PASS", "artifact_revision": "content-a", "target_identity": "content-a", "consumer_point": "new session"})
            self.assertNotIn("INSTRUCTION_ACTIVE_CHECK_MISSING", [x["code"] for x in evaluate_completion(ledger.read())["reasons"]])
            completion = ledger.read()["completion_state"]
            completion["instruction_installation_required"] = ["AGENTS.md"]
            completion["instruction_source_revision"] = "commit-a"
            ledger.replace("completion_state", completion)
            self.assertNotIn("INSTRUCTION_INSTALLATION_MISSING", [x["code"] for x in evaluate_completion(ledger.read())["reasons"]])
            completion = ledger.read()["completion_state"]
            completion["instruction_source_revision"] = "commit-b"
            ledger.replace("completion_state", completion)
            self.assertIn("INSTRUCTION_INSTALLATION_MISSING", [x["code"] for x in evaluate_completion(ledger.read())["reasons"]])
            always_on._observe_instruction_changes(ledger, "content-b", ["AGENTS.md"])
            self.assertIn("INSTRUCTION_RECOMPOSITION_MISSING", [x["code"] for x in evaluate_completion(ledger.read())["reasons"]])

    def test_owner_move_new_responsibility_and_continuous_recomposition(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = Ledger(Path(directory))
            ledger.create("task", "Move OS instruction", "Place rules with their owner")
            for revision, outcome, artifact, owner, displaced in [
                ("first", "moved", "AGENTS.md", "runtime/instructions/macos.md", ["macOS path rule in root"]),
                ("second", "new_owner", "runtime/instructions/macos.md", "OS-specific global instruction", []),
            ]:
                always_on._observe_instruction_changes(ledger, revision, [artifact])
                ledger.update("evidence", {"evidence_id": f"read-{revision}", "producer": "test", "operation": "read complete instruction file", "observable_result": "coherent", "scope": artifact, "chronology_index": len(ledger.read()["evidence"])+1, "artifact_refs": [artifact]})
                ledger.update("instruction_changes", {"artifact": artifact, "target_identity": revision, "candidate_revision": revision, "requirement": "Place OS rule with owner", "owner": owner, "outcome": outcome, "existing_principle": "semantic ownership" if outcome == "moved" else "", "integration": "Recomposed current file", "displaced_guidance": displaced, "whole_file_review_ref": f"read-{revision}", "active_check_ref": f"session-{revision}"})
            state = ledger.read()
            self.assertEqual([x["outcome"] for x in state["instruction_changes"]], ["moved", "new_owner"])
            self.assertEqual(len(state["instruction_changes"]), 2)
            self.assertEqual(state["completion_state"]["instruction_recomposition_required"], ["AGENTS.md", "runtime/instructions/macos.md"])

    def test_stop_hook_detects_edit_and_requests_recomposition(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "project"
            project.mkdir()
            subprocess.run(["git", "init", "-q", str(project)], check=True)
            (project / "AGENTS.md").write_text("# Principles\n", encoding="utf-8")
            (project / "scripts").mkdir()
            (project / "scripts/install_global.py").write_text("# installer\n", encoding="utf-8")
            session = "instruction-session-123"
            from unittest.mock import patch
            with patch.object(always_on, "STATE_HOME", Path(directory) / "sessions"), patch.object(always_on, "RECOVERY_HOME", Path(directory) / "archive"):
                base = {"session_id": session, "cwd": str(project), "turn_id": "turn-1"}
                always_on.handle({**base, "hook_event_name": "UserPromptSubmit", "prompt": "Recompose AGENTS.md"})
                (project / "AGENTS.md").write_text("# Principles\nUpdated.\n", encoding="utf-8")
                result = always_on.handle({**base, "hook_event_name": "Stop", "stop_hook_active": False})
                self.assertIn("instruction recomposition", result["reason"])
                completion = Ledger(Path(directory) / "sessions" / session).read()["completion_state"]
                self.assertIn("AGENTS.md", completion["instruction_recomposition_required"])
                self.assertNotIn("AGENTS.md", completion["instruction_installation_required"])
                self.assertIsNone(Ledger(Path(directory) / "sessions" / session).read()["completion_state"]["pending_review_hash"])

    def test_old_local_installation_requirement_can_be_migrated(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = Ledger(Path(directory))
            ledger.create("task", "migrate owner", "Local AGENTS is not installed globally")
            state = ledger.read()
            state["completion_state"]["instruction_installation_required"] = ["AGENTS.md", "runtime/instructions/common.md"]
            ledger._write_state(state)
            completion = ledger.read()["completion_state"]
            completion["instruction_installation_required"] = ["runtime/instructions/common.md"]
            ledger.replace("completion_state", completion)
            self.assertEqual(ledger.read()["completion_state"]["instruction_installation_required"], ["runtime/instructions/common.md"])
            with self.assertRaises(ValueError):
                ledger.replace("completion_state", {**completion, "instruction_installation_required": []})


if __name__ == "__main__":
    unittest.main()
