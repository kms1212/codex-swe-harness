"""Codex lifecycle hooks that bind native sessions to the task ledger."""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import shlex
import subprocess
import sys
import time
from contextlib import contextmanager

from .completion import evaluate_and_record
from .core import Ledger, canonical_bytes, digest, review_context_hash
from .review import BuiltinSubagentAdapter, build_package, route_review
from .instructions import instruction_paths, recomposition_reasons
from .permissions import decide as decide_permission
from .optimization import select_next_actions, duplicate_expensive_action
from .commands import verification_command, result_status, words
from .scheduling import schedule, coverage
from .lifecycle import cleanup, tracking_reasons

STATE_HOME = Path(os.environ.get("HARNESS_STATE_HOME", "/tmp/harness-sessions"))
RECOVERY_HOME = Path(os.environ.get("HARNESS_RECOVERY_HOME", str(Path.home() / ".codex/harness/recovery")))
SESSION_ID = re.compile(r"[A-Za-z0-9_-]{8,128}\Z")
RECOVERY_DAYS = 7


def _is_test_command(command: str) -> bool:
    return verification_command(command) is not None


def _session(event: dict) -> Ledger | None:
    session_id = event.get("session_id")
    if not isinstance(session_id, str) or not SESSION_ID.fullmatch(session_id):
        return None
    return Ledger(STATE_HOME / session_id)


def _recovery_meta(directory: Path) -> dict | None:
    marker = directory / ".recovery.json"
    if directory.is_symlink() or marker.is_symlink() or not marker.is_file():
        return None
    try:
        meta = json.loads(marker.read_text())
        if meta.get("owner") == "harness" and meta.get("session_id") == directory.name and isinstance(meta.get("updated_at"), (int, float)):
            return meta
    except (ValueError, OSError):
        pass
    return None


@contextmanager
def _locked(ledger: Ledger):
    ledger.directory.mkdir(parents=True, exist_ok=True)
    with (ledger.directory / ".lock").open("a+b") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        try:
            archived = RECOVERY_HOME / ledger.directory.name
            meta = _recovery_meta(archived)
            if not ledger.state_path.exists() and meta and time.time() - meta["updated_at"] < RECOVERY_DAYS * 86400:
                shutil.copytree(archived, ledger.directory, dirs_exist_ok=True, symlinks=True)
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def _checkpoint(ledger: Ledger) -> None:
    """Recovery has a bounded inactivity lifetime; no per-tool archive mirror."""
    RECOVERY_HOME.mkdir(parents=True, exist_ok=True)
    now = time.time()
    for directory in RECOVERY_HOME.iterdir():
        meta = _recovery_meta(directory)
        if meta and now - meta["updated_at"] > RECOVERY_DAYS * 86400:
            shutil.rmtree(directory)
    target = RECOVERY_HOME / ledger.directory.name
    if target.exists() and not _recovery_meta(target) or target.is_symlink():
        ledger.append_event("recovery_unknown_destination_preserved", {"path": str(target)})
        return
    shutil.copytree(ledger.directory, target, dirs_exist_ok=True, symlinks=True, ignore=shutil.ignore_patterns(".lock", "scratch"))
    (target / ".recovery.json").write_bytes(canonical_bytes({"owner": "harness", "session_id": ledger.directory.name, "updated_at": now}))
    ledger.append_event("recovery_checkpoint", {"path": str(target), "inactivity_days": RECOVERY_DAYS})


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
    baseline_file = ledger.directory / "candidate-baseline.json"
    if baseline_file.is_file():
        import difflib
        baseline = json.loads(baseline_file.read_text())
        current = _snapshot(cwd, [name for name, identity in content], "")["resulting_state"]
        paths = [name for name in sorted(baseline.keys() | current.keys()) if baseline.get(name) != current.get(name)]
        diff = "".join("".join(difflib.unified_diff(baseline.get(name, {}).get("content", "").splitlines(keepends=True), current.get(name, {}).get("content", "").splitlines(keepends=True), fromfile="a/" + name, tofile="b/" + name)) for name in paths).encode()
    revision = digest(sorted(content)) if content else digest({"status": status.decode("utf-8", "replace"), "diff_sha256": hashlib.sha256(diff).hexdigest(), "untracked": untracked})
    return revision, paths, diff.decode("utf-8", "replace")


