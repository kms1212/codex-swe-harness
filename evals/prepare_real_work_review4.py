"""Freeze the repaired current-work candidate for another fresh native review."""
import hashlib
import json
from pathlib import Path

from harness_v0.core import Ledger, digest, initial_state
from harness_v0.review import BuiltinSubagentAdapter, build_package, record_disposition, route_review

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "eval-results" / "real-work" / "current-v0-implementation"
FILES = [
    "source/harness_v0/core.py", "source/harness_v0/review.py", "source/harness_v0/completion.py",
    "source/harness_v0/cli.py", "runtime/stop_hook.py", "tests/test_contracts.py",
    "ARCHITECTURE.md", "STATE-SCHEMA.md", "REVIEW-PROTOCOL.md", "COMPLETION.md",
    "EVALUATION.md", "OPERATIONS.md", "V0-ACCEPTANCE.md",
]


def main():
    ledger = Ledger(CASE)
    state = ledger.read()
    if len(state["verification_chronology"]) != 18 or len(state["reviews"]) != 3:
        raise RuntimeError("expected third-review state")
    authority = initial_state("t", "o", "r")["authority"]
    ledger.replace("authority", authority)
    revision = digest({name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in FILES if name.startswith("source/")})
    events = [
        ("tests", "authority-default-fix", ["current-v0-implementation-review-1-semantic:0", "current-v0-implementation-review-1-semantic:1", "current-v0-implementation-review-1-semantic:2", "current-v0-implementation-review-2-semantic:0", "current-v0-implementation-review-3-semantic:0"], False, "Source unit suite: 11 passed; unspecified authority preserves unknown policy, explicit allowlist and denylist validated."),
        ("hook", "hook-activation-final", ["current-v0-implementation-review-1-semantic:3"], False, "Isolated Codex CLI with installed runtime: two agent messages, two Stop evaluations in latest turn."),
        ("consumer", "targeted-repair-final", ["current-v0-implementation-review-2-semantic:1"], True, "Consumer-point contract test passed with explicit finding resolution on current candidate."),
        ("tests", "semantic-risk-cli-fix", ["current-v0-implementation-review-3-semantic:1"], False, "Installed CLI code-only --semantic-risk smoke returned required=true and pending review hash."),
        ("installed-tests", "installed-tests-11", [], False, "Installed wheel test suite: 11 passed."),
        ("real-work", "realwork-f063-final", [], False, "F063 live-derived result and current-work rounds 1-3 indexed; source-to-install hashes matched."),
    ]
    for index, (scope, ref, resolves, consumer, observable) in enumerate(events, start=19):
        ledger.update("verification_chronology", {
            "chronology_index": index, "action": "verify reviewed repair", "command_or_tool": scope,
            "scope": scope, "observable_result": observable, "evidence_ref": ref,
            "status": "PASS", "artifact_revision": revision, "resolves": resolves,
            "consumer_point": consumer,
        })
    record_disposition(ledger, "current-v0-implementation-review-3-semantic", 0, "accepted", ["authority-default-fix"])
    record_disposition(ledger, "current-v0-implementation-review-3-semantic", 1, "accepted", ["semantic-risk-cli-fix"])
    ledger.append_event("repair_applied", {"review_id": "current-v0-implementation-review-3-semantic", "evidence_refs": ["authority-default-fix", "semantic-risk-cli-fix"]})
    state = ledger.read()
    state["completion_state"].update(candidate_revision=revision, evidence_refs=[], status="CONTINUE")
    state["artifacts"] = [{"artifact_id": path, "semantic_role": "v0 implementation or current documentation", "semantic_owner": "product", "expected_lifetime": "durable", "current_state_role": "fourth RC candidate"} for path in FILES]
    ledger._write_state(state)
    snapshot = "\n".join(f"=== {path} ===\n{(ROOT / path).read_text()}" for path in FILES)
    evidence = {
        "source_tests": (ROOT / "eval-results/raw-traces/source-tests-final.txt").read_text(),
        "installed_tests": (ROOT / "eval-results/raw-traces/installed-tests-final.txt").read_text(),
        "installed_cli_help": (ROOT / "eval-results/raw-traces/installed-cli-help.txt").read_text(),
        "installed_cli_semantic_risk_smoke": "required=true; pending hash matched frozen package",
        "source_to_runtime": json.loads((ROOT / "eval-results/source-to-runtime.json").read_text()),
        "hook_agent_messages": [json.loads(line)["item"]["text"] for line in (ROOT / "eval-results/raw-traces/isolated-hook-final.jsonl").read_text().splitlines() if json.loads(line).get("type") == "item.completed" and json.loads(line).get("item", {}).get("type") == "agent_message"],
        "controlled_score": json.loads((ROOT / "eval-results/controlled/score.json").read_text()),
    }
    routing = route_review(["architecture", "code", "documentation", "integration", "completion"], semantic_risk=True)
    ledger.append_event("review_routed", routing)
    package = build_package(state, routing, {"artifact_refs": FILES, "aggregate_diff": snapshot,
        "resulting_state": "Fourth supervised RC candidate: source and installed suite 11/11 pass; installed CLI semantic-risk path exercised; isolated active Stop hook continued once; source/install hashes match.",
        "verification_evidence": evidence},
        ["eval-results/source-to-runtime.json", "eval-results/controlled/score.json", "eval-results/raw-traces/native-trace-index.jsonl"])
    request = BuiltinSubagentAdapter(ledger).prepare(package)
    print(json.dumps({"request": request, "candidate_revision": revision, "bytes": len(snapshot.encode())}, indent=2))


if __name__ == "__main__":
    main()
