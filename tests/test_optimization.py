import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from harness import always_on
from harness.completion import evaluate_completion, progress_snapshot
from harness.core import Ledger, initial_state
from harness.scheduling import assess
from harness.optimization import (duplicate_expensive_action, impacted_scopes, parallelizable,
                                     review_path, running_work_value, select_checks, select_next_actions, verification_reusable)


def state_for(scope="release", identity="tree-A"):
    state = initial_state("task", "objective", "request")
    state["obligations"] = [{"id": "request", "description": "request", "status": "SATISFIED", "evidence_refs": ["passed"]}]
    state["evidence"] = [{"evidence_id": "passed", "producer": "test", "operation": "run", "observable_result": "passed", "scope": scope, "chronology_index": 1, "artifact_refs": []}]
    inputs = {"module-a": "module-a-hash", "release-config": "config-hash"}
    state["completion_state"].update(candidate_revision="revision-before-commit", required_verification_scopes=[scope], scope_identities={scope: identity}, scope_input_identities={scope: dict(inputs)})
    state["verification_chronology"] = [{"chronology_index": 1, "action": "run", "command_or_tool": "full release verification", "scope": scope,
        "observable_result": "passed", "evidence_ref": "passed", "status": "PASS", "artifact_revision": "revision-before-commit",
        "target_identity": identity, "related_inputs": ["module-a", "release-config"], "input_identities": inputs, "execution_environment": "macos"}]
    return state