def _session_baseline(ledger: Ledger) -> str | None:
    return next((event["data"]["fingerprint"] for event in ledger.events() if event["kind"] == "session_candidate_baseline"), None)


def _changed_session_paths(ledger: Ledger, cwd: Path, paths: list[str]) -> list[str]:
    baseline = next((event["data"].get("path_identities", {}) for event in ledger.events() if event["kind"] == "session_candidate_baseline"), None)
    if baseline is None:
        return paths
    result = []
    for path in paths:
        file = cwd / path
        identity = hashlib.sha256(file.read_bytes()).hexdigest() if file.is_file() and not file.is_symlink() else None
        if baseline.get(path) != identity or path not in baseline:
            result.append(path)
    return result


def _resolved_request(prompt: str) -> str:
    """Keep the submitted prompt and resolve a Codex pasted-request attachment."""
    if "Pasted text contains the user's request" not in prompt:
        return prompt
    attachment_root = (Path.home() / ".codex/attachments").resolve()
    pieces = []
    for raw in re.findall(r"(/[^\n:]+/\.codex/attachments/[A-Za-z0-9-]+/Pasted text\.txt)", prompt):
        path = Path(raw).resolve()
        if path.is_relative_to(attachment_root) and path.is_file() and path.stat().st_size <= 262144:
            pieces.append(f"[Attachment content from {path}]\n{path.read_text(encoding='utf-8')}")
    return prompt + ("\n\n" + "\n\n".join(pieces) if pieces else "")


def _observe_instruction_changes(ledger: Ledger, revision: str, paths: list[str], cwd: Path | None = None) -> None:
    instructions = instruction_paths(paths)
    if not instructions:
        return
    state = ledger.read()
    completion = state["completion_state"]
    prior = set(completion.get("instruction_recomposition_required", []))
    targets = dict(completion.get("instruction_recomposition_targets", {}))
    for path in instructions:
        file = cwd / path if cwd else None
        targets[path] = hashlib.sha256(file.read_bytes()).hexdigest() if file and file.is_file() else revision
    installation = {path for path in completion.get("instruction_installation_required", []) if path.startswith("runtime/instructions/")}
    if cwd and (cwd / "scripts/install_global.py").is_file():
        installation.update(path for path in instructions if path.startswith("runtime/instructions/"))
    source_revision = _run_git(cwd, "rev-parse", "HEAD").decode("utf-8", "replace").strip() if cwd else None
    if prior == prior | set(instructions) and completion.get("candidate_revision") == revision and targets == completion.get("instruction_recomposition_targets", {}) and installation == set(completion.get("instruction_installation_required", [])) and source_revision == completion.get("instruction_source_revision"):
        return
    completion["instruction_recomposition_required"] = sorted(prior | set(instructions))
    completion["instruction_recomposition_targets"] = targets
    completion["instruction_installation_required"] = sorted(installation)
    completion["instruction_source_revision"] = source_revision
    completion["candidate_revision"] = revision
    completion["status"] = "CONTINUE"
    ledger._write_state(state)
    ledger.append_event("instruction_recomposition_required", {"artifacts": instructions, "targets": targets, "candidate_revision": revision})


