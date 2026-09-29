import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from harness_v0 import always_on
from harness_v0.completion import evaluate_completion, progress_snapshot
from harness_v0.core import Ledger, initial_state
from harness_v0.optimization import (duplicate_expensive_action, impacted_scopes, parallelizable,
                                     review_path, running_work_value, select_checks, verification_reusable)


def state_for(scope="release", identity="tree-A"):
    state = initial_state("task", "objective", "request")
    state["obligations"] = [{"id": "request", "description": "request", "status": "SATISFIED", "evidence_refs": ["passed"]}]
    state["evidence"] = [{"evidence_id": "passed", "producer": "test", "operation": "run", "observable_result": "passed", "scope": scope, "chronology_index": 1, "artifact_refs": []}]
    state["completion_state"].update(candidate_revision="revision-before-commit", required_verification_scopes=[scope], scope_identities={scope: identity})
    state["verification_chronology"] = [{"chronology_index": 1, "action": "run", "command_or_tool": "full release verification", "scope": scope,
        "observable_result": "passed", "evidence_ref": "passed", "status": "PASS", "artifact_revision": "revision-before-commit",
        "target_identity": identity, "related_inputs": ["module-a", "release-config"], "execution_environment": "macos"}]
    return state


class OptimizationTests(unittest.TestCase):
    def test_commit_only_reuses_release_verification(self):
        state = state_for()
        state["completion_state"]["candidate_revision"] = "revision-after-commit"
        self.assertEqual(evaluate_completion(state)["status"], "COMPLETE")
        state["verification_chronology"].append({"chronology_index": 2, "action": "commit", "command_or_tool": "git commit", "scope": "git-identity",
            "observable_result": "tree unchanged", "evidence_ref": "commit-check", "status": "PASS", "artifact_revision": "revision-after-commit",
            "target_identity": "commit-sha", "related_inputs": []})
        self.assertEqual(evaluate_completion(state)["status"], "COMPLETE")

    def test_stale_identity_and_environment_fail(self):
        state = state_for()
        state["completion_state"]["scope_identities"]["release"] = "tree-B"
        self.assertIn("VERIFICATION_MISSING_OR_FAILING", [x["code"] for x in evaluate_completion(state)["reasons"]])
        state["completion_state"]["scope_identities"]["release"] = "tree-A"
        state["completion_state"]["scope_environments"] = {"release": "linux"}
        self.assertIn("VERIFICATION_MISSING_OR_FAILING", [x["code"] for x in evaluate_completion(state)["reasons"]])
        self.assertFalse(verification_reusable(state["verification_chronology"][0], "tree-B", "anything"))

    def test_unrelated_change_retains_evidence_and_scoped_selection(self):
        state = state_for("module-a-check", "module-a-hash")
        state["completion_state"]["candidate_revision"] = "whole-repo-changed"
        checks = [{"scope": "module-a-check", "related_inputs": ["module-a", "shared-contract"]},
                  {"scope": "module-b-check", "related_inputs": ["module-b"]}]
        self.assertEqual(impacted_scopes(["module-b"], checks), ["module-b-check"])
        self.assertEqual([x["scope"] for x in select_checks(["shared-contract"], checks)], ["module-a-check"])
        self.assertEqual(evaluate_completion(state)["status"], "COMPLETE")

    def test_trivial_and_semantic_review_paths(self):
        self.assertEqual(review_path(["documentation"], deterministic=True), "lightweight")
        self.assertEqual(review_path(["code"]), "scoped_checks")
        self.assertEqual(review_path(["architecture"], deterministic=True), "semantic_review")
        self.assertEqual(review_path(["code"], semantic_risk=True), "semantic_review")

    def test_duplicate_running_and_parallel_work(self):
        passed = {"chronology_index": 1, "command_or_tool": "full release verification", "scope": "release", "target_identity": "tree-A", "execution_environment": "macos", "status": "PASS", "observable_result": "passed"}
        proposed = {**passed, "chronology_index": 2, "expensive": True}
        self.assertEqual(duplicate_expensive_action([passed], proposed), passed)
        self.assertIsNone(duplicate_expensive_action([passed], {**proposed, "target_identity": "tree-B"}))
        running = {"work_item_id": "build", "status": "ACTIVE", "verification_scope": "release", "target_identity": "tree-A", "cancelable": True}
        self.assertEqual(running_work_value(running, [passed]), "cancel_if_possible")
        self.assertEqual(running_work_value({**running, "target_identity": "tree-B"}, [passed]), "continue")
        left = {"work_item_id": "a", "dependencies": [], "write_targets": ["a.py"], "estimated_wall_time": 10, "integration_cost": 2}
        right = {"work_item_id": "b", "dependencies": [], "write_targets": ["b.py"], "estimated_wall_time": 10, "integration_cost": 2}
        self.assertTrue(parallelizable(left, right, priority="speed"))
        self.assertFalse(parallelizable(left, {**right, "dependencies": ["a"]}))
        self.assertFalse(parallelizable(left, {**right, "write_targets": ["a.py"]}))
        state = state_for()
        state["verification_chronology"].append({**proposed, "evidence_ref": "second"})
        self.assertEqual(progress_snapshot(state)["duplicate_expensive_actions"], [[1, 2]])

    def test_content_identity_survives_commit_and_trivial_stop_skips_review(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            project.mkdir()
            subprocess.run(["git", "init", "-q", str(project)], check=True)
            (project / "AGENTS.md").write_text("First line\n")
            subprocess.run(["git", "-C", str(project), "add", "."], check=True)
            subprocess.run(["git", "-C", str(project), "-c", "user.name=CI", "-c", "user.email=ci@example.test", "commit", "-qm", "base"], check=True)
            ledger = Ledger(root / "sessions" / "session-test-123")
            ledger.create("session-test-123", "edit", "add one line")
            before = always_on._candidate(project, ledger)[0]
            (project / "AGENTS.md").write_text("First line\nSecond line\n")
            edited = always_on._candidate(project, ledger)[0]
            self.assertNotEqual(before, edited)
            with patch.object(always_on, "STATE_HOME", root / "sessions"), patch.object(always_on, "ARCHIVE_HOME", root / "archive"):
                response = always_on.handle({"session_id": "session-test-123", "cwd": str(project), "hook_event_name": "Stop", "stop_hook_active": False})
            self.assertIn("CONTINUE", response["reason"])
            self.assertIsNone(ledger.read()["completion_state"]["pending_review_hash"])
            subprocess.run(["git", "-C", str(project), "add", "."], check=True)
            subprocess.run(["git", "-C", str(project), "-c", "user.name=CI", "-c", "user.email=ci@example.test", "commit", "-qm", "line"], check=True)
            committed, remaining, _ = always_on._candidate(project, ledger)
            self.assertEqual(edited, committed)
            self.assertEqual(remaining, [])


if __name__ == "__main__":
    unittest.main()
