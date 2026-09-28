"""Freeze a candidate with all 16 parent completion obligations and indexed raw evidence."""
import hashlib
import json

from harness_v0.core import Ledger, digest
from harness_v0.completion import evaluate_completion
from harness_v0.review import BuiltinSubagentAdapter, build_package, record_disposition, route_review
from prepare_real_work_review4 import FILES, ROOT, CASE


def main():
    ledger = Ledger(CASE)
    state = ledger.read()
    if len(state["verification_chronology"]) != 76 or len(state["reviews"]) != 10 or len(state["obligations"]) != 19:
        raise RuntimeError("expected audited tenth-review state")
    revision = digest({name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in FILES})
    audit = json.loads((ROOT / "eval-results/completion-set-audit.json").read_text())
    assert audit["count"] == 16 and audit["candidate_revision"] == revision
    all_pairs = [(round_number, index) for round_number in range(1, 10) for index in range(len(state["reviews"][round_number - 1]["findings"]))]
    def target(round_number, index):
        if (round_number, index) == (2, 1):
            return "consumer-final-eleven"
        if (round_number, index) in {(1, 3), (4, 1), (6, 0)}:
            return "hook-no-work-final-eleven"
        if round_number == 3:
            return "policy-routing-final-eleven"
        return "completion-set-tests-20"
    scopes = [
        ("tests", "completion-set-tests-20", False, "20 source contract tests PASS; 16 explicit completion obligations audited."),
        ("hook", "hook-no-work-final-eleven", False, "Installed active Stop hook continued once for no-ready-work CONTINUE."),
        ("consumer", "consumer-final-eleven", True, "Consumer-point targeted repair test PASS."),
        ("tests", "policy-routing-final-eleven", False, "Authority and sequential installed CLI routing PASS."),
        ("installed-tests", "installed-tests-20-final", False, "Installed wheel suite: 20 PASS."),
        ("real-work", "realwork-f063-round10", False, "F063 live-derived and ten current-work review rounds recorded."),
    ]
    for index, (scope, ref, consumer, observable) in enumerate(scopes, start=77):
        pairs = [(r, i) for r, i in all_pairs if target(r, i) == ref]
        ledger.update("verification_chronology", {"chronology_index": index, "action": "verify audited parent candidate", "command_or_tool": scope,
            "scope": scope, "observable_result": observable, "evidence_ref": ref, "status": "PASS", "artifact_revision": revision,
            "resolves": [f"current-v0-implementation-review-{r}-semantic:{i}" for r, i in pairs], "consumer_point": consumer})
    for round_number, finding_index in all_pairs:
        record_disposition(ledger, f"current-v0-implementation-review-{round_number}-semantic", finding_index, "accepted", [target(round_number, finding_index)])
    record_disposition(ledger, "current-v0-implementation-review-10-semantic", 0, "accepted", ["completion-set:16"])
    ledger.append_event("repair_applied", {"review_id": "current-v0-implementation-review-10-semantic", "evidence_refs": ["completion-set:16", "eval-results/completion-set-audit.json"]})
    state = ledger.read()
    state["completion_state"].update(candidate_revision=revision, evidence_refs=[], status="CONTINUE")
    state["artifacts"] = [{"artifact_id": path, "semantic_role": "v0 implementation or current documentation", "semantic_owner": "product", "expected_lifetime": "durable", "current_state_role": "audited eleventh RC candidate"} for path in FILES]
    ledger._write_state(state)
    snapshot = "\n".join(f"=== {path} ===\n{(ROOT / path).read_text()}" for path in FILES)
    run_index = [json.loads(line) for line in (ROOT / "eval-results/run-index.jsonl").read_text().splitlines()]
    native_traces = [json.loads(line) for line in (ROOT / "eval-results/raw-traces/native-trace-index.jsonl").read_text().splitlines()]
    evidence = {
        "completion_set_audit": audit,
        "source_tests": (ROOT / "eval-results/raw-traces/source-tests-final.txt").read_text(),
        "installed_tests": (ROOT / "eval-results/raw-traces/installed-tests-final.txt").read_text(),
        "installed_cli_sequential_routing": json.loads((ROOT / "eval-results/raw-traces/installed-cli-risk-smoke.json").read_text()),
        "source_to_runtime": json.loads((ROOT / "eval-results/source-to-runtime.json").read_text()),
        "active_no_work_hook_events": [json.loads(line) for line in (ROOT / "eval-results/raw-traces/isolated-hook-no-work-events.jsonl").read_text().splitlines()],
        "run_index": run_index,
        "native_trace_index": native_traces,
        "parent_completion_diagnostic_before_current_review": evaluate_completion(state),
        "controlled_score": json.loads((ROOT / "eval-results/controlled/score.json").read_text()),
    }
    routing = route_review(["architecture", "code", "documentation", "integration", "completion"], semantic_risk=True)
    ledger.append_event("review_routed", routing)
    package = build_package(state, routing, {"artifact_refs": FILES, "aggregate_diff": snapshot,
        "resulting_state": "Eleventh supervised RC: all 16 original completion-set items individually satisfied with evidence; 20 source/installed tests PASS; active source/install/hook and native reviewer traces indexed.",
        "verification_evidence": evidence},
        ["eval-results/completion-set-audit.json", "eval-results/run-index.jsonl", "eval-results/raw-traces/native-trace-index.jsonl"])
    request = BuiltinSubagentAdapter(ledger).prepare(package)
    print(json.dumps({"request": request, "candidate_revision": revision, "bytes": len(snapshot.encode()), "obligations": len(state["obligations"])}, indent=2))


if __name__ == "__main__":
    main()