def _tool_result(event: dict, ledger: Ledger) -> None:
    name = str(event.get("tool_name", "unknown"))
    token = str(event.get("tool_use_id") or digest(event)[:16])
    tool_input = event.get("tool_input")
    tool_response = event.get("tool_response")
    if isinstance(tool_response, str):
        try:
            parsed = json.loads(tool_response)
            if isinstance(parsed, dict):
                tool_response = parsed
        except ValueError:
            pass
    raw = {"tool_name": name, "tool_use_id": token, "turn_id": event.get("turn_id"), "input": tool_input, "response": tool_response}
    raw_dir = ledger.directory / "raw-tools"
    raw_dir.mkdir(exist_ok=True)
    (raw_dir / f"{re.sub('[^A-Za-z0-9_-]', '_', token)}.json").write_bytes(canonical_bytes(raw))
    if name == "collaborationspawn_agent" and isinstance(tool_input, dict):
        response_value = tool_response
        if isinstance(response_value, str):
            try:
                response_value = json.loads(response_value)
            except ValueError:
                response_value = None
        alias = response_value.get("task_name") if isinstance(response_value, dict) else None
        if isinstance(alias, str) and alias.startswith("/root/"):
            message = str(tool_input.get("message", ""))
            requests = ledger.read()["review_schedule"]["requests"]
            matched = [r for r in requests if r.get("package_path") and r["package_path"] in message]
            review_hash = matched[0]["package_hash"] if len(matched) == 1 else None
            ledger.append_event("native_spawn_alias_available", {"alias": alias, "tool_use_id": token, "review_hash": review_hash})
    summary = json.dumps(tool_response, ensure_ascii=False, default=str)[:800]
    status = result_status(tool_response)
    command = str(tool_input.get("command", tool_input.get("cmd", ""))) if isinstance(tool_input, dict) else str(tool_input)[:300]
    if name in {"apply_patch", "Edit", "Write"} or re.search(r"(^|[;&| ])(touch|cp|mv|mkdir|sed -i|tee)\b|(^|[^<>])>(?!>)", command):
        ledger.append_event("artifact_write_observed", {"artifact_ref": str(raw_dir / f"{re.sub('[^A-Za-z0-9_-]', '_', token)}.json"), "tool_use_id": token})
    declaration = tool_input.get("verification") if isinstance(tool_input, dict) else None
    if declaration is None:
        declaration = next((x for x in reversed(ledger.read().get("verification_plans", [])) if x["command_or_tool"] == command), None)
    is_test = verification_command(command, declaration)
    continuation = None
    if not command and isinstance(tool_input, dict) and tool_input.get("session_id") is not None:
        continuation = ledger.read().get("executions", {}).get(str(tool_input["session_id"]))
        if continuation:
            command = continuation["command_or_tool"]
            is_test = continuation["identity"]
    scope = is_test["scope"] if is_test else f"tool:{name}"
    cwd = Path(event.get("cwd") or os.getcwd())
    observed_revision, observed_paths, _ = _candidate(cwd, ledger)
    if "git commit" in command:
        observed_paths += _run_git(cwd, "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").decode("utf-8", "replace").splitlines()
    if observed_revision != _session_baseline(ledger):
        _observe_instruction_changes(ledger, observed_revision, _changed_session_paths(ledger, cwd, observed_paths), cwd)
    _sync_candidate(ledger, observed_revision)
    state = ledger.read()
    index = len(state["verification_chronology"]) + 1
    ref = f"tool:{token}"
    revision = observed_revision
    verification = {"chronology_index": index, "action": "native tool result", "command_or_tool": command or name,
        "scope": scope, "observable_result": summary, "evidence_ref": ref, "status": status, "artifact_revision": revision}
    if is_test:
        started = next((e["data"] for e in reversed(ledger.events()) if e["kind"] == "verification_started" and e["data"]["tool_use_id"] == token), None)
        verification.update(target_identity=observed_revision,
                            related_inputs=["repository"], input_identities={"repository": observed_revision},
                            execution_environment=sys.platform, expensive=True)
        verification.update(is_test)
        if started:
            verification.update(started["identity"])
        if continuation:
            verification.update(continuation["identity"])
            verification["initiating_tool_use_id"] = continuation["initiating_tool_use_id"]
        session_id = tool_response.get("session_id") if isinstance(tool_response, dict) else None
        if session_id is not None and status == "UNKNOWN":
            state = ledger.read()
            state.setdefault("executions", {})[str(session_id)] = {"command_or_tool": command, "initiating_tool_use_id": token,
                "identity": {key: verification[key] for key in ("scope", "target_identity", "input_identities", "related_inputs", "execution_environment", "artifact_revision", "expensive")}, "status": "running"}
            ledger._write_state(state)
        elif continuation and status in {"PASS", "FAIL"}:
            state = ledger.read(); state["executions"][str(tool_input["session_id"])]["status"] = "completed"; ledger._write_state(state)
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


