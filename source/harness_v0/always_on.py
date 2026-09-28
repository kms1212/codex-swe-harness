"""Codex lifecycle hooks that bind native sessions to the v0 task ledger."""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from contextlib import contextmanager

from .completion import evaluate_and_record
from .core import Ledger, canonical_bytes, digest, review_context_hash
from .review import BuiltinSubagentAdapter, build_package, route_review

STATE_HOME = Path(os.environ.get("HARNESS_V0_STATE_HOME", str(Path.home() / ".codex/harness-v0/sessions")))
SESSION_ID = re.compile(r"[A-Za-z0-9_-]{8,128}\Z")
TEST_WORDS = re.compile(r"(^|\W)(pytest|unittest|jest|vitest|cargo test|go test|npm test|make test)(\W|$)", re.I)


def _session(event: dict) -> Ledger | None:
    session_id = event.get("session_id")
    if not isinstance(session_id, str) or not SESSION_ID.fullmatch(session_id):
        return None
    return Ledger(STATE_HOME / session_id)


@contextmanager
def _locked(ledger: Ledger):
    ledger.directory.mkdir(parents=True, exist_ok=True)
    with (ledger.directory / ".lock").open("a+b") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def _context(event_name: str, message: str) -> dict:
    return {"hookSpecificOutput": {"hookEventName": event_name, "additionalContext": message}}


def _run_git(cwd: Path, *args: str) -> bytes:
    try:
        return subprocess.check_output(["git", "-C", str(cwd), *args], stderr=subprocess.DEVNULL, timeout=10)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return b""


