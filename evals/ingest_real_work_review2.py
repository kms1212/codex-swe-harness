import json
from pathlib import Path

from harness_v0.core import Ledger, digest
from harness_v0.review import BuiltinSubagentAdapter

root = Path(__file__).resolve().parents[1]
ledger = Ledger(root / "eval-results" / "real-work" / "current-v0-implementation")
package = json.loads((ledger.directory / "current-v0-implementation-review-2.json").read_text())
result = json.loads((ledger.directory / "review-result-2.json").read_text())
if not any(item["review_id"] == result["review_id"] for item in ledger.read()["reviews"]):
    BuiltinSubagentAdapter(ledger).ingest(package, result, {"native_subagent_id": "/root/real_work_repaired_review", "package_received": True, "package_hash_verified": digest(package), "role_integrity": "read-only semantic evaluator"})
print(json.dumps({"review_id": result["review_id"], "findings": len(result["findings"]), "hash": digest(package)}))
