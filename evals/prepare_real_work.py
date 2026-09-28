"""Freeze this v0 implementation as an exact current-work reviewer episode."""
from pathlib import Path
import json

from harness_v0.core import Ledger, digest
from harness_v0.review import BuiltinSubagentAdapter, build_package, route_review

ROOT = Path(__file__).resolve().parents[1]
REQUEST = Path("/Users/kms1212/.codex/attachments/98542353-2f6e-4378-b1d8-41b0dc51acc2/Pasted text.txt")
FILES = [
    "source/harness_v0/core.py", "source/harness_v0/review.py", "source/harness_v0/completion.py",
    "source/harness_v0/cli.py", "tests/test_contracts.py", "ARCHITECTURE.md", "STATE-SCHEMA.md",
    "REVIEW-PROTOCOL.md", "COMPLETION.md", "EVALUATION.md", "OPERATIONS.md", "V0-ACCEPTANCE.md",
]


def main():
    directory = ROOT / "eval-results" / "real-work" / "current-v0-implementation"
    ledger = Ledger(directory)
    if not ledger.state_path.exists():
        ledger.create("current-v0-implementation", "implement and validate the requested Codex SWE harness v0", REQUEST.read_text())
    state = ledger.read()
    state["obligations"] = [
        {"id": "contracts", "description": "Executable canonical state, review and completion contracts", "status": "SATISFIED", "evidence_refs": ["tests-6-pass"]},
        {"id": "runtime", "description": "Active runtime and native review evidence", "status": "SATISFIED", "evidence_refs": ["native-review-7", "installed-cli"]},
        {"id": "fresh-work", "description": "Multiple fresh real-work outcomes and full activation chain", "status": "IN_PROGRESS", "evidence_refs": []},
    ]
    state["artifacts"] = [{"artifact_id": path, "semantic_role": "v0 implementation or current documentation", "semantic_owner": "product", "expected_lifetime": "durable", "current_state_role": "candidate"} for path in FILES]
    state["verification_chronology"] = [
        {"chronology_index": 1, "action": "compile", "command_or_tool": "python3 -m py_compile", "scope": "source", "observable_result": "failed because Python cache path was outside sandbox", "evidence_ref": "cache-permission", "status": "FAIL"},
        {"chronology_index": 2, "action": "test", "command_or_tool": "PYTHONDONTWRITEBYTECODE=1 python3 -m unittest", "scope": "source", "observable_result": "five tests passed", "evidence_ref": "tests-5-pass", "status": "PASS"},
        {"chronology_index": 3, "action": "install", "command_or_tool": "pip install --no-build-isolation", "scope": "package", "observable_result": "failed: isolated venv lacked bdist_wheel", "evidence_ref": "install-fail", "status": "FAIL"},
        {"chronology_index": 4, "action": "install", "command_or_tool": "pip install ./harness-v0", "scope": "package", "observable_result": "wheel built and installed", "evidence_ref": "installed-cli", "status": "PASS"},
        {"chronology_index": 5, "action": "smoke", "command_or_tool": "installed harness-v0 complete", "scope": "completion", "observable_result": "empty task incorrectly returned COMPLETE", "evidence_ref": "premature-completion", "status": "FAIL"},
        {"chronology_index": 6, "action": "test", "command_or_tool": "PYTHONDONTWRITEBYTECODE=1 python3 -m unittest", "scope": "source", "observable_result": "six tests passed after gate repair", "evidence_ref": "tests-6-pass", "status": "PASS"},
        {"chronology_index": 7, "action": "review", "command_or_tool": "native collaboration subagents", "scope": "semantic review", "observable_result": "seven fresh controlled packages received hash receipts", "evidence_ref": "native-review-7", "status": "PASS"},
    ]
    ledger._write_state(state)
    snapshot = "\n".join(f"=== {path} ===\n{(ROOT / path).read_text()}" for path in FILES)
    routing = route_review(["architecture", "code", "documentation", "integration", "completion"], semantic_risk=True)
    ledger.append_event("review_routed", routing)
    package = build_package(state, routing, {"artifact_refs": FILES, "aggregate_diff": snapshot, "resulting_state": "Current source and documents shown in aggregate_diff; controlled cases and isolated CLI install passed. Acceptance remains conditional."}, ["reviewer isolation FINAL-DECISION.md", "F062 source", "F063 corpus extension"])
    request = BuiltinSubagentAdapter(ledger).prepare(package)
    print(json.dumps({"request": request, "bytes": len(snapshot.encode())}, indent=2))


if __name__ == "__main__":
    main()