def _candidate(cwd: Path, ledger: Ledger) -> tuple[str, list[str], str]:
    """Fingerprint the working candidate, including untracked file bytes."""
    status = _run_git(cwd, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    diff = _run_git(cwd, "diff", "--binary", "HEAD")
    paths = []
    untracked = []
    for row in status.split(b"\0"):
        if not row or len(row) < 4:
            continue
        name = row[3:].decode("utf-8", "replace")
        paths.append(name)
        if row.startswith(b"?? "):
            file_path = cwd / name
            if file_path.is_file() and not file_path.is_symlink():
                untracked.append((name, hashlib.sha256(file_path.read_bytes()).hexdigest()))
    if not paths:
        writes = [event["data"] for event in ledger.events() if event["kind"] == "artifact_write_observed"]
        if writes:
            paths = [item["artifact_ref"] for item in writes]
            diff = canonical_bytes(writes)
    revision = digest({"status": status.decode("utf-8", "replace"), "diff_sha256": hashlib.sha256(diff).hexdigest(), "untracked": untracked})
    return revision, paths, diff.decode("utf-8", "replace")


def _tool_result(event: dict, ledger: Ledger) -> None:
    name = str(event.get("tool_name", "unknown"))
    token = str(event.get("tool_use_id") or digest(event)[:16])
    tool_input = event.get("tool_input")
    tool_response = event.get("tool_response")
    raw = {"tool_name": name, "tool_use_id": token, "turn_id": event.get("turn_id"), "input": tool_input, "response": tool_response}
    raw_dir = ledger.directory / "raw-tools"
    raw_dir.mkdir(exist_ok=True)
    (raw_dir / f"{re.sub('[^A-Za-z0-9_-]', '_', token)}.json").write_bytes(canonical_bytes(raw))
    summary = json.dumps(tool_response, ensure_ascii=False, default=str)[:800]
    status = "UNKNOWN"
    if isinstance(tool_response, dict):
        if tool_response.get("isError") is True or tool_response.get("exit_code") not in (None, 0):
            status = "FAIL"
        elif tool_response.get("exit_code") == 0 or tool_response.get("isError") is False:
            status = "PASS"
    command = str(tool_input.get("command", tool_input.get("cmd", ""))) if isinstance(tool_input, dict) else str(tool_input)[:300]
    if name in {"apply_patch", "Edit", "Write"} or re.search(r"(^|[;&| ])(touch|cp|mv|mkdir|sed -i|tee)\b|(^|[^<>])>(?!>)", command):
        ledger.append_event("artifact_write_observed", {"artifact_ref": str(raw_dir / f"{re.sub('[^A-Za-z0-9_-]', '_', token)}.json"), "tool_use_id": token})
    scope = "test" if TEST_WORDS.search(command) else f"tool:{name}"
    state = ledger.read()
    index = len(state["verification_chronology"]) + 1
    ref = f"tool:{token}"
    revision = state["completion_state"].get("candidate_revision")
    ledger.update("verification_chronology", {"chronology_index": index, "action": "native tool result", "command_or_tool": command[:500] or name,
        "scope": scope, "observable_result": summary, "evidence_ref": ref, "status": status, "artifact_revision": revision})
    ledger.update("evidence", {"evidence_id": ref, "producer": name, "operation": command[:500] or name,
        "observable_result": summary, "scope": scope, "chronology_index": index, "artifact_refs": [str(raw_dir / f"{re.sub('[^A-Za-z0-9_-]', '_', token)}.json")]})


def _parse_result(message: str) -> dict | None:
    text = message.strip()
    if text.startswith("```json") and text.endswith("```"):
        text = text[7:-3].strip()
    try:
        result = json.loads(text)
    except (TypeError, ValueError):
        return None
    return result if isinstance(result, dict) else None


def _route(paths: list[str]) -> list[str]:
    if not paths:
        return []
    types = set()
    for path in paths:
        lower = path.lower()
        if lower.endswith((".md", ".rst", ".txt")):
            types.add("documentation")
        elif lower.endswith((".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".swift")):
            types.add("code")
        else:
            types.add("user_artifact")
    return sorted(types)


def _stop(event: dict, ledger: Ledger) -> dict | None:
    state = ledger.read()
    cwd = Path(event.get("cwd") or os.getcwd())
    revision, paths, diff = _candidate(cwd, ledger)
    if not paths and not state["work_items"] and not state["artifacts"]:
        ledger.append_event("nonartifact_turn_observed", {"turn_id": event.get("turn_id")})
        return None
    completion = state["completion_state"]
    if paths and completion.get("candidate_revision") != revision:
        completion["candidate_revision"] = revision
        completion["status"] = "CONTINUE"
        ledger._write_state(state)
        ledger.append_event("candidate_revision_observed", {"revision": revision, "paths": paths})
        state = ledger.read()
    change_types = _route(paths)
    if change_types:
        routing = route_review(change_types, semantic_risk=True)
        if routing["required"] and not state["completion_state"]["semantic_review_required"]:
            state["completion_state"]["semantic_review_required"] = True
            ledger._write_state(state)
            ledger.append_event("review_routed", routing)
            state = ledger.read()
        latest = state["reviews"][-1] if state["reviews"] else None
        if not state["completion_state"]["pending_review_hash"] and (not latest or latest.get("candidate_revision") != revision or latest.get("review_context_hash") != review_context_hash(state)):
            package = build_package(state, routing, {"artifact_refs": paths, "aggregate_diff": diff[:200000], "resulting_state": paths}, paths)
            request = BuiltinSubagentAdapter(ledger).prepare(package)
            message = ("The SWE harness prepared a frozen semantic review package. Spawn one fresh built-in subagent now as a read-only semantic evaluator. "
                f"Give it only {request['package_path']} and ask it to read the file, independently SHA-256 hash its bytes, and return ONLY a JSON ReviewResult "
                f"with package_hash={request['package_hash']}, reviewer_adapter=builtin_subagent, review_id, findings, overall_completion_risk, and unresolved_unknowns. "
                "Wait for the result, consume its findings, repair if needed, and continue the parent task. Do not ask the user to run harness commands.")
            return {"decision": "block", "reason": message} if not event.get("stop_hook_active") else {"systemMessage": message}
    state = ledger.read()
    if state["completion_state"].get("pending_review_hash"):
        reason = "A native semantic review is pending. Spawn or wait for the fresh built-in reviewer using the frozen package in the ledger, then consume its structured result."
        return {"decision": "block", "reason": reason} if not event.get("stop_hook_active") else {"systemMessage": reason}
    result = evaluate_and_record(ledger)
    if result["status"] == "CONTINUE":
        codes = [item["code"] for item in result["reasons"]]
        reason = (f"The SWE parent completion gate is CONTINUE: {', '.join(codes)}. Update the session ledger from actual work and evidence; "
                  "resolve findings and required verification, then re-evaluate. Do not claim completion or ask the user for harness commands.")
        return {"decision": "block", "reason": reason} if not event.get("stop_hook_active") else {"systemMessage": reason}
    if result["status"] == "BLOCKED":
        return {"systemMessage": "SWE task is BLOCKED on external input: " + json.dumps(result["external_blockers"])}
    return None


def handle(event: dict) -> dict | None:
    ledger = _session(event)
    if ledger is None:
        return None
    kind = event.get("hook_event_name")
    with _locked(ledger):
        if kind == "SessionStart":
            return _context(kind, f"SWE harness v0 is active. Session ledger: {ledger.directory}. Natural-language work requests are recorded automatically.")
        if kind == "UserPromptSubmit":
            prompt = event.get("prompt", "")
            if not isinstance(prompt, str) or not prompt.strip():
                return None
            if not ledger.state_path.exists():
                ledger.create(str(event["session_id"]), prompt[:500], prompt)
                ledger.update("obligations", {"id": "user-request", "description": prompt[:1000], "status": "IN_PROGRESS", "evidence_refs": []})
                ledger.append_event("session_bound", {"session_id": event["session_id"], "cwd": event.get("cwd")})
            else:
                ledger.append_event("user_prompt_received", {"turn_id": event.get("turn_id"), "prompt_hash": digest(prompt)})
            return _context(kind, f"SWE task ledger is {ledger.directory}. The original request and parent obligation are recorded. Maintain task state and verification as you work; the lifecycle hooks capture native tool results and enforce review/completion. No user harness command is needed.")
        if not ledger.state_path.exists():
            return None
        if kind == "PostToolUse":
            _tool_result(event, ledger)
        elif kind == "SubagentStart":
            ledger.append_event("native_subagent_started", {"agent_id": event.get("agent_id"), "agent_type": event.get("agent_type"), "turn_id": event.get("turn_id")})
        elif kind == "SubagentStop":
            message = event.get("last_assistant_message") or ""
            result = _parse_result(message)
            pending = ledger.read()["completion_state"].get("pending_review_hash")
            if result and pending and result.get("package_hash") == pending:
                package_files = list(ledger.directory.glob("*-review-*.json"))
                package = next((json.loads(p.read_text()) for p in package_files if digest(json.loads(p.read_text())) == pending), None)
                if package is not None:
                    activation = {"native_subagent_id": event.get("agent_id"), "package_received": True,
                        "package_hash_verified": result["package_hash"], "role_integrity": "read-only semantic evaluator"}
                    review = BuiltinSubagentAdapter(ledger).ingest(package, result, activation)
                    return _context(kind, f"SWE review {review['review_id']} was ingested into the parent ledger. Consume and resolve every blocking finding before completion.")
            ledger.append_event("native_subagent_returned", {"agent_id": event.get("agent_id"), "turn_id": event.get("turn_id"), "result_hash": digest(message)})
        elif kind == "Stop":
            return _stop(event, ledger)
    return None


def main() -> None:
    event = json.load(sys.stdin)
    output = handle(event)
    if output is not None:
        print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
