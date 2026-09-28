"""Consume the current-work review, record repairs, and freeze the revised candidate."""
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
    state = ledger.read()
    source_names = [name for name in FILES if name.startswith("source/")]
    revision = digest({name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in source_names})
    if len(state["verification_chronology"]) == 7:
        additions = [
            ("tests", "eight source tests passed after gate repair", "gate-fixes", False),
            ("installed-tests", "eight tests passed against isolated installed wheel", "installed-tests-8", False),
            ("hook", "final installed source loaded; Stop hook evaluated twice and continued once", "hook-activation", False),
            ("real-work", "F063 live-derived package reviewed; no findings", "realwork-f063", False),
            ("consumer", "installed CLI returned CONTINUE for task with undeclared obligations", "installed-consumer", True),
        ]
        for index, (scope, observation, ref, consumer) in enumerate(additions, start=8):
            ledger.update("verification_chronology", {"chronology_index": index, "action": "verify repaired candidate", "command_or_tool": scope, "scope": scope,
                                                      "observable_result": observation, "evidence_ref": ref, "status": "PASS", "artifact_revision": revision, "consumer_point": consumer})
        for index in range(4):
            ref = "gate-fixes" if index < 3 else "hook-activation"
            record_disposition(ledger, "current-v0-implementation-review-1-semantic", index, "accepted", [ref])
        ledger.append_event("repair_applied", {"review_id": "current-v0-implementation-review-1-semantic", "evidence_refs": ["gate-fixes", "hook-activation", "realwork-f063"]})
    state = ledger.read()
    state["obligations"] = [
        {"id": "contracts", "description": "Executable canonical state, review and completion contracts", "status": "SATISFIED", "evidence_refs": ["gate-fixes"]},
        {"id": "runtime", "description": "Installed CLI and active hook/reviewer behavior", "status": "SATISFIED", "evidence_refs": ["hook-activation", "installed-consumer"]},
        {"id": "fresh-work", "description": "Selected current/live-regression-derived episodes", "status": "SATISFIED", "evidence_refs": ["realwork-f063"]},
    ]
    state["completion_state"].update({"candidate_revision": revision, "required_verification_scopes": ["tests", "installed-tests", "hook", "real-work"],
                                      "required_consumer_scopes": ["consumer"], "semantic_review_required": True})
    state["artifacts"] = [{"artifact_id": path, "semantic_role": "v0 implementation or current documentation", "semantic_owner": "product", "expected_lifetime": "durable", "current_state_role": "repaired candidate"} for path in FILES]
    ledger._write_state(state)
    snapshot = "\n".join(f"=== {path} ===\n{(ROOT / path).read_text()}" for path in FILES)
    routing = route_review(["architecture", "code", "documentation", "integration", "completion"], semantic_risk=True)
    ledger.append_event("review_routed", routing)
    package = build_package(state, routing, {"artifact_refs": FILES, "aggregate_diff": snapshot,
                                                       "resulting_state": "Repaired source and docs are shown in aggregate_diff. Isolated installed tests and Stop-hook continuation passed. Release candidate is for supervised local use."},
                            ["source-to-runtime.json", "controlled/score.json", "F063-live-derived/review-result-1.json"])
    request = BuiltinSubagentAdapter(ledger).prepare(package)
    print(json.dumps({"request": request, "candidate_revision": revision, "bytes": len(snapshot.encode())}, indent=2))


if __name__ == "__main__":
    main()
