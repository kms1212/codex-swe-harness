"""Consume F062 finding, repair the candidate, and freeze a second review package."""
import json
from pathlib import Path

from harness_v0.core import Ledger
from harness_v0.review import BuiltinSubagentAdapter, record_disposition

ROOT = Path(__file__).resolve().parents[1]


def main():
    ledger = Ledger(ROOT / "eval-results" / "controlled" / "v2_F062_lifetime")
    state = ledger.read()
    if not any(event["kind"] == "repair_applied" for event in ledger.events()):
        ledger.append_event("finding_consumed", {"review_id": "v2_F062_lifetime-review-1", "finding_index": 0})
        ledger.update("evidence", {"evidence_id": "repair-1", "producer": "integrator", "operation": "remove transient next-batch line", "observable_result": "durable design only", "scope": "design.md", "chronology_index": 1, "artifact_refs": ["design.md"]})
        ledger.append_event("repair_applied", {"review_id": "v2_F062_lifetime-review-1", "evidence_ref": "repair-1"})
        ledger.update("verification_chronology", {"chronology_index": 1, "action": "inspect repaired artifact", "command_or_tool": "diff", "scope": "design.md", "observable_result": "transient line absent", "evidence_ref": "repair-1", "status": "PASS"})
        record_disposition(ledger, "v2_F062_lifetime-review-1", 0, "accepted", ["repair-1"])
    first = json.loads((ledger.directory / "challenge-v2-review-1.json").read_text())
    repaired = dict(first)
    repaired["package_id"] = "challenge-v2-review-2"
    old = "\nCurrent next batch: ask reviewer to inspect this file tomorrow.\n"
    for key in ("aggregate_diff", "resulting_state"):
        original = repaired["candidate_result"][key]
        if old not in original:
            raise ValueError("expected defect not present")
        repaired["candidate_result"][key] = original.replace(old, "\n")
    repaired["verification_chronology"].append({"chronology_index": 3, "action": "repair inspection", "command_or_tool": "diff", "scope": "design.md", "observable_result": "transient line absent", "evidence_ref": "repair-1", "status": "PASS"})
    repaired_path = ledger.directory / "challenge-v2-review-2.json"
    request = {"package_path": str(repaired_path), "package_hash": None}
    if not repaired_path.exists():
        request = BuiltinSubagentAdapter(ledger).prepare(repaired)
    print(json.dumps(request, indent=2))


if __name__ == "__main__":
    main()
