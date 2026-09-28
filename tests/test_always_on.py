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
                review_prompt = always_on.handle({**base, "hook_event_name": "Stop", "stop_hook_active": False})
                self.assertEqual(review_prompt["decision"], "block")
                self.assertIn("fresh built-in subagent", review_prompt["reason"])
                state = ledger.read()
                package_hash = state["completion_state"]["pending_review_hash"]
                self.assertTrue(package_hash)
                package_file = next(ledger.directory.glob("*-review-*.json"))
                package = json.loads(package_file.read_text())
                self.assertIn("Useful content.", package["candidate_result"]["aggregate_diff"])
                always_on.handle({**base, "hook_event_name": "SubagentStart", "agent_id": "/root/reviewer", "agent_type": "default"})
                result = {"review_id": "native-review-1", "package_hash": package_hash, "reviewer_adapter": "builtin_subagent",
                    "findings": [], "overall_completion_risk": "low", "unresolved_unknowns": []}
                always_on.handle({**base, "hook_event_name": "SubagentStop", "agent_id": "/root/reviewer", "agent_type": "default",
                    "last_assistant_message": json.dumps(result)})
                self.assertIsNone(ledger.read()["completion_state"]["pending_review_hash"])
                self.assertEqual(ledger.read()["reviews"][-1]["review_id"], "native-review-1")
                self.assertTrue((root / "archive" / session / "state.json").is_file())
                gate = always_on.handle({**base, "hook_event_name": "Stop", "stop_hook_active": False})
                self.assertEqual(gate["decision"], "block")
                self.assertIn("CONTINUE", gate["reason"])
                shutil.rmtree(ledger.directory)
                always_on.handle({**base, "hook_event_name": "SessionStart", "source": "resume"})
                self.assertEqual(Ledger(root / "sessions" / session).read()["reviews"][-1]["review_id"], "native-review-1")


if __name__ == "__main__":
    unittest.main()
