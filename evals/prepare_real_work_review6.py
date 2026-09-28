"""Freeze candidate after sticky routing and dependency-aware liveness repairs."""
import hashlib
import json

from harness_v0.core import Ledger, digest
from harness_v0.completion import evaluate_completion
from harness_v0.review import BuiltinSubagentAdapter, build_package, record_disposition, route_review
from prepare_real_work_review4 import FILES, ROOT, CASE


def main():
    ledger = Ledger(CASE)
    state = ledger.read()
    if len(state["verification_chronology"]) != 30 or len(state["reviews"]) != 5:
        raise RuntimeError("expected fifth-review state")
    revision = digest({name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in FILES if name.startswith("source/")})
    events = [
        ("tests", "sticky-routing-dependency-fix", [(1, 0), (1, 1), (1, 2), (2, 0), (4, 0), (5, 0), (5, 1)], False, "14 source tests PASS, including dependency-aware BLOCKED and sticky semantic review."),
        ("hook", "hook-final-six", [(1, 3), (4, 1)], False, "Active installed Codex Stop hook continued once after current source installation."),
        ("consumer", "consumer-final-six", [(2, 1)], True, "Current-candidate consumer-point contract PASS."),
        ("tests", "policy-routing-final-six", [(3, 0), (3, 1)], False, "Unspecified policy and sequential installed CLI semantic-risk routes PASS."),
        ("installed-tests", "installed-tests-14", [], False, "Installed wheel suite: 14 PASS."),
        ("real-work", "realwork-f063-round5", [], False, "F063 and current-work review rounds 1-5 recorded."),
    ]
    for index, (scope, ref, finding_pairs, consumer, observable) in enumerate(events, start=31):
        ledger.update("verification_chronology", {
            "chronology_index": index, "action": "verify final repaired source", "command_or_tool": scope,
            "scope": scope, "observable_result": observable, "evidence_ref": ref,
            "status": "PASS", "artifact_revision": revision,
            "resolves": [f"current-v0-implementation-review-{round_number}-semantic:{finding_index}" for round_number, finding_index in finding_pairs],
            "consumer_point": consumer,
        })
    dispositions = [
        (1, 0, "sticky-routing-dependency-fix"), (1, 1, "sticky-routing-dependency-fix"),
        (1, 2, "sticky-routing-dependency-fix"), (1, 3, "hook-final-six"),
        (2, 0, "sticky-routing-dependency-fix"), (2, 1, "consumer-final-six"),
        (3, 0, "policy-routing-final-six"), (3, 1, "policy-routing-final-six"),
        (4, 0, "sticky-routing-dependency-fix"), (4, 1, "hook-final-six"),
        (5, 0, "sticky-routing-dependency-fix"), (5, 1, "sticky-routing-dependency-fix"),
    ]
    for round_number, finding_index, ref in dispositions:
        record_disposition(ledger, f"current-v0-implementation-review-{round_number}-semantic", finding_index, "accepted", [ref])
    ledger.append_event("repair_applied", {"review_id": "current-v0-implementation-review-5-semantic", "evidence_refs": ["sticky-routing-dependency-fix", "policy-routing-final-six"]})
    state = ledger.read()
    state["completion_state"].update(candidate_revision=revision, evidence_refs=[], status="CONTINUE")
    state["artifacts"] = [{"artifact_id": path, "semantic_role": "v0 implementation or current documentation", "semantic_owner": "product", "expected_lifetime": "durable", "current_state_role": "sixth RC candidate"} for path in FILES]
    ledger._write_state(state)
    pre_review = evaluate_completion(state)
    snapshot = "\n".join(f"=== {path} ===\n{(ROOT / path).read_text()}" for path in FILES)
    evidence = {
        "source_tests": (ROOT / "eval-results/raw-traces/source-tests-final.txt").read_text(),
        "installed_tests": (ROOT / "eval-results/raw-traces/installed-tests-final.txt").read_text(),
        "installed_cli_sequential_routing": json.loads((ROOT / "eval-results/raw-traces/installed-cli-risk-smoke.json").read_text()),
        "source_to_runtime": json.loads((ROOT / "eval-results/source-to-runtime.json").read_text()),
        "hook_agent_messages": [json.loads(line)["item"]["text"] for line in (ROOT / "eval-results/raw-traces/isolated-hook-final.jsonl").read_text().splitlines() if json.loads(line).get("type") == "item.completed" and json.loads(line).get("item", {}).get("type") == "agent_message"],
        "parent_completion_diagnostic_before_current_review": pre_review,
        "controlled_score": json.loads((ROOT / "eval-results/controlled/score.json").read_text()),
    }
    routing = route_review(["architecture", "code", "documentation", "integration", "completion"], semantic_risk=True)
    ledger.append_event("review_routed", routing)
    package = build_package(state, routing, {"artifact_refs": FILES, "aggregate_diff": snapshot,
        "resulting_state": "Sixth supervised RC: sticky required semantic review, dependency-aware BLOCKED, source/installed tests 14/14 PASS, installed CLI sequential routing and active Stop hook verified.",
        "verification_evidence": evidence},
        ["eval-results/source-to-runtime.json", "eval-results/controlled/score.json", "eval-results/raw-traces/native-trace-index.jsonl"])
    request = BuiltinSubagentAdapter(ledger).prepare(package)
    print(json.dumps({"request": request, "candidate_revision": revision, "bytes": len(snapshot.encode())}, indent=2))


if __name__ == "__main__":
    main()
