"""Narrow approval for communication within a live, recorded delegation."""
from __future__ import annotations

from .core import Ledger, digest

COMMUNICATION_TOOLS = {
    "mcp__codex_app__send_message_to_thread": "message",
    "send_message_to_thread": "message",
    "collaboration.send_message": "message",
    "collaboration.followup_task": "followup",
}


def _identity(value: object) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def decide(event: dict, ledger: Ledger) -> dict | None:
    """Return an allow decision only when both endpoints match an active delegation."""
    tool = event.get("tool_name")
    kind = COMMUNICATION_TOOLS.get(tool)
    args = event.get("tool_input")
    if not kind or not isinstance(args, dict):
        return None
    sender = _identity(event.get("agent_id")) or _identity(event.get("thread_id")) or _identity(event.get("session_id"))
    recipient = _identity(args.get("threadId")) or _identity(args.get("target"))
    payload = _identity(args.get("prompt")) or _identity(args.get("message"))
    if not sender or not recipient or not payload:
        return None
    state = ledger.read()
    matched = None
    direction = None
    for work in state["delegated_work"]:
        if work["status"] != "DISPATCHED":
            continue
        if sender == state["task_id"] and recipient == work["owner"]:
            matched, direction = work, "to_worker"
            break
        if sender == work["owner"] and recipient == work["return_destination"]:
            matched, direction = work, "to_parent"
            break
    if matched is None:
        return None
    request_id = _identity(event.get("tool_use_id")) or _identity(event.get("request_id")) or digest({"turn_id": event.get("turn_id"), "tool": tool, "input": args})[:24]
    ledger.append_event("delegated_communication_approved", {
        "request_id": request_id, "communication_kind": kind, "direction": direction,
        "sender": sender, "recipient": recipient, "delegation_id": matched["id"],
        "decision": "allow", "payload_sha256": digest(payload),
    })
    return {"hookSpecificOutput": {"hookEventName": "PermissionRequest", "decision": {"behavior": "allow"}}}