def _sync_candidate(ledger: Ledger, revision: str) -> None:
    state = ledger.read()
    completion = state["completion_state"]
    if completion.get("candidate_revision") == revision:
        return
    completion["candidate_revision"] = revision
    completion["status"] = "CONTINUE"
    for request in state.get("review_schedule", {}).get("requests", []):
        if request["package_hash"] == completion.get("pending_review_hash") and request["candidate_revision"] != revision:
            request["status"] = "obsolete"
            completion["pending_review_hash"] = None
    ledger._write_state(state)
    ledger.append_event("candidate_revision_observed", {"revision": revision})


def _snapshot(cwd: Path, paths: list[str], diff: str) -> dict:
    result = {}
    for path in paths:
        file = cwd / path
        if file.is_file() and not file.is_symlink():
            data = file.read_bytes()
            result[path] = {"sha256": hashlib.sha256(data).hexdigest(), "content": data.decode("utf-8", "replace")}
        elif file.is_symlink():
            result[path] = {"state": "symlink", "target": os.readlink(file)}
        else:
            result[path] = {"state": "deleted or nonregular"}
    return {"artifact_refs": paths, "aggregate_diff": diff, "resulting_state": result}


def _dispatch_message(request: dict, *, catchup: bool = False) -> str:
    return ("Semantic review catch-up: " if catchup else "Execution-time semantic review: ") + (
        f"Spawn one fresh built-in subagent with only frozen package {request['package_path']}. "
        "Require an independently computed SHA-256 receipt and ONLY structured JSON ReviewResult "
        "(review_id, package_hash, reviewer_adapter=builtin_subagent, findings, overall_completion_risk, unresolved_unknowns). "
        "Instruct it not to edit artifacts; this is instruction-level isolation, not restricted tool capability. "
        "Continue independent main work while the child runs. Consume current findings and verify accepted repairs before completion.")


