"""Materialize frozen controlled packages and grader-only labels."""
import json
from pathlib import Path

from challenges import cases
from harness_v0.core import Ledger, canonical_bytes, digest
from harness_v0.review import BuiltinSubagentAdapter

ROOT = Path(__file__).resolve().parents[1]


def main():
    labels = []
    for case in cases():
        case_id = case["case_id"]
        ledger = Ledger(ROOT / "eval-results" / "controlled" / case_id)
        if ledger.state_path.exists():
            continue
        ledger.create(case_id, "controlled semantic challenge", case["package"]["original_request"])
        ledger.append_event("challenge_prepared", {"case_id": case_id, "package_hash": digest(case["package"])})
        request = BuiltinSubagentAdapter(ledger).prepare(case["package"])
        labels.append({"case_id": case_id, "expected_criterion": case["expected_criterion"], "package_hash": request["package_hash"]})
    label_path = ROOT / "evals" / "grader-labels.json"
    label_path.write_bytes(canonical_bytes(labels))
    print(json.dumps(labels, indent=2))


if __name__ == "__main__":
    main()
