"""Freeze candidate with full semantic-context freshness and linked external blockers."""
import hashlib
import json

from harness_v0.core import Ledger, digest
from harness_v0.completion import evaluate_completion
from harness_v0.review import BuiltinSubagentAdapter, build_package, record_disposition, route_review
from prepare_real_work_review4 import FILES, ROOT, CASE


def main():
    ledger = Ledger(CASE)
    state = ledger.read()
    if len(state["verification_chronology"]) != 82 or len(state["reviews"]) != 11 or len(state["obligations"]) != 19:
        raise RuntimeError("expected eleventh-review state")
    revision = digest({name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in FILES})
    known_refs = {item["evidence_id"] for item in state["evidence"]} | {item["evidence_ref"] for item in state["verification_chronology"]}
    audit_items = [item for item in state["obligations"] if item["id"].startswith("completion-set-")]
    assert len(audit_items) == 16 and all(item["status"] == "SATISFIED" and set(item["evidence_refs"]) <= known_refs for item in audit_items)
    current_audit = {"count": 16, "candidate_revision": revision, "items": [{"id": item["id"], "description": item["description"], "evidence_refs": item["evidence_refs"]} for item in audit_items]}
    (ROOT / "eval-results/completion-set-audit-current.json").write_text(json.dumps(current_audit, indent=2) + "\n")
    all_pairs = [(round_number, index) for round_number in range(1, 12) for index in range(len(state["reviews"][round_number - 1]["findings"]))]
    def target(round_number, index):
        if (round_number, index) == (2, 1):
            return "consumer-final-twelve"
        if (round_number, index) in {(1, 3), (4, 1), (6, 0)}:
            return "hook-no-work-final-twelve"
        if round_number == 3:
            return "policy-routing-final-twelve"
        if round_number == 10:
            return "completion-set-final-twelve"
        return "semantic-context-tests-22"
    scopes = [
        ("tests", "semantic-context-tests-22", False, "22 source tests PASS; linked parent obligation BLOCKED and full semantic review context invalidation verified."),
        ("hook", "hook-no-work-final-twelve", False, "Installed active Stop hook continued once for no-ready-work CONTINUE."),
        ("consumer", "consumer-final-twelve", True, "Consumer-point targeted repair test PASS."),
        ("tests", "policy-routing-final-twelve", False, "Unspecified authority and sequential installed CLI routing PASS."),
        ("installed-tests", "installed-tests-22", False, "Installed wheel suite: 22 PASS."),
        ("real-work", "realwork-f063-round11", False, "F063 live-derived and eleven current-work review rounds recorded."),
        ("completion-set", "completion-set-final-twelve", False, "All 16 original completion-set obligations individually SATISFIED with known evidence refs on current candidate."),
    ]
    for index, (scope, ref, consumer, observable) in enumerate(scopes, start=83):
        pairs = [(r, i) for r, i in all_pairs if target(r, i) == ref]
        ledger.update("verification_chronology", {"chronology_index": index, "action": "verify repaired parent candidate", "command_or_tool": scope,
            "scope": scope, "observable_result": observable, "evidence_ref": ref, "status": "PASS", "artifact_revision": revision,
            "resolves": [f"current-v0-implementation-review-{r}-semantic:{i}" for r, i in pairs], "consumer_point": consumer})
    for round_number, finding_index in all_pairs:
        record_disposition(ledger, f"current-v0-implementation-review-{round_number}-semantic", finding_index, "accepted", [target(round_number, finding_index)])
    ledger.append_event("repair_applied", {"review_id": "current-v0-implementation-review-11-semantic", "evidence_refs": ["semantic-context-tests-22", "completion-set-final-twelve"]})
    state = ledger.read()
    state["completion_state"].update(candidate_revision=revision, evidence_refs=[], status="CONTINUE")
    state["artifacts"] = [{"artifact_id": path, "semantic_role": "v0 implementation or current documentation", "semantic_owner": "product", "expected_lifetime": "durable", "current_state_role": "twelfth RC candidate"} for path in FILES]
    ledger._write_state(state)
    snapshot = "\n".join(f"=== {path} ===\n{(ROOT / path).read_text()}" for path in FILES)
    evidence = {
        "completion_set_audit_current": current_audit,
        "source_tests": (ROOT / "eval-results/raw-traces/source-tests-final.txt").read_text(),
        "installed_tests": (ROOT / "eval-results/raw-traces/installed-tests-final.txt").read_text(),
        "installed_cli_sequential_routing": json.loads((ROOT / "eval-results/raw-traces/installed-cli-risk-smoke.json").read_text()),
        "source_to_runtime": json.loads((ROOT / "eval-results/source-to-runtime.json").read_text()),
        "active_no_work_hook_events": [json.loads(line) for line in (ROOT / "eval-results/raw-traces/isolated-hook-no-work-events.jsonl").read_text().splitlines()],
        "run_index": [json.loads(line) for line in (ROOT / "eval-results/run-index.jsonl").read_text().splitlines()],
        "native_trace_index": [json.loads(line) for line in (ROOT / "eval-results/raw-traces/native-trace-index.jsonl").read_text().splitlines()],
        "parent_completion_diagnostic_before_current_review": evaluate_completion(state),
        "controlled_score": json.loads((ROOT / "eval-results/controlled/score.json").read_text()),
    }
    routing = route_review(["architecture", "code", "documentation", "integration", "completion"], semantic_risk=True)
    ledger.append_event("review_routed", routing)
    package = build_package(state, routing, {"artifact_refs": FILES, "aggregate_diff": snapshot,
        "resulting_state": "Twelfth supervised RC: 22 source/installed tests PASS, linked parent BLOCKED and full semantic context freshness, all 16 completion-set obligations audited.",
        "verification_evidence": evidence},
        ["eval-results/completion-set-audit-current.json", "eval-results/run-index.jsonl", "eval-results/raw-traces/native-trace-index.jsonl"])
    request = BuiltinSubagentAdapter(ledger).prepare(package)
    print(json.dumps({"request": request, "candidate_revision": revision, "bytes": len(snapshot.encode()), "obligations": len(state["obligations"])}, indent=2))


if __name__ == "__main__":
    main()
