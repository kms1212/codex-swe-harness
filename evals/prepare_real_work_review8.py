"""Freeze candidate with conservative BLOCKED and protected completion transitions."""
import hashlib
import json

from harness_v0.core import Ledger, digest
from harness_v0.completion import evaluate_completion
from harness_v0.review import BuiltinSubagentAdapter, build_package, record_disposition, route_review
from prepare_real_work_review4 import FILES, ROOT, CASE


def main():
    ledger = Ledger(CASE)
    state = ledger.read()
    if len(state["verification_chronology"]) != 42 or len(state["reviews"]) != 7:
        raise RuntimeError("expected seventh-review state")
    revision = digest({name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in FILES})
    refs = {
        1: ["protected-gate-tests-17"] * 3 + ["hook-no-work-final-eight"],
        2: ["protected-gate-tests-17", "consumer-final-eight"],
        3: ["policy-routing-final-eight"] * 2,
        4: ["protected-gate-tests-17", "hook-no-work-final-eight"],
        5: ["protected-gate-tests-17"] * 2,
        6: ["hook-no-work-final-eight"],
        7: ["protected-gate-tests-17"] * 2,
    }
    scopes = [
        ("tests", "protected-gate-tests-17", False, "17 source tests PASS, including independent gate work and protected completion replacement."),
        ("hook", "hook-no-work-final-eight", False, "Installed active Stop hook continued once with no ready work item on final completion code."),
        ("consumer", "consumer-final-eight", True, "Consumer-point targeted repair test PASS."),
        ("tests", "policy-routing-final-eight", False, "Unspecified authority and sequential installed CLI routing PASS."),
        ("installed-tests", "installed-tests-17", False, "Installed wheel suite: 17 PASS."),
        ("real-work", "realwork-f063-round7", False, "F063 live-derived and seven current-work review rounds recorded."),
    ]
    for index, (scope, ref, consumer, observable) in enumerate(scopes, start=43):
        pairs = [(round_number, finding_index) for round_number, values in refs.items() for finding_index, target_ref in enumerate(values) if target_ref == ref]
        ledger.update("verification_chronology", {"chronology_index": index, "action": "verify repaired candidate", "command_or_tool": scope,
            "scope": scope, "observable_result": observable, "evidence_ref": ref, "status": "PASS", "artifact_revision": revision,
            "resolves": [f"current-v0-implementation-review-{round_number}-semantic:{finding_index}" for round_number, finding_index in pairs],
            "consumer_point": consumer})
    for round_number, values in refs.items():
        for finding_index, ref in enumerate(values):
            record_disposition(ledger, f"current-v0-implementation-review-{round_number}-semantic", finding_index, "accepted", [ref])
    ledger.append_event("repair_applied", {"review_id": "current-v0-implementation-review-7-semantic", "evidence_refs": ["protected-gate-tests-17"]})
    state = ledger.read()
    state["completion_state"].update(candidate_revision=revision, evidence_refs=[], status="CONTINUE")
    state["artifacts"] = [{"artifact_id": path, "semantic_role": "v0 implementation or current documentation", "semantic_owner": "product", "expected_lifetime": "durable", "current_state_role": "eighth RC candidate"} for path in FILES]
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
        "resulting_state": "Eighth supervised RC: source/installed tests 17/17 PASS, completion replacement protected, external BLOCKED conservative, installed and active paths verified.",
        "verification_evidence": evidence},
        ["eval-results/source-to-runtime.json", "eval-results/controlled/score.json", "eval-results/raw-traces/native-trace-index.jsonl"])
    request = BuiltinSubagentAdapter(ledger).prepare(package)
    print(json.dumps({"request": request, "candidate_revision": revision, "bytes": len(snapshot.encode())}, indent=2))


if __name__ == "__main__":
    main()
