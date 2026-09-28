"""Freeze the fifth candidate after decision-history and liveness repairs."""
import hashlib
import json
from pathlib import Path

from harness_v0.core import Ledger, digest
from harness_v0.review import BuiltinSubagentAdapter, build_package, record_disposition, route_review
from prepare_real_work_review4 import FILES, ROOT, CASE


def main():
    ledger = Ledger(CASE)
    state = ledger.read()
    if len(state["verification_chronology"]) != 24 or len(state["reviews"]) != 4:
        raise RuntimeError("expected fourth-review state")
    revision = digest({name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in FILES if name.startswith("source/")})
    events = [
        ("tests", "decision-history-fix", ["current-v0-implementation-review-1-semantic:0", "current-v0-implementation-review-1-semantic:1", "current-v0-implementation-review-1-semantic:2", "current-v0-implementation-review-2-semantic:0", "current-v0-implementation-review-4-semantic:0"], False, "13 source tests PASS, including frozen superseded-decision history and gate repairs."),
        ("hook", "hook-liveness-final", ["current-v0-implementation-review-1-semantic:3", "current-v0-implementation-review-4-semantic:1"], False, "Installed completion gate and active isolated Codex Stop hook continued once; independent-ready-work test PASS."),
        ("consumer", "consumer-repair-final", ["current-v0-implementation-review-2-semantic:1"], True, "Consumer-point targeted resolution contract PASS on current candidate."),
        ("tests", "policy-routing-final", ["current-v0-implementation-review-3-semantic:0", "current-v0-implementation-review-3-semantic:1"], False, "Unspecified policy and installed CLI semantic-risk tests PASS."),
        ("installed-tests", "installed-tests-13", [], False, "Installed wheel test suite: 13 PASS."),
        ("real-work", "realwork-f063-round4", [], False, "F063 live-derived case and current-work review rounds 1-4 recorded."),
    ]
    for index, (scope, ref, resolves, consumer, observable) in enumerate(events, start=25):
        ledger.update("verification_chronology", {
            "chronology_index": index, "action": "verify final repaired source", "command_or_tool": scope,
            "scope": scope, "observable_result": observable, "evidence_ref": ref,
            "status": "PASS", "artifact_revision": revision, "resolves": resolves,
            "consumer_point": consumer,
        })
    dispositions = [
        (1, 0, "decision-history-fix"), (1, 1, "decision-history-fix"),
        (1, 2, "decision-history-fix"), (1, 3, "hook-liveness-final"),
        (2, 0, "decision-history-fix"), (2, 1, "consumer-repair-final"),
        (3, 0, "policy-routing-final"), (3, 1, "policy-routing-final"),
        (4, 0, "decision-history-fix"), (4, 1, "hook-liveness-final"),
    ]
    for round_number, index, ref in dispositions:
        record_disposition(ledger, f"current-v0-implementation-review-{round_number}-semantic", index, "accepted", [ref])
    ledger.append_event("repair_applied", {"review_id": "current-v0-implementation-review-4-semantic", "evidence_refs": ["decision-history-fix", "hook-liveness-final"]})
    state = ledger.read()
    state["completion_state"].update(candidate_revision=revision, evidence_refs=[], status="CONTINUE")
    state["artifacts"] = [{"artifact_id": path, "semantic_role": "v0 implementation or current documentation", "semantic_owner": "product", "expected_lifetime": "durable", "current_state_role": "fifth RC candidate"} for path in FILES]
    ledger._write_state(state)
    snapshot = "\n".join(f"=== {path} ===\n{(ROOT / path).read_text()}" for path in FILES)
    evidence = {
        "source_tests": (ROOT / "eval-results/raw-traces/source-tests-final.txt").read_text(),
        "installed_tests": (ROOT / "eval-results/raw-traces/installed-tests-final.txt").read_text(),
        "installed_cli_risk_smoke": json.loads((ROOT / "eval-results/raw-traces/installed-cli-risk-smoke.json").read_text()),
        "source_to_runtime": json.loads((ROOT / "eval-results/source-to-runtime.json").read_text()),
        "hook_agent_messages": [json.loads(line)["item"]["text"] for line in (ROOT / "eval-results/raw-traces/isolated-hook-final.jsonl").read_text().splitlines() if json.loads(line).get("type") == "item.completed" and json.loads(line).get("item", {}).get("type") == "agent_message"],
        "controlled_score": json.loads((ROOT / "eval-results/controlled/score.json").read_text()),
    }
    routing = route_review(["architecture", "code", "documentation", "integration", "completion"], semantic_risk=True)
    ledger.append_event("review_routed", routing)
    package = build_package(state, routing, {"artifact_refs": FILES, "aggregate_diff": snapshot,
        "resulting_state": "Fifth supervised RC: decision history in frozen package, external block with ready work stays CONTINUE, source/installed tests 13/13 PASS, installed CLI and active Stop hook verified.",
        "verification_evidence": evidence},
        ["eval-results/source-to-runtime.json", "eval-results/controlled/score.json", "eval-results/raw-traces/native-trace-index.jsonl"])
    request = BuiltinSubagentAdapter(ledger).prepare(package)
    print(json.dumps({"request": request, "candidate_revision": revision, "bytes": len(snapshot.encode())}, indent=2))


if __name__ == "__main__":
    main()
