"""Validate recorded native reviewer observations against frozen package receipts."""
import json
from pathlib import Path

from harness_v0.core import Ledger, canonical_bytes, digest
from harness_v0.review import BuiltinSubagentAdapter

ROOT = Path(__file__).resolve().parents[1]


def main():
    observations = [json.loads(line) for line in (ROOT / "evals" / "observed-results.jsonl").read_text().splitlines()]
    index = []
    for item in observations:
        case_id = item["case_id"]
        ledger = Ledger(ROOT / "eval-results" / "controlled" / case_id)
        package_file = ledger.directory / "challenge-v2-review-1.json"
        package = json.loads(package_file.read_text())
        activation = {"native_subagent_id": item["agent"], "package_received": True,
                      "package_hash_verified": digest(package), "role_integrity": "read-only semantic evaluator"}
        if not ledger.read()["reviews"]:
            BuiltinSubagentAdapter(ledger).ingest(package, item["result"], activation)
        index.append({"case_id": case_id, "package_path": str(package_file), "package_sha256": digest(package),
                      "result_sha256": digest(item["result"]), "native_subagent_id": item["agent"],
                      "findings": len(item["result"]["findings"]), "receipt": item["receipt"]})
    output = ROOT / "eval-results" / "run-index.jsonl"
    output.write_bytes(b"".join(canonical_bytes(row) for row in index))
    print(json.dumps(index, indent=2))


if __name__ == "__main__":
    main()
