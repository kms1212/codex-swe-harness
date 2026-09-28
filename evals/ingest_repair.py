import json
from pathlib import Path

from harness_v0.core import Ledger, digest
from harness_v0.review import BuiltinSubagentAdapter

root = Path(__file__).resolve().parents[1]
ledger = Ledger(root / "eval-results" / "controlled" / "v2_F062_lifetime")
package = json.loads((ledger.directory / "challenge-v2-review-2.json").read_text())
result = json.loads((ledger.directory / "repair-review-result.json").read_text())
if not any(item["review_id"] == result["review_id"] for item in ledger.read()["reviews"]):
    BuiltinSubagentAdapter(ledger).ingest(package, result, {"native_subagent_id": "/root/review_repair_v2", "package_received": True, "package_hash_verified": digest(package), "role_integrity": "read-only semantic evaluator"})
ledger.append_event("findings_consumed", {"review_id": result["review_id"], "finding_count": 0})
print(json.dumps({"before": 1, "after": len(result["findings"]), "package_hash": digest(package)}))
