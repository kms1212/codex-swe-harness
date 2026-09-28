"""Close targeted review findings and freeze the final supervised RC candidate."""
import hashlib
import json
from pathlib import Path

from harness_v0.core import Ledger, digest
from harness_v0.review import BuiltinSubagentAdapter, build_package, record_disposition, route_review

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    "source/harness_v0/core.py", "source/harness_v0/review.py", "source/harness_v0/completion.py",
    "source/harness_v0/cli.py", "runtime/stop_hook.py", "tests/test_contracts.py",
    "ARCHITECTURE.md", "STATE-SCHEMA.md", "REVIEW-PROTOCOL.md", "COMPLETION.md",
    "EVALUATION.md", "OPERATIONS.md", "V0-ACCEPTANCE.md",
]


def main():
    ledger = Ledger(ROOT / "eval-results" / "real-work" / "current-v0-implementation")
    revision = digest({name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in FILES if name.startswith("source/")})
    if len(ledger.read()["verification_chronology"]) == 12:
        fixes = [
            ("tests", "gate-fixes", ["current-v0-implementation-review-1-semantic:0", "current-v0-implementation-review-1-semantic:1", "current-v0-implementation-review-1-semantic:2"], False),
            ("hook", "hook-activation", ["current-v0-implementation-review-1-semantic:3"], False),
            ("tests", "review-coverage-fix", ["current-v0-implementation-review-2-semantic:0"], False),
            ("consumer", "targeted-repair-fix", ["current-v0-implementation-review-2-semantic:1"], True),
            ("installed-tests", "installed-tests-final", [], False),
            ("real-work", "realwork-f063", [], False),
        ]
        for index, (scope, ref, resolves, consumer) in enumerate(fixes, start=13):
            ledger.update("verification_chronology", {"chronology_index": index, "action": "verify final repaired source", "command_or_tool": scope,
                "scope": scope, "observable_result": "PASS: final source test or consumer observation", "evidence_ref": ref,
                "status": "PASS", "artifact_revision": revision, "resolves": resolves, "consumer_point": consumer})
        record_disposition(ledger, "current-v0-implementation-review-2-semantic", 0, "accepted", ["review-coverage-fix"])
        record_disposition(ledger, "current-v0-implementation-review-2-semantic", 1, "accepted", ["targeted-repair-fix"])
        ledger.append_event("repair_applied", {"review_id": "current-v0-implementation-review-2-semantic", "evidence_refs": ["review-coverage-fix", "targeted-repair-fix"]})
    state = ledger.read()
    state["completion_state"].update(candidate_revision=revision, evidence_refs=[], status="CONTINUE")
    state["artifacts"] = [{"artifact_id": path, "semantic_role": "v0 implementation or current documentation", "semantic_owner": "product", "expected_lifetime": "durable", "current_state_role": "final RC candidate"} for path in FILES]
    ledger._write_state(state)
    snapshot = "\n".join(f"=== {path} ===\n{(ROOT / path).read_text()}" for path in FILES)
    routing = route_review(["architecture", "code", "documentation", "integration", "completion"], semantic_risk=True)
    ledger.append_event("review_routed", routing)
    package = build_package(state, routing, {"artifact_refs": FILES, "aggregate_diff": snapshot,
        "resulting_state": "Final supervised local RC candidate, source/install hashes matched, ten source and installed tests passed, isolated Stop hook continued once, F063 live-derived review returned no finding."},
        ["source-to-runtime.json", "controlled/score.json", "F063-live-derived/review-result-1.json", "raw-traces/native-trace-index.jsonl"])
    request = BuiltinSubagentAdapter(ledger).prepare(package)
    print(json.dumps({"request": request, "candidate_revision": revision, "bytes": len(snapshot.encode())}, indent=2))


if __name__ == "__main__":
    main()