class OptimizationTests(unittest.TestCase):
    def test_commit_only_reuses_release_verification(self):
        state = state_for()
        state["completion_state"]["candidate_revision"] = "revision-after-commit"
        self.assertEqual(evaluate_completion(state)["status"], "COMPLETE")
        self.assertEqual(select_next_actions(state)["run_verification"], [])
        self.assertEqual(select_next_actions(state)["reuse_verification"], {"release": "passed"})
        state["verification_chronology"].append({"chronology_index": 2, "action": "commit", "command_or_tool": "git commit", "scope": "git-identity",
            "observable_result": "tree unchanged", "evidence_ref": "commit-check", "status": "PASS", "artifact_revision": "revision-after-commit",
            "target_identity": "commit-sha", "related_inputs": []})
        self.assertEqual(evaluate_completion(state)["status"], "COMPLETE")

    def test_stale_identity_and_environment_fail(self):
        state = state_for()
        state["completion_state"]["scope_identities"]["release"] = "tree-B"
        self.assertIn("VERIFICATION_MISSING_OR_FAILING", [x["code"] for x in evaluate_completion(state)["reasons"]])
        self.assertEqual(select_next_actions(state)["run_verification"], ["release"])
        state["completion_state"]["scope_identities"]["release"] = "tree-A"
        state["completion_state"]["scope_environments"] = {"release": "linux"}
        self.assertIn("VERIFICATION_MISSING_OR_FAILING", [x["code"] for x in evaluate_completion(state)["reasons"]])
        self.assertFalse(verification_reusable(state["verification_chronology"][0], "tree-B", "anything"))

    def test_related_contract_change_invalidates_unchanged_target(self):
        state = state_for("module-a-check", "module-a-hash")
        self.assertEqual(evaluate_completion(state)["status"], "COMPLETE")
        state["completion_state"]["scope_input_identities"]["module-a-check"]["release-config"] = "changed-contract-hash"
        self.assertIn("VERIFICATION_MISSING_OR_FAILING", [x["code"] for x in evaluate_completion(state)["reasons"]])
        state["verification_chronology"].append({**state["verification_chronology"][0], "chronology_index": 2,
            "evidence_ref": "new-pass", "input_identities": dict(state["completion_state"]["scope_input_identities"]["module-a-check"])})
        self.assertEqual(evaluate_completion(state)["status"], "COMPLETE")

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
        self.assertEqual(review_path(["code"], deterministic=True), "scoped_checks")
        self.assertEqual(review_path(["code", "documentation"], deterministic=True), "scoped_checks")
        self.assertEqual(review_path(["architecture"], deterministic=True), "semantic_review")
        self.assertEqual(review_path(["code"], semantic_risk=True), "semantic_review")

    def test_duplicate_running_and_parallel_work(self):
        passed = {"chronology_index": 1, "command_or_tool": "full release verification", "scope": "release", "target_identity": "tree-A", "execution_environment": "macos", "status": "PASS", "observable_result": "passed"}
        proposed = {**passed, "chronology_index": 2, "expensive": True}
        self.assertEqual(duplicate_expensive_action([passed], proposed), passed)
        selection_state = state_for()
        selection_state["verification_chronology"] = [passed | {"evidence_ref": "existing"}]
        self.assertEqual(select_next_actions(selection_state, proposed)["proposed_action"], {"decision": "reuse", "evidence_ref": "existing"})
        failed = {**passed, "chronology_index": 2, "status": "FAIL", "evidence_ref": "latest-fail"}
        self.assertIsNone(duplicate_expensive_action([passed, failed], proposed))
        selection_state["verification_chronology"].append(failed)
        self.assertEqual(select_next_actions(selection_state, proposed)["proposed_action"], {"decision": "run", "evidence_ref": None})
        self.assertIsNone(duplicate_expensive_action([passed], {**proposed, "target_identity": "tree-B"}))
        self.assertIsNone(duplicate_expensive_action([passed], {**proposed, "input_identities": {"shared-contract": "changed"}}))
        self.assertIsNone(duplicate_expensive_action([passed], {**proposed, "repeat_reason": "new_hypothesis"}))
        running = {"work_item_id": "build", "status": "ACTIVE", "verification_scope": "release", "target_identity": "tree-A", "cancelable": True}
        self.assertEqual(running_work_value(running, [passed]), "cancel_if_possible")
        selection_state["work_items"] = [running]
        self.assertEqual(select_next_actions(selection_state)["cancel_running_if_supported"], [])
        selection_state["verification_chronology"].pop()
        self.assertEqual(select_next_actions(selection_state)["cancel_running_if_supported"], ["build"])
        self.assertEqual(running_work_value({**running, "target_identity": "tree-B"}, [passed]), "continue")
        self.assertEqual(running_work_value({**running, "input_identities": {"shared-contract": "changed"}}, [passed]), "continue")
        left = {"work_item_id": "a", "dependencies": [], "write_targets": ["a.py"], "estimated_wall_time": 10, "integration_cost": 2}
        right = {"work_item_id": "b", "dependencies": [], "write_targets": ["b.py"], "estimated_wall_time": 10, "integration_cost": 2}
        self.assertTrue(parallelizable(left, right, priority="speed"))
        self.assertFalse(parallelizable(left, {**right, "dependencies": ["a"]}))
        self.assertFalse(parallelizable(left, {**right, "write_targets": ["a.py"]}))
        state = state_for()
        state["verification_chronology"].append({**state["verification_chronology"][0], "chronology_index": 2, "expensive": True, "evidence_ref": "second"})
        self.assertEqual(progress_snapshot(state)["duplicate_expensive_actions"], [[1, 2]])

    def test_native_duplicate_prevention_and_commit_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = Ledger(directory); ledger.create("parent", "task", "task")
            cwd = Path(directory)
            revision = always_on._candidate(cwd, ledger)[0]
            command = "corepack pnpm run test:unit"
            passed = {"chronology_index": 1, "action": "run", "command_or_tool": command, "scope": "test", "target_identity": revision, "input_identities": {"repository": revision}, "execution_environment": always_on.sys.platform, "status": "PASS", "observable_result": "passed", "evidence_ref": "p"}
            ledger.update("verification_chronology", passed)
            event = {"cwd": str(cwd), "tool_input": {"command": command}, "tool_use_id": "next"}
            self.assertEqual(always_on._pre_tool(event, ledger)["hookSpecificOutput"]["permissionDecision"], "deny")
            ledger.update("verification_chronology", dict(passed, chronology_index=2, status="FAIL", evidence_ref="f"))
            self.assertIsNone(always_on._pre_tool(event, ledger))
            commit = {"cwd": str(cwd), "tool_input": {"command": "git commit -m 'Separate build test release'"}}
            ledger.replace("commit_scope", {"candidate_revision": revision, "scope": "Build/test/release responsibility separation", "message": "Separate build test release", "remaining_required_work": ["transitive test duplication", "release still compiles"]})
            self.assertEqual(always_on._pre_tool(commit, ledger)["hookSpecificOutput"]["permissionDecision"], "deny")
            ledger.replace("commit_scope", {"candidate_revision": revision, "scope": "Build/test/release responsibility separation", "message": "Separate build test release", "remaining_required_work": []})
            self.assertIsNone(always_on._pre_tool(commit, ledger))
            broader = dict(commit, tool_input={"command": "git commit -m 'Complete the entire release'"})
            self.assertEqual(always_on._pre_tool(broader, ledger)["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertEqual(ledger.read()["completion_state"]["required_verification_scopes"], [])

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
            with patch.object(always_on, "STATE_HOME", root / "sessions"), patch.object(always_on, "RECOVERY_HOME", root / "archive"):
                state = ledger.read(); state["completion_state"]["candidate_revision"] = edited; ledger._write_state(state)
                assess(ledger, {"candidate_revision": edited, "change_types": ["documentation"], "semantic_risk": False, "reason": "Deterministic one-line edit"})
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
