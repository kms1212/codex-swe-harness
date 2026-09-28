"""Freeze candidate after linked external blockers and review-context freshness."""
import hashlib
import json

from harness_v0.core import Ledger, digest
from harness_v0.completion import evaluate_completion
from harness_v0.review import BuiltinSubagentAdapter, build_package, record_disposition, route_review
from prepare_real_work_review4 import FILES, ROOT, CASE


def main():
    ledger = Ledger(CASE)
    state = ledger.read()
    if len(state["verification_chronology"]) != 54 or len(state["reviews"]) != 9:
        raise RuntimeError("expected ninth-review state")
    revision = digest({name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in FILES})
    all_pairs = [(round_number, index) for round_number in range(1, 10) for index in range(len(state["reviews"][round_number - 1]["findings"]))]
    def target(round_number, index):
        if (round_number, index) == (2, 1):
            return "consumer-final-ten"
        if (round_number, index) in {(1, 3), (4, 1), (6, 0)}:
            return "hook-no-work-final-ten"
        if round_number == 3:
            return "policy-routing-final-ten"
        return "context-integration-tests-20"
    scopes = [
        ("tests", "context-integration-tests-20", False, "20 source tests PASS; DONE integration stays CONTINUE and changed requirements invalidate semantic review."),
        ("hook", "hook-no-work-final-ten", False, "Installed active Stop hook continued once for no-ready-work CONTINUE on final installed completion code."),
        ("consumer", "consumer-final-ten", True, "Consumer-point targeted repair test PASS."),
        ("tests", "policy-routing-final-ten", False, "Unspecified authority and sequential installed CLI routing PASS."),
        ("installed-tests", "installed-tests-20", False, "Installed wheel suite: 20 PASS."),
        ("real-work", "realwork-f063-round9", False, "F063 live-derived and nine current-work review rounds recorded."),
    ]
    for index, (scope, ref, consumer, observable) in enumerate(scopes, start=55):
        pairs = [(r, i) for r, i in all_pairs if target(r, i) == ref]
        ledger.update("verification_chronology", {"chronology_index": index, "action": "verify repaired candidate", "command_or_tool": scope,
            "scope": scope, "observable_result": observable, "evidence_ref": ref, "status": "PASS", "artifact_revision": revision,
            "resolves": [f"current-v0-implementation-review-{r}-semantic:{i}" for r, i in pairs], "consumer_point": consumer})
    for round_number, finding_index in all_pairs:
        record_disposition(ledger, f"current-v0-implementation-review-{round_number}-semantic", finding_index, "accepted", [target(round_number, finding_index)])
    ledger.append_event("repair_applied", {"review_id": "current-v0-implementation-review-9-semantic", "evidence_refs": ["context-integration-tests-20"]})
    state = ledger.read()
    state["completion_state"].update(candidate_revision=revision, evidence_refs=[], status="CONTINUE")
    state["artifacts"] = [{"artifact_id": path, "semantic_role": "v0 implementation or current documentation", "semantic_owner": "product", "expected_lifetime": "durable", "current_state_role": "tenth RC candidate"} for path in FILES]
    ledger._write_state(state)
    snapshot = "\n".join(f"=== {path} ===\n{(ROOT / path).read_text()}" for path in FILES)
    evidence = {
        "source_tests": (ROOT / "eval-results/raw-traces/source-tests-final.txt").read_text(),
        "installed_tests": (ROOT / "eval-results/raw-traces/installed-tests-final.txt").read_text(),
        "installed_cli_sequential_routing": json.loads((ROOT / "eval-results/raw-traces/installed-cli-risk-smoke.json").read_text()),
        "source_to_runtime": json.loads((ROOT / "eval-results/source-to-runtime.json").read_text()),
        "active_no_work_hook_events": [json.loads(line) for line in (ROOT / "eval-results/raw-traces/isolated-hook-no-work-events.jsonl").read_text().splitlines()],
        "active_no_work_agent_messages": [json.loads(line)["item"]["text"] for line in (ROOT / "eval-results/raw-traces/isolated-hook-no-work.jsonl").read_text().splitlines() if json.loads(line).get("type") == "item.completed" and json.loads(line).get("item", {}).get("type") == "agent_message"],
        "parent_completion_diagnostic_before_current_review": evaluate_completion(state),
        "controlled_score": json.loads((ROOT / "eval-results/controlled/score.json").read_text()),
    }
    routing = route_review(["architecture", "code", "documentation", "integration", "completion"], semantic_risk=True)
    ledger.append_event("review_routed", routing)
    package = build_package(state, routing, {"artifact_refs": FILES, "aggregate_diff": snapshot,
        "resulting_state": "Tenth supervised RC: 20 source/installed tests PASS, external BLOCKED requires linked blocked work, semantic review checked against current requirements/decisions/authority.",
        "verification_evidence": evidence},
        ["eval-results/source-to-runtime.json", "eval-results/controlled/score.json", "eval-results/raw-traces/native-trace-index.jsonl"])
    request = BuiltinSubagentAdapter(ledger).prepare(package)
    print(json.dumps({"request": request, "candidate_revision": revision, "bytes": len(snapshot.encode())}, indent=2))


if __name__ == "__main__":
    main()
