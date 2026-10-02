"""Check the installed CLI's code-only semantic-risk path."""
import json
import subprocess
import tempfile
from pathlib import Path

ENTRY = Path("/tmp/codex-swe-harness-rc/bin/harness")
with tempfile.TemporaryDirectory(prefix="harness-cli-") as directory:
    root = Path(directory)
    ledger = root / "ledger"
    candidate = root / "candidate.json"
    candidate.write_text(json.dumps({"artifact_refs": ["code.py"], "aggregate_diff": "+contract change", "resulting_state": "candidate"}))
    subprocess.run([str(ENTRY), str(ledger), "create", "cli-risk", "review code semantics", "Preserve compatibility"], check=True, capture_output=True, text=True)
    request = json.loads(subprocess.check_output([str(ENTRY), str(ledger), "prepare-review", str(candidate), "--type", "code", "--semantic-risk"], text=True))
    state = json.loads((ledger / "state.json").read_text())
    events = [json.loads(line) for line in (ledger / "events.jsonl").read_text().splitlines()]
    assert state["completion_state"]["semantic_review_required"] is True
    assert state["completion_state"]["pending_review_hash"] == request["package_hash"]
    assert next(event for event in events if event["kind"] == "review_routed")["data"]["required"] is True
    result_file = root / "result.json"
    result_file.write_text(json.dumps({"review_id": "cli-risk-review-1", "package_hash": request["package_hash"], "reviewer_adapter": "builtin_subagent", "findings": [], "overall_completion_risk": "low", "unresolved_unknowns": []}))
    activation_file = root / "activation.json"
    activation_file.write_text(json.dumps({"native_subagent_id": "smoke-child", "package_received": True, "package_hash_verified": request["package_hash"], "role_integrity": "read-only semantic evaluator"}))
    subprocess.run([str(ENTRY), str(ledger), "ingest-review", request["package_path"], str(result_file), str(activation_file)], check=True, capture_output=True, text=True)
    second = json.loads(subprocess.check_output([str(ENTRY), str(ledger), "prepare-review", str(candidate), "--type", "code"], text=True))
    later = json.loads((ledger / "state.json").read_text())
    routed = [json.loads(line)["data"] for line in (ledger / "events.jsonl").read_text().splitlines() if json.loads(line)["kind"] == "review_routed"]
    assert later["completion_state"]["semantic_review_required"] is True
    assert later["completion_state"]["pending_review_hash"] == second["package_hash"]
    assert routed[-1]["required"] is True
    print(json.dumps({"installed_cli_semantic_risk_required": True, "requirement_persists_after_later_code_route": True, "first_package_hash": request["package_hash"], "second_package_hash": second["package_hash"]}))