def _pre_tool(event: dict, ledger: Ledger) -> dict | None:
    tool_input = event.get("tool_input") or {}
    command = str(tool_input.get("command", tool_input.get("cmd", ""))) if isinstance(tool_input, dict) else ""
    argv = words(command)
    state = ledger.read()
    reason = None
    if argv and Path(argv[0]).name == "git" and "add" in argv[1:]:
        cwd = Path(event.get("cwd") or os.getcwd())
        untracked = _run_git(cwd, "ls-files", "--others", "--exclude-standard", "-z").decode().split("\0")
        targets = [x for x in argv[argv.index("add") + 1:] if not x.startswith("-")]
        selected = [path for path in untracked if path and (not targets or any(t == "." or path == t or path.startswith(t.rstrip("/") + "/") for t in targets))]
        missing = tracking_reasons(state, selected)
        if missing:
            reason = "New Git-tracked artifacts need a separate persistence decision with owner, future consumer, maintainer, contract/convention and alternatives: " + ", ".join(missing)
    if argv and Path(argv[0]).name == "git" and "commit" in argv[1:]:
        unit = state.get("commit_scope")
        if unit and (unit.get("candidate_revision") != _candidate(Path(event.get("cwd") or os.getcwd()), ledger)[0] or unit.get("remaining_required_work")):
            reason = "The declared commit change unit is not closed. Resolve its known required work; full-suite verification is a separate decision."
        elif not unit:
            reason = "Record a closed commit_scope with candidate_revision, scope, actual message and remaining_required_work before committing. Full verification is separate."
        elif any(flag in argv for flag in ("-m", "--message")):
            messages = [argv[i + 1] for i, arg in enumerate(argv[:-1]) if arg in {"-m", "--message"}]
            if "\n\n".join(messages) != unit["message"]:
                reason = "Commit message differs from the reviewed change-unit declaration. Match the actual scope before committing."
    declaration = tool_input.get("verification") if isinstance(tool_input, dict) else None
    if declaration is None:
        declaration = next((x for x in reversed(ledger.read().get("verification_plans", [])) if x["command_or_tool"] == command), None)
    proposed = verification_command(command, declaration)
    if proposed:
        revision, _, _ = _candidate(Path(event.get("cwd") or os.getcwd()), ledger)
        identity = dict(target_identity=revision, input_identities={"repository": revision}, related_inputs=["repository"], execution_environment=sys.platform, artifact_revision=revision)
        identity.update(proposed)
        proposed = identity
        previous = duplicate_expensive_action(state["verification_chronology"], proposed)
        if previous:
            reason = f"Reuse matching PASS {previous['evidence_ref']}; this identical expensive check adds no protection. For a necessary repeat, declare new_evidence, new_hypothesis, or prior_result_followup."
            ledger.append_event("duplicate_check_prevented", {"command": command, "evidence_ref": previous["evidence_ref"]})
        else:
            ledger.append_event("verification_started", {"tool_use_id": str(event.get("tool_use_id")), "identity": identity})
    if reason:
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": reason}}
    return None


def _stop(event: dict, ledger: Ledger) -> dict | None:
    cwd = Path(event.get("cwd") or os.getcwd())
    fingerprint, paths, diff = _candidate(cwd, ledger)
    changed = fingerprint != _session_baseline(ledger)
    paths = _changed_session_paths(ledger, cwd, paths) if changed else []
    if changed:
        _observe_instruction_changes(ledger, fingerprint, paths, cwd)
    _sync_candidate(ledger, fingerprint)
    state = ledger.read()
    if state.get("lifecycle", {}).get("status") == "cancelled":
        cleanup(ledger)
        ledger.append_event("cancelled_work_stopped", {"running_work": [x["work_item_id"] for x in state["work_items"] if x["status"] == "ACTIVE"]})
        return _context("Stop", "Task cancelled. Stop remaining work and interrupt native workers when supported. Only proven harness scratch was cleaned.")
    def feedback(reason):
        return {"decision": "block", "reason": reason} if not event.get("stop_hook_active") else {"systemMessage": reason}
    if state["request_state"]["interpreted_through"] != len(state["request_history"]):
        return feedback("Latest user request is not reflected in task state. Read ordered request_history and confirm its scope, priorities, active obligations, and change classification with confirm-request; no user ceremony is needed.")
    if not changed and not state["work_items"] and not state["artifacts"] and not state["completion_state"].get("instruction_recomposition_required"):
        ledger.append_event("nonartifact_turn_observed", {"turn_id": event.get("turn_id")})
        return None
    missing_recomposition = [r for r in recomposition_reasons(state) if r["code"] in {"INSTRUCTION_RECOMPOSITION_MISSING", "INSTRUCTION_WHOLE_FILE_REVIEW_MISSING"}]
    if missing_recomposition:
        return feedback("SWE parent gate CONTINUE: instruction recomposition requires complete-file reading and owner integration: " + json.dumps(missing_recomposition))
    assessment = state["review_schedule"]["assessment"]
    if not assessment or assessment["candidate_revision"] != fingerprint or assessment["request_revision"] != state["request_state"]["semantic_revision"]:
        return feedback("Assess the current candidate's semantic risk and review protection value with assess-review. File count and extension are not risk. Use direct/scoped verification for mechanical changes. Select execution-time review at a stable boundary; Stop catch-up is fallback.")
    request = schedule(ledger, _snapshot(cwd, paths, diff), fallback=True)
    if request:
        return feedback(_dispatch_message(request, catchup=True))
    state = ledger.read()
    selection = select_next_actions(state)
    ledger.append_event("action_selection", {"fingerprint": fingerprint, "selection": selection})
    result = evaluate_and_record(ledger)
    if result["status"] == "CONTINUE":
        return feedback("SWE parent completion gate is CONTINUE: " + json.dumps(result["reasons"]) + ". Selection: " + json.dumps(selection) + ". Reuse valid evidence, complete only missing work, consume findings and re-evaluate internally.")
    if result["status"] == "BLOCKED":
        return {"systemMessage": "SWE task is BLOCKED on external input: " + json.dumps(result["external_blockers"])}
    cleanup(ledger)
    return None


