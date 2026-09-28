import json
from pathlib import Path

from harness_v0.core import Ledger, digest
from harness_v0.review import BuiltinSubagentAdapter

root = Path(__file__).resolve().parents[1]
ledger = Ledger(root / "eval-results" / "real-work" / "F063-live-derived")
package = json.loads((ledger.directory / "F063-live-derived-review-1.json").read_text())
result = json.loads((ledger.directory / "review-result-1.json").read_text())
if not ledger.read()["reviews"]:
    BuiltinSubagentAdapter(ledger).ingest(package, result, {"native_subagent_id": "/root/f063_live_review", "package_received": True, "package_hash_verified": digest(package), "role_integrity": "read-only semantic evaluator"})
print(json.dumps({"review_id": result["review_id"], "findings": len(result["findings"]), "hash": digest(package)}))
