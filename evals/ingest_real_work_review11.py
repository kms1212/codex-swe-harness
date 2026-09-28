"""Record the eleventh fresh native review of the current implementation."""
import json
from pathlib import Path

from harness_v0.core import Ledger, digest
from harness_v0.review import BuiltinSubagentAdapter

case = Path(__file__).resolve().parents[1] / "eval-results" / "real-work" / "current-v0-implementation"
package = json.loads((case / "current-v0-implementation-review-11.json").read_text())
result = json.loads((case / "review-result-11.json").read_text())
review = BuiltinSubagentAdapter(Ledger(case)).ingest(package, result, {
    "native_subagent_id": "/root/final_rc_review11", "package_received": True,
    "package_hash_verified": digest(package), "role_integrity": "read-only semantic evaluator",
})
print(json.dumps({"review_id": review["review_id"], "findings": len(review["findings"])}, indent=2))
