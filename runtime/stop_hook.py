"""Optional Codex Stop hook for a task ledger selected by HARNESS_V0_LEDGER.

This script is inert when no ledger is selected. Trust this hook only after
reviewing its exact installed command and definition in Codex.
"""
import json
import os
import sys

from harness_v0.completion import evaluate_completion, progress_snapshot
from harness_v0.core import Ledger


def main():
    event = json.load(sys.stdin)
    directory = os.environ.get("HARNESS_V0_LEDGER")
    if not directory:
        return
    ledger = Ledger(directory)
    if not ledger.state_path.exists():
        return
    state = ledger.read()
    result = evaluate_completion(state)
    ledger.append_event("stop_hook_evaluated", {"turn_id": event.get("turn_id"), "status": result["status"], "reason_codes": [item["code"] for item in result.get("reasons", [])]})
    if result["status"] == "CONTINUE" and not event.get("stop_hook_active"):
        progress = progress_snapshot(state)
        if progress["available_next_actions"]:
            reason = "The parent task still has authorized work. Continue with the next work item: " + progress["available_next_actions"][0]
        else:
            reason_codes = [item["code"] for item in result.get("reasons", [])]
            reason = "The parent completion gate is CONTINUE. Resolve the next gate reason: " + (reason_codes[0] if reason_codes else "inspect task state")
        print(json.dumps({"decision": "block", "reason": reason}))


if __name__ == "__main__":
    main()
