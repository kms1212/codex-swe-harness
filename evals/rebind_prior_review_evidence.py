"""Bind prior accepted findings to passing checks for the final candidate revision."""
from pathlib import Path

from harness_v0.core import Ledger
from harness_v0.review import record_disposition

case = Path(__file__).resolve().parents[1] / "eval-results" / "real-work" / "current-v0-implementation"
ledger = Ledger(case)
for review_id, index, ref in [
    ("current-v0-implementation-review-1-semantic", 0, "authority-default-fix"),
    ("current-v0-implementation-review-1-semantic", 1, "authority-default-fix"),
    ("current-v0-implementation-review-1-semantic", 2, "authority-default-fix"),
    ("current-v0-implementation-review-1-semantic", 3, "hook-activation-final"),
    ("current-v0-implementation-review-2-semantic", 0, "authority-default-fix"),
    ("current-v0-implementation-review-2-semantic", 1, "targeted-repair-final"),
]:
    record_disposition(ledger, review_id, index, "accepted", [ref])
print("rebound six prior findings to final-candidate checks")