def handle(event: dict) -> dict | None:
    ledger = _session(event)
    if ledger is None:
        return None
    kind = event.get("hook_event_name")
    with _locked(ledger):
        if kind == "SessionStart":
            return _context(kind, f"SWE harness is active. Session ledger: {ledger.directory}. Natural-language work requests are recorded automatically. CLI: {shlex.quote(sys.executable)} -m harness.cli. Installation manifest: {Path(sys.executable).parent.parent.parent / 'installation.json'} (source_root locates OPERATIONS.md, REVIEW-PROTOCOL.md and COMPLETION.md).")
        if kind == "UserPromptSubmit":
            prompt = event.get("prompt", "")
            if not isinstance(prompt, str) or not prompt.strip():
                return None
            if not ledger.state_path.exists():
                request = _resolved_request(prompt)
                ledger.create(str(event["session_id"]), request[:500], request)
                ledger.update("obligations", {"id": "user-request", "description": request[:1000], "status": "IN_PROGRESS", "evidence_refs": []})
                ledger.append_event("session_bound", {"session_id": event["session_id"], "cwd": event.get("cwd")})
                cwd = Path(event.get("cwd") or os.getcwd())
                baseline, paths, _ = _candidate(cwd, ledger)
                baseline_paths = _run_git(cwd, "ls-files", "-co", "--exclude-standard", "-z").decode("utf-8", "replace").split("\0")
                identities = {path: hashlib.sha256((cwd / path).read_bytes()).hexdigest() if (cwd / path).is_file() and not (cwd / path).is_symlink() else None for path in baseline_paths if path}
                baseline_state = _snapshot(cwd, [path for path in baseline_paths if path], "")["resulting_state"]
                (ledger.directory / "candidate-baseline.json").write_bytes(canonical_bytes(baseline_state))
                ledger.append_event("session_candidate_baseline", {"fingerprint": baseline, "path_identities": identities})
            else:
                ledger.receive_request(_resolved_request(prompt), event.get("turn_id"))
            return _context(kind, f"SWE task ledger is {ledger.directory}. Ordered request history and parent obligations are recorded. Interpret new turns with confirm-request, preserving scope separately from priority. Assess semantic risk and schedule review during execution at meaningful boundaries; the lifecycle hooks capture native tool results and enforce review/completion. No user harness command is needed.")
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
        if kind == "PreToolUse":
            return _pre_tool(event, ledger)
        if kind in {"PreCompact", "SessionEnd"}:
            _checkpoint(ledger)
            return None
        if kind == "PostToolUse":
            _tool_result(event, ledger)
            cwd = Path(event.get("cwd") or os.getcwd())
            _, paths, diff = _candidate(cwd, ledger)
            request = schedule(ledger, _snapshot(cwd, _changed_session_paths(ledger, cwd, paths), diff))
            if request:
                return _context(kind, _dispatch_message(request))
        elif kind == "SubagentStart":
            agent_id = str(event.get("agent_id") or "")
            ledger.append_event("native_subagent_started", {"agent_id": agent_id, "agent_type": event.get("agent_type"), "turn_id": event.get("turn_id")})
            if agent_id:
                # Native starts do not expose a dispatch correlation key. Never infer role
                # from event order or the number of pending aliases. Reconcile from receipts.
                alias = None
                ledger.append_event("native_child_identity_unclassified", {"agent_id": agent_id, "reason": "No native dispatch correlation key"})
                work_id = "native-" + re.sub(r"[^A-Za-z0-9_-]", "_", agent_id)
                if not any(item["work_item_id"] == work_id for item in ledger.read()["work_items"]):
                    ledger.update("work_items", {"work_item_id": work_id, "parent_id": ledger.read()["task_id"],
                        "objective": f"Native subagent {event.get('agent_type') or 'work'}", "owner": agent_id, "status": "ACTIVE", "semantic_role": "unclassified",
                        "dependencies": [], "produced_changes": [], "verification_refs": [], "evidence_refs": [],
                        "remaining_issues": [], "integration_notes": "Await native result and parent integration"})
                    ledger.update("delegated_work", {"id": work_id, "work_item_id": work_id, "owner": agent_id,
                        "expected_result": "native subagent result", "return_destination": ledger.read()["task_id"],
                        "status": "DISPATCHED", "semantic_role": "unclassified", "result_refs": [], "consumed_refs": [], "integration_refs": [],
                        "aliases": [alias, alias.rsplit("/", 1)[-1]] if alias else [],
                        "return_aliases": [alias.rsplit("/", 1)[0]] if alias else []})
        elif kind == "SubagentStop":
            message = event.get("last_assistant_message") or ""
            result = _parse_result(message)
            pending = ledger.read()["completion_state"].get("pending_review_hash")
            agent_id = str(event.get("agent_id") or "")
            review_request = next((x for x in ledger.read()["review_schedule"]["requests"] if result and x["package_hash"] == result.get("package_hash") and x.get("native_subagent_id") in {None, agent_id}), None)
            if result and review_request:
                package_files = list(ledger.directory.glob("*-review-*.json"))
                package = next((json.loads(p.read_text()) for p in package_files if digest(json.loads(p.read_text())) == result.get("package_hash")), None)
                if package is not None:
                    activation = {"native_subagent_id": event.get("agent_id"), "package_received": True,
                        "package_hash_verified": result["package_hash"], "role_integrity": "read-only semantic evaluator", "isolation": "instruction", "write_capability_removed": False}
                    review = BuiltinSubagentAdapter(ledger).ingest(package, result, activation)
                    fingerprint, _, _ = _candidate(Path(event.get("cwd") or os.getcwd()), ledger)
                    state = ledger.read()
                    state["reviews"][-1]["observed_return_candidate"] = fingerprint
                    ledger._write_state(state)
                    ledger.append_event("review_artifact_fingerprint_recorded", {"review_id": review["review_id"], "fingerprint": fingerprint})
                    return _context(kind, f"SWE review {review['review_id']} was ingested into the parent ledger. Consume and resolve every blocking finding before completion.")
            agent_id = str(event.get("agent_id") or "")
            result_ref = "subagent:" + re.sub(r"[^A-Za-z0-9_-]", "_", agent_id)
            ledger.append_event("native_subagent_returned", {"agent_id": agent_id, "turn_id": event.get("turn_id"), "result_hash": digest(message)})
            state = ledger.read()
            work = next((item for item in state["work_items"] if item["work_item_id"] == "native-" + re.sub(r"[^A-Za-z0-9_-]", "_", agent_id)), None)
            if work:
                state = ledger.read()
                for item in state["work_items"] + state["delegated_work"]:
                    if item.get("owner") == agent_id:
                        item["semantic_role"] = "worker"
                ledger._write_state(state)
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
