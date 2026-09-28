"""Freeze a prior live-regression work artifact without exposing grader labels."""
from pathlib import Path
import json

from harness_v0.core import Ledger
from harness_v0.review import BuiltinSubagentAdapter, build_package, route_review

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "eval-results" / "prior-evidence" / "F063-LIVE"


def main():
    ledger = Ledger(ROOT / "eval-results" / "real-work" / "F063-live-derived")
    if not ledger.state_path.exists():
        ledger.create("F063-live-derived", "produce a closed-world Codex work prompt", (SOURCE / "prompt.txt").read_text())
    state = ledger.read()
    state["obligations"] = [{"id": "policy", "description": "Preserve the requested positive capability set and closed default", "status": "IN_PROGRESS", "evidence_refs": []}]
    state["authority"] = {"policy_model": "allowlist", "default_admissibility": "deny", "closure": "closed", "capabilities": ["read supplied packet", "collect native and selected candidate traces", "compare and report", "save two traces and report"], "constraints": ["repository only"], "exceptions": [], "scope": "top-level actions", "side_effect_scope": ["output/"], "delegation_scope": []}
    state["artifacts"] = [{"artifact_id": "final.txt", "semantic_role": "Codex work prompt", "semantic_owner": "user-facing result", "expected_lifetime": "current request", "current_state_role": "candidate"}]
    state["verification_chronology"] = [{"chronology_index": 1, "action": "candidate generation", "command_or_tool": "codex exec", "scope": "prompt", "observable_result": "turn completed; git_dirty false", "evidence_ref": "F063-metadata", "status": "PASS"}]
    ledger._write_state(state)
    final = (SOURCE / "final.txt").read_text()
    routing = route_review(["user_artifact", "architecture"], semantic_risk=True)
    ledger.append_event("review_routed", routing)
    package = build_package(state, routing, {"artifact_refs": ["final.txt"], "aggregate_diff": final, "resulting_state": final}, [str(SOURCE / "trace.jsonl"), str(SOURCE / "metadata.json"), str(SOURCE / "scenario" / "requested-work.md")])
    request = BuiltinSubagentAdapter(ledger).prepare(package)
    print(json.dumps(request, indent=2))


if __name__ == "__main__":
    main()
