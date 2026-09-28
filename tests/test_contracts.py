import json
import copy
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from harness_v0.core import Ledger, digest, initial_state, review_context_hash, validate_authority
from harness_v0.review import BuiltinSubagentAdapter, build_package, record_disposition, route_review
from harness_v0.completion import evaluate_completion, progress_snapshot


def verification(index, scope, status, consumer=False):
    return {"chronology_index": index, "action": "run", "command_or_tool": "check", "scope": scope,
            "observable_result": status.lower(), "evidence_ref": f"e{index}", "status": status, "consumer_point": consumer, "artifact_revision": "rev1"}


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.ledger = Ledger(Path(self.temp.name) / "task")
        self.ledger.create("t1", "deliver artifact", "Deliver the artifact")

    def test_parent_is_not_worker(self):
        state = self.ledger.read()
        state["obligations"] = [{"id": "o1", "description": "deliver", "status": "SATISFIED", "evidence_refs": ["e1"]}]
        state["work_items"] = [{"work_item_id": "w1", "parent_id": "t1", "objective": "build", "owner": "worker", "status": "DONE", "dependencies": [], "produced_changes": ["a"], "verification_refs": ["e1"], "evidence_refs": ["e1"], "remaining_issues": [], "integration_notes": ""}]
        state["integration_state"]["candidate_changes"] = ["a"]
        state["completion_state"]["candidate_revision"] = "rev1"
        state["completion_state"]["required_verification_scopes"] = ["integration"]
        state["verification_chronology"] = [verification(1, "integration", "PASS")]
        self.assertIn("WORK_ITEM_NOT_INTEGRATED", {x["code"] for x in evaluate_completion(state)["reasons"]})
        state["work_items"][0]["status"] = "INTEGRATED"
        state["integration_state"]["integrated_changes"] = ["a"]
        self.assertEqual(evaluate_completion(state)["status"], "COMPLETE")

    def test_stale_failure_and_consumer(self):
        state = self.ledger.read()
        state["obligations"] = [{"id": "o1", "description": "deliver", "status": "SATISFIED", "evidence_refs": ["e3"]}]
        state["completion_state"]["candidate_revision"] = "rev1"
        state["completion_state"]["required_verification_scopes"] = ["tests"]
        state["completion_state"]["required_consumer_scopes"] = ["consumer"]
        state["verification_chronology"] = [verification(1, "tests", "FAIL"), verification(2, "tests", "PASS"), verification(3, "consumer", "PASS", True)]
        self.assertEqual(evaluate_completion(state)["status"], "COMPLETE")
        state["verification_chronology"].append(verification(4, "tests", "FAIL"))
        self.assertEqual(evaluate_completion(state)["status"], "CONTINUE")

    def test_policy_fidelity(self):
        state = self.ledger.read()
        validate_authority(state["authority"])
        self.assertEqual(state["authority"]["policy_model"], "unspecified")
        self.assertIsNone(state["authority"]["default_admissibility"])
        self.assertIsNone(state["authority"]["closure"])
        explicit = dict(state["authority"], policy_model="allowlist", default_admissibility="deny", closure="closed")
        validate_authority(explicit)
        changed = dict(explicit, default_admissibility="allow")
        with self.assertRaises(ValueError):
            validate_authority(changed)
        with self.assertRaises(ValueError):
            validate_authority(dict(explicit, closure="open"))
        with self.assertRaises(ValueError):
            validate_authority(dict(state["authority"], closure="closed"))
        validate_authority(dict(explicit, policy_model="denylist", default_admissibility="allow", closure="open"))

    def test_code_semantic_risk_requires_review(self):
        self.assertFalse(route_review(["code"])["required"])
        self.assertTrue(route_review(["code"], semantic_risk=True)["required"])

    def test_decision_supersession_and_work_transition(self):
        first = {"id": "d1", "decision": "use JSON", "status": "CONFIRMED", "scope": "integration", "evidence_refs": ["request"], "supersedes": [], "superseded_by": []}
        self.ledger.update("decisions", first)
        second = dict(first, id="d2", decision="use JSON with cents", supersedes=["d1"])
        self.ledger.update("decisions", second)
        decisions = self.ledger.read()["decisions"]
        self.assertEqual(decisions[0]["superseded_by"], ["d2"])
        self.assertEqual(decisions[0]["status"], "SUPERSEDED")
        item = {"work_item_id": "w1", "parent_id": "t1", "objective": "build", "owner": "worker", "status": "READY", "dependencies": [], "produced_changes": [], "verification_refs": [], "evidence_refs": [], "remaining_issues": [], "integration_notes": ""}
        self.ledger.update("work_items", item)
        self.ledger.transition("work_items", "w1", {"status": "INTEGRATED"}, ["integration-review"])
        self.assertEqual(self.ledger.read()["work_items"][0]["status"], "INTEGRATED")

    def test_frozen_package_and_native_receipt(self):
        self.ledger.update("verification_chronology", verification(1, "tests", "PASS"))
        before_review = self.ledger.read()
        before_review["obligations"] = [{"id": "o1", "description": "deliver", "status": "SATISFIED", "evidence_refs": ["e1"]}]
        before_review["completion_state"].update(candidate_revision="rev1", required_verification_scopes=["tests"], semantic_review_required=True)
        self.ledger._write_state(before_review)
        routing = route_review(["architecture"])
        package = build_package(self.ledger.read(), routing, {"artifact_refs": ["a"], "aggregate_diff": "+x", "resulting_state": "candidate"}, ["source"])
        adapter = BuiltinSubagentAdapter(self.ledger)
        request = adapter.prepare(package)
        self.assertEqual(request["package_hash"], digest(package))
        result = {"review_id": "r1", "package_hash": digest(package), "reviewer_adapter": "builtin_subagent", "findings": [{"criterion": 4, "severity": "major", "evidence_refs": ["a:1"], "violated_requirement": "durable data only", "blocking": True, "confidence": 0.9}], "overall_completion_risk": "high", "unresolved_unknowns": []}
        with self.assertRaises(ValueError):
            adapter.ingest(package, result, {"package_received": False})
        adapter.ingest(package, result, {"native_subagent_id": "child-1", "package_received": True, "package_hash_verified": digest(package), "role_integrity": "read-only semantic evaluator"})
        state = self.ledger.read()
        state["completion_state"]["semantic_review_required"] = True
        state["obligations"] = [{"id": "o1", "description": "deliver", "status": "SATISFIED", "evidence_refs": ["e1"]}]
        state["completion_state"]["candidate_revision"] = "rev1"
        state["completion_state"]["required_verification_scopes"] = ["tests"]
        self.assertEqual(evaluate_completion(state)["status"], "CONTINUE")
        self.ledger.update("evidence", {"evidence_id": "repair-evidence", "producer": "integrator", "operation": "repair", "observable_result": "fixed", "scope": "a", "chronology_index": 1, "artifact_refs": ["a"]})
        self.ledger.update("verification_chronology", verification(2, "repair", "PASS"))
        state = self.ledger.read()
        state["verification_chronology"][-1]["evidence_ref"] = "repair-evidence"
        state["verification_chronology"][-1]["resolves"] = ["r1:0"]
        self.ledger._write_state(state)
        record_disposition(self.ledger, "r1", 0, "accepted", ["repair-evidence"])
        state = self.ledger.read()
        state["completion_state"]["semantic_review_required"] = True
        state["obligations"] = [{"id": "o1", "description": "deliver", "status": "SATISFIED", "evidence_refs": ["e1"]}]
        state["completion_state"]["candidate_revision"] = "rev1"
        state["completion_state"]["required_verification_scopes"] = ["tests"]
        self.assertEqual(evaluate_completion(state)["status"], "COMPLETE")

    def test_requirement_change_invalidates_review_without_revision_change(self):
        state = self.ledger.read()
        state["obligations"] = [{"id": "o1", "description": "deliver A", "status": "SATISFIED", "evidence_refs": ["e1"]}]
        state["completion_state"].update(candidate_revision="rev1", required_verification_scopes=["tests"], semantic_review_required=True)
        state["verification_chronology"] = [verification(1, "tests", "PASS")]
        state["reviews"] = [{"review_id": "r1", "evidence_package_hash": "h", "reviewer_adapter": "builtin_subagent", "findings": [], "disposition": "RESOLVED", "resolution_evidence": [], "activation": {"native_subagent_id": "child"}, "candidate_revision": "rev1", "review_context_hash": review_context_hash(state)}]
        self.assertEqual(evaluate_completion(state)["status"], "COMPLETE")
        state["obligations"][0]["description"] = "deliver B"
        self.assertIn("CURRENT_REQUIREMENTS_NOT_REVIEWED", {reason["code"] for reason in evaluate_completion(state)["reasons"]})

    def test_relevant_work_and_epistemic_changes_invalidate_review(self):
        state = self.ledger.read()
        state["obligations"] = [{"id": "o", "description": "ship", "status": "SATISFIED", "evidence_refs": ["e1"]}]
        state["completion_state"].update(candidate_revision="rev1", required_verification_scopes=["tests"], semantic_review_required=True)
        state["verification_chronology"] = [verification(1, "tests", "PASS")]
        state["reviews"] = [{"review_id": "r", "evidence_package_hash": "h", "reviewer_adapter": "builtin_subagent", "findings": [], "disposition": "RESOLVED", "resolution_evidence": [], "activation": {"native_subagent_id": "child"}, "candidate_revision": "rev1", "review_context_hash": review_context_hash(state)}]
        self.assertEqual(evaluate_completion(state)["status"], "COMPLETE")
        changed_work = copy.deepcopy(state)
        changed_work["work_items"].append({"work_item_id": "w", "parent_id": "t1", "objective": "integrate", "owner": "worker", "status": "INTEGRATED", "dependencies": [], "produced_changes": [], "verification_refs": [], "evidence_refs": [], "remaining_issues": [], "integration_notes": ""})
        self.assertIn("CURRENT_REQUIREMENTS_NOT_REVIEWED", {reason["code"] for reason in evaluate_completion(changed_work)["reasons"]})
        changed_epistemic = copy.deepcopy(state)
        changed_epistemic["epistemic"].append({"id": "e", "proposition": "deployment available", "classification": "UNKNOWN", "evidence_refs": [], "scope": "deploy"})
        self.assertIn("CURRENT_REQUIREMENTS_NOT_REVIEWED", {reason["code"] for reason in evaluate_completion(changed_epistemic)["reasons"]})

    def test_external_block_and_repetition(self):
        state = self.ledger.read()
        state["blockers"] = [{"id": "b", "reason": "need credential", "external": True, "required_input": "credential"}]
        state["verification_chronology"] = [verification(1, "tests", "FAIL"), verification(2, "tests", "FAIL")]
        self.assertEqual(evaluate_completion(state)["status"], "CONTINUE")
        self.assertEqual(progress_snapshot(state)["repeated_actions"], [[1, 2]])

    def test_external_blocked_when_only_blocked_work_remains(self):
        state = self.ledger.read()
        state["obligations"] = [{"id": "o", "description": "ship", "status": "SATISFIED", "evidence_refs": ["e1"]}]
        state["completion_state"].update(candidate_revision="rev1", required_verification_scopes=["tests"])
        state["verification_chronology"] = [verification(1, "tests", "PASS")]
        state["work_items"] = [{"work_item_id": "w", "parent_id": "t1", "objective": "deploy", "owner": "worker", "status": "BLOCKED", "dependencies": [], "produced_changes": [], "verification_refs": [], "evidence_refs": [], "remaining_issues": ["credential"], "integration_notes": ""}]
        state["blockers"] = [{"id": "b", "reason": "need credential", "external": True, "required_input": "credential", "work_item_ids": ["w"]}]
        self.assertEqual(evaluate_completion(state)["status"], "BLOCKED")

    def test_external_blocker_can_link_unsatisfied_parent_obligation(self):
        state = self.ledger.read()
        state["obligations"] = [{"id": "deploy", "description": "deploy", "status": "OPEN", "evidence_refs": []}]
        state["completion_state"].update(candidate_revision="rev1", required_verification_scopes=["tests"])
        state["verification_chronology"] = [verification(1, "tests", "PASS")]
        state["work_items"] = [{"work_item_id": "w", "parent_id": "t1", "objective": "deploy", "owner": "worker", "status": "BLOCKED", "dependencies": [], "produced_changes": [], "verification_refs": [], "evidence_refs": [], "remaining_issues": ["credential"], "integration_notes": ""}]
        state["blockers"] = [{"id": "b", "reason": "credential required", "external": True, "required_input": "credential", "work_item_ids": ["w"], "obligation_ids": ["deploy"]}]
        result = evaluate_completion(state)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["external_blockers"][0]["required_input"], "credential")

    def test_unrelated_external_blocker_does_not_hide_local_verification_work(self):
        state = self.ledger.read()
        state["obligations"] = [{"id": "o", "description": "ship", "status": "SATISFIED", "evidence_refs": ["e1"]}]
        state["completion_state"].update(candidate_revision="rev1", required_verification_scopes=["tests"], required_consumer_scopes=["consumer"])
        state["verification_chronology"] = [verification(1, "tests", "FAIL")]
        state["blockers"] = [{"id": "b", "reason": "need deployment credential", "external": True, "required_input": "credential"}]
        result = evaluate_completion(state)
        self.assertEqual(result["status"], "CONTINUE")
        self.assertIn("VERIFICATION_MISSING_OR_FAILING", {reason["code"] for reason in result["reasons"]})
        self.assertIn("CONSUMER_EVIDENCE_MISSING", {reason["code"] for reason in result["reasons"]})

    def test_done_work_still_needs_integration_despite_external_blocker(self):
        state = self.ledger.read()
        state["obligations"] = [{"id": "o", "description": "ship", "status": "SATISFIED", "evidence_refs": ["e1"]}]
        state["completion_state"].update(candidate_revision="rev1", required_verification_scopes=["tests"])
        state["verification_chronology"] = [verification(1, "tests", "PASS")]
        state["work_items"] = [{"work_item_id": "w", "parent_id": "t1", "objective": "build", "owner": "worker", "status": "DONE", "dependencies": [], "produced_changes": ["x"], "verification_refs": ["e1"], "evidence_refs": ["e1"], "remaining_issues": [], "integration_notes": ""}]
        state["integration_state"]["candidate_changes"] = ["x"]
        state["blockers"] = [{"id": "b", "reason": "unrelated credential", "external": True, "required_input": "credential"}]
        self.assertEqual(evaluate_completion(state)["status"], "CONTINUE")

    def test_completion_replace_cannot_bypass_review_or_required_checks(self):
        value = self.ledger.read()["completion_state"]
        value.update(semantic_review_required=True, required_verification_scopes=["tests"], required_consumer_scopes=["consumer"])
        self.ledger.replace("completion_state", value)
        value["pending_review_hash"] = "hash"
        state = self.ledger.read()
        state["completion_state"] = value
        self.ledger._write_state(state)
        for changes in ({"semantic_review_required": False}, {"pending_review_hash": None}, {"required_verification_scopes": []}, {"required_consumer_scopes": []}, {"status": "COMPLETE"}):
            with self.assertRaises(ValueError):
                self.ledger.replace("completion_state", dict(value, **changes))

    def test_external_blocker_does_not_stop_independent_ready_work(self):
        state = self.ledger.read()
        state["blockers"] = [{"id": "b", "reason": "need credential for deployment", "external": True, "required_input": "credential"}]
        state["work_items"] = [{"work_item_id": "w", "parent_id": "t1", "objective": "write docs", "owner": "worker", "status": "READY", "dependencies": [], "produced_changes": [], "verification_refs": [], "evidence_refs": [], "remaining_issues": [], "integration_notes": ""}]
        result = evaluate_completion(state)
        self.assertEqual(result["status"], "CONTINUE")
        self.assertIn("w", progress_snapshot(state)["available_next_actions"])
        self.assertIn("EXTERNAL_BLOCKER", {reason["code"] for reason in result["reasons"]})

    def test_externally_blocked_dependency_is_not_available_work(self):
        state = self.ledger.read()
        state["blockers"] = [{"id": "b", "reason": "need credential", "external": True, "required_input": "credential"}]
        base = {"parent_id": "t1", "owner": "worker", "dependencies": [], "produced_changes": [], "verification_refs": [], "evidence_refs": [], "remaining_issues": [], "integration_notes": ""}
        state["work_items"] = [dict(base, work_item_id="blocked", objective="deploy", status="BLOCKED"),
                               dict(base, work_item_id="dependent", objective="verify deployment", status="READY", dependencies=["blocked"])]
        self.assertEqual(progress_snapshot(state)["available_next_actions"], [])
        self.assertEqual(evaluate_completion(state)["status"], "CONTINUE")
        state["work_items"][0]["status"] = "INTEGRATED"
        self.assertEqual(progress_snapshot(state)["available_next_actions"], ["dependent"])

    def test_stop_hook_continues_gate_without_ready_work_item(self):
        hook = Path(__file__).resolve().parents[1] / "runtime" / "stop_hook.py"
        env = dict(os.environ, HARNESS_V0_LEDGER=str(self.ledger.directory))
        first = subprocess.run([sys.executable, str(hook)], input=json.dumps({"turn_id": "t", "stop_hook_active": False}), text=True, capture_output=True, env=env, check=True)
        self.assertEqual(json.loads(first.stdout)["decision"], "block")
        self.assertIn("OBLIGATIONS_UNDECLARED", json.loads(first.stdout)["reason"])
        second = subprocess.run([sys.executable, str(hook)], input=json.dumps({"turn_id": "t", "stop_hook_active": True}), text=True, capture_output=True, env=env, check=True)
        self.assertEqual(second.stdout, "")

    def test_frozen_package_preserves_superseded_decisions(self):
        first = {"id": "old", "decision": "keep compatibility", "status": "CONFIRMED", "scope": "api", "evidence_refs": ["request"], "supersedes": [], "superseded_by": []}
        self.ledger.update("decisions", first)
        self.ledger.update("decisions", dict(first, id="new", decision="drop compatibility", supersedes=["old"], superseded_by=[]))
        package = build_package(self.ledger.read(), route_review(["architecture"]), {"artifact_refs": ["api"], "aggregate_diff": "+change", "resulting_state": "candidate"}, [])
        self.assertEqual([item["id"] for item in package["confirmed_decisions"]], ["new"])
        self.assertEqual([item["id"] for item in package["decision_history"]], ["old", "new"])
        self.assertEqual(package["decision_history"][0]["superseded_by"], ["new"])

    def test_unknown_evidence_and_stale_revision_do_not_complete(self):
        state = self.ledger.read()
        state["obligations"] = [{"id": "o1", "description": "deliver", "status": "SATISFIED", "evidence_refs": ["missing"]}]
        state["completion_state"]["candidate_revision"] = "rev2"
        state["completion_state"]["required_verification_scopes"] = ["tests"]
        state["verification_chronology"] = [verification(1, "tests", "PASS")]
        codes = {item["code"] for item in evaluate_completion(state)["reasons"]}
        self.assertIn("OBLIGATION_EVIDENCE_UNKNOWN", codes)
        self.assertIn("VERIFICATION_MISSING_OR_FAILING", codes)

    def test_pre_review_pass_does_not_verify_repair(self):
        state = self.ledger.read()
        state["obligations"] = [{"id": "o1", "description": "deliver", "status": "SATISFIED", "evidence_refs": ["e1"]}]
        state["completion_state"].update(candidate_revision="rev1", required_verification_scopes=["tests"], semantic_review_required=True)
        state["verification_chronology"] = [verification(1, "tests", "PASS")]
        state["reviews"] = [{"review_id": "r1", "evidence_package_hash": "h", "reviewer_adapter": "builtin_subagent", "findings": [{"criterion": 4, "severity": "major", "evidence_refs": ["a"], "violated_requirement": "lifetime", "blocking": True, "confidence": 0.9, "disposition": "accepted", "resolution_evidence": ["e1"]}], "disposition": "RESOLVED", "resolution_evidence": ["e1"], "activation": {"native_subagent_id": "child"}, "verification_cutoff_index": 1}]
        self.assertIn("REPAIR_VERIFICATION_MISSING", {item["code"] for item in evaluate_completion(state)["reasons"]})

    def test_review_must_cover_current_revision_and_target_finding(self):
        state = self.ledger.read()
        state["obligations"] = [{"id": "o1", "description": "deliver", "status": "SATISFIED", "evidence_refs": ["e1"]}]
        state["completion_state"].update(candidate_revision="rev1", required_verification_scopes=["tests"], semantic_review_required=True)
        state["verification_chronology"] = [verification(1, "tests", "PASS"), verification(2, "repair", "PASS")]
        state["reviews"] = [{"review_id": "r1", "evidence_package_hash": "h", "reviewer_adapter": "builtin_subagent", "findings": [{"criterion": 4, "severity": "major", "evidence_refs": ["a"], "violated_requirement": "lifetime", "blocking": True, "confidence": 0.9, "disposition": "accepted", "resolution_evidence": ["e2"]}], "disposition": "RESOLVED", "resolution_evidence": ["e2"], "activation": {"native_subagent_id": "child"}, "verification_cutoff_index": 1, "candidate_revision": "rev0"}]
        codes = {item["code"] for item in evaluate_completion(state)["reasons"]}
        self.assertIn("CURRENT_CANDIDATE_NOT_REVIEWED", codes)
        self.assertIn("REPAIR_VERIFICATION_MISSING", codes)

    def test_pending_review_prevents_parent_completion(self):
        state = self.ledger.read()
        state["obligations"] = [{"id": "o1", "description": "deliver", "status": "SATISFIED", "evidence_refs": ["e1"]}]
        state["completion_state"].update(candidate_revision="rev1", required_verification_scopes=["tests"], pending_review_hash="sha256:pending")
        state["verification_chronology"] = [verification(1, "tests", "PASS")]
        self.assertIn("REVIEW_RESULT_PENDING", {item["code"] for item in evaluate_completion(state)["reasons"]})


if __name__ == "__main__":
    unittest.main()
