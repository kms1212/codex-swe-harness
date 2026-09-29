"""Codex lifecycle hooks that bind native sessions to the v0 task ledger."""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from contextlib import contextmanager

from .completion import evaluate_and_record
from .core import Ledger, canonical_bytes, digest, review_context_hash
from .review import BuiltinSubagentAdapter, build_package, route_review
from .permissions import decide as decide_permission
from .optimization import is_trivial_diff, review_path

STATE_HOME = Path(os.environ.get("HARNESS_V0_STATE_HOME", "/private/tmp/harness-v0-sessions"))
ARCHIVE_HOME = Path(os.environ.get("HARNESS_V0_ARCHIVE_HOME", str(Path.home() / ".codex/harness-v0/archive")))
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
            archived = ARCHIVE_HOME / ledger.directory.name
            if not ledger.state_path.exists() and (archived / "state.json").is_file():
                shutil.copytree(archived, ledger.directory, dirs_exist_ok=True)
            yield
        finally:
            if ledger.state_path.is_file():
                archived.mkdir(parents=True, exist_ok=True)
                shutil.copytree(ledger.directory, archived, dirs_exist_ok=True, ignore=shutil.ignore_patterns(".lock"))
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
    untracked_diff = []
    for row in status.split(b"\0"):
        if not row or len(row) < 4:
            continue
        name = row[3:].decode("utf-8", "replace")
        paths.append(name)
        if row.startswith(b"?? "):
            file_path = cwd / name
            if file_path.is_file() and not file_path.is_symlink():
                content = file_path.read_bytes()
                untracked.append((name, hashlib.sha256(content).hexdigest()))
                untracked_diff.append(b"\n--- /dev/null\n+++ b/" + name.encode("utf-8", "replace") + b"\n" + content + b"\n")
    diff += b"".join(untracked_diff)
    if not paths and _run_git(cwd, "rev-parse", "--is-inside-work-tree").strip() != b"true":
        writes = [event["data"] for event in ledger.events() if event["kind"] == "artifact_write_observed"]
        if writes:
            paths = [item["artifact_ref"] for item in writes]
            diff = canonical_bytes(writes)
    tracked = _run_git(cwd, "ls-files", "-co", "--exclude-standard", "-z")
    content = []
    for raw_name in tracked.split(b"\0"):
        if not raw_name:
            continue
        name = raw_name.decode("utf-8", "replace")
        file_path = cwd / name
        if file_path.is_file() and not file_path.is_symlink():
            content.append((name, hashlib.sha256(file_path.read_bytes()).hexdigest()))
        elif file_path.is_symlink():
            content.append((name, "symlink:" + os.readlink(file_path)))
    revision = digest(sorted(content)) if content else digest({"status": status.decode("utf-8", "replace"), "diff_sha256": hashlib.sha256(diff).hexdigest(), "untracked": untracked})
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
    if name == "collaborationspawn_agent" and isinstance(tool_input, dict) and isinstance(tool_response, dict):
        alias = tool_response.get("task_name")
        if isinstance(alias, str) and alias.startswith("/root/"):
            ledger.append_event("native_spawn_alias_available", {"alias": alias, "tool_use_id": token})
    summary = json.dumps(tool_response, ensure_ascii=False, default=str)[:800]
    status = "UNKNOWN"
    if isinstance(tool_response, dict):
        if tool_response.get("isError") is True or tool_response.get("exit_code") not in (None, 0):
            status = "FAIL"
        elif tool_response.get("exit_code") == 0 or tool_response.get("isError") is False:
            status = "PASS"
    command = str(tool_input.get("command", tool_input.get("cmd", ""))) if isinstance(tool_input, dict) else str(tool_input)[:300]
    if isinstance(tool_response, str) and TEST_WORDS.search(command):
        if re.search(r"\bFAILED\b|\b[1-9][0-9]* failed\b", tool_response):
            status = "FAIL"
        elif re.search(r"Ran \d+ tests? in [^\n]+\n\nOK\b|\b\d+ passed\b", tool_response):
            status = "PASS"
    if name in {"apply_patch", "Edit", "Write"} or re.search(r"(^|[;&| ])(touch|cp|mv|mkdir|sed -i|tee)\b|(^|[^<>])>(?!>)", command):
        ledger.append_event("artifact_write_observed", {"artifact_ref": str(raw_dir / f"{re.sub('[^A-Za-z0-9_-]', '_', token)}.json"), "tool_use_id": token})
    is_test = bool(TEST_WORDS.search(command))
    scope = "test" if is_test else f"tool:{name}"
    state = ledger.read()
    index = len(state["verification_chronology"]) + 1
    ref = f"tool:{token}"
    revision = state["completion_state"].get("candidate_revision") or _candidate(Path(event.get("cwd") or os.getcwd()), ledger)[0]
    verification = {"chronology_index": index, "action": "native tool result", "command_or_tool": command[:500] or name,
        "scope": scope, "observable_result": summary, "evidence_ref": ref, "status": status, "artifact_revision": revision}
    if is_test:
        verification.update(target_identity=_candidate(Path(event.get("cwd") or os.getcwd()), ledger)[0],
                            related_inputs=["repository"], execution_environment=sys.platform, expensive=True)
    ledger.update("verification_chronology", verification)
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
    fingerprint, paths, diff = _candidate(cwd, ledger)
    if not paths and not state["work_items"] and not state["artifacts"]:
        ledger.append_event("nonartifact_turn_observed", {"turn_id": event.get("turn_id")})
        return None
    completion = state["completion_state"]
    if paths and not completion.get("candidate_revision"):
        completion["candidate_revision"] = fingerprint
        completion["status"] = "CONTINUE"
        ledger._write_state(state)
        ledger.append_event("candidate_revision_observed", {"revision": fingerprint, "paths": paths})
        state = ledger.read()
    revision = state["completion_state"].get("candidate_revision")
    change_types = _route(paths)
    if change_types:
        risk = len(paths) > 3 or any(kind in {"architecture", "integration"} for kind in change_types)
        path = review_path(change_types, deterministic=is_trivial_diff(paths, diff), semantic_risk=risk)
        routing = route_review(change_types, semantic_risk=path == "semantic_review")
        if path != "semantic_review":
            routing["required"] = False
        if not any(e["kind"] == "optimization_choice" and e["data"].get("fingerprint") == fingerprint for e in ledger.events()):
            ledger.append_event("optimization_choice", {"action": path, "reason": "change scope and semantic risk", "fingerprint": fingerprint,
                "changed_paths": paths, "reusable_evidence": [], "new_evidence": state["completion_state"].get("required_verification_scopes", []), "parallel": False})
        if routing["required"] and not state["completion_state"]["semantic_review_required"]:
            state["completion_state"]["semantic_review_required"] = True
            ledger._write_state(state)
            ledger.append_event("review_routed", routing)
            state = ledger.read()
        latest = state["reviews"][-1] if state["reviews"] else None
        if (routing["required"] or state["completion_state"]["semantic_review_required"]) and not state["completion_state"]["pending_review_hash"] and (not latest or latest.get("candidate_revision") != revision or latest.get("artifact_fingerprint") != fingerprint or latest.get("review_context_hash") != review_context_hash(state)):
            package = build_package(state, routing, {"artifact_refs": paths, "aggregate_diff": diff, "resulting_state": paths}, paths)
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
        if kind == "PermissionRequest":
            if event.get("tool_name") in {"mcp__codex_app__send_message_to_thread", "send_message_to_thread", "collaboration.send_message", "collaboration.followup_task", "collaborationsend_message", "collaborationfollowup_task"}:
                request_id = str(event.get("tool_use_id") or event.get("request_id") or digest(event)[:24])
                raw_dir = ledger.directory / "raw-permissions"
                raw_dir.mkdir(exist_ok=True)
                (raw_dir / f"{re.sub('[^A-Za-z0-9_-]', '_', request_id)}.json").write_bytes(canonical_bytes(event))
                ledger.append_event("permission_request_observed", {"request_id": request_id, "tool_name": event.get("tool_name"), "raw_ref": str(raw_dir / f"{re.sub('[^A-Za-z0-9_-]', '_', request_id)}.json")})
            return decide_permission(event, ledger)
        if kind == "PostToolUse":
            _tool_result(event, ledger)
        elif kind == "SubagentStart":
            agent_id = str(event.get("agent_id") or "")
            ledger.append_event("native_subagent_started", {"agent_id": agent_id, "agent_type": event.get("agent_type"), "turn_id": event.get("turn_id")})
            if agent_id and not ledger.read()["completion_state"].get("pending_review_hash"):
                available = [item["data"]["alias"] for item in ledger.events() if item["kind"] == "native_spawn_alias_available"]
                assigned = {alias for work in ledger.read()["delegated_work"] for alias in work.get("aliases", []) if alias.startswith("/root/")}
                unassigned = [alias for alias in available if alias not in assigned]
                alias = unassigned[0] if len(unassigned) == 1 else None
                work_id = "native-" + re.sub(r"[^A-Za-z0-9_-]", "_", agent_id)
                if not any(item["work_item_id"] == work_id for item in ledger.read()["work_items"]):
                    ledger.update("work_items", {"work_item_id": work_id, "parent_id": ledger.read()["task_id"],
                        "objective": f"Native subagent {event.get('agent_type') or 'work'}", "owner": agent_id, "status": "ACTIVE",
                        "dependencies": [], "produced_changes": [], "verification_refs": [], "evidence_refs": [],
                        "remaining_issues": [], "integration_notes": "Await native result and parent integration"})
                    ledger.update("delegated_work", {"id": work_id, "work_item_id": work_id, "owner": agent_id,
                        "expected_result": "native subagent result", "return_destination": ledger.read()["task_id"],
                        "status": "DISPATCHED", "result_refs": [], "consumed_refs": [], "integration_refs": [],
                        "aliases": [alias, alias.rsplit("/", 1)[-1]] if alias else [],
                        "return_aliases": [alias.rsplit("/", 1)[0]] if alias else []})
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
                    fingerprint, _, _ = _candidate(Path(event.get("cwd") or os.getcwd()), ledger)
                    state = ledger.read()
                    state["reviews"][-1]["artifact_fingerprint"] = fingerprint
                    ledger._write_state(state)
                    ledger.append_event("review_artifact_fingerprint_recorded", {"review_id": review["review_id"], "fingerprint": fingerprint})
                    return _context(kind, f"SWE review {review['review_id']} was ingested into the parent ledger. Consume and resolve every blocking finding before completion.")
            agent_id = str(event.get("agent_id") or "")
            result_ref = "subagent:" + re.sub(r"[^A-Za-z0-9_-]", "_", agent_id)
            ledger.append_event("native_subagent_returned", {"agent_id": agent_id, "turn_id": event.get("turn_id"), "result_hash": digest(message)})
            state = ledger.read()
            work = next((item for item in state["work_items"] if item["work_item_id"] == "native-" + re.sub(r"[^A-Za-z0-9_-]", "_", agent_id)), None)
            if work:
                index = len(state["verification_chronology"]) + 1
                ledger.update("verification_chronology", {"chronology_index": index, "action": "native subagent returned",
                    "command_or_tool": agent_id, "scope": "delegation", "observable_result": message[:800],
                    "evidence_ref": result_ref, "status": "UNKNOWN"})
                ledger.update("evidence", {"evidence_id": result_ref, "producer": agent_id, "operation": "native subagent return",
                    "observable_result": message[:800], "scope": "delegation", "chronology_index": index,
                    "artifact_refs": [str(event.get("agent_transcript_path"))] if event.get("agent_transcript_path") else []})
                ledger.transition("work_items", work["work_item_id"], {"status": "DONE", "evidence_refs": [result_ref]}, [result_ref])
                ledger.transition("delegated_work", work["work_item_id"], {"status": "RETURNED", "result_refs": [result_ref]}, [result_ref])
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
