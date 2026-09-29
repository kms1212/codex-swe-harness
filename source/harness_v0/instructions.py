"""Track instruction changes as a recomposition of their current owners."""
from __future__ import annotations

from pathlib import PurePosixPath

OUTCOMES = {"existing", "integrated", "moved", "new_owner"}


def instruction_paths(paths: list[str]) -> list[str]:
    """Recognize engineering instructions without treating every document as policy."""
    result = []
    for raw in paths:
        path = PurePosixPath(raw.replace("\\", "/"))
        if path.name in {"AGENTS.md", "CLAUDE.md"} or path.name.endswith(".instructions.md") or (
            "instructions" in path.parts and path.suffix == ".md"
        ):
            result.append(raw)
    return sorted(set(result))


def recomposition_reasons(state: dict) -> list[dict]:
    completion = state["completion_state"]
    revision = completion.get("candidate_revision")
    records = state.get("instruction_changes", [])
    known = {entry["evidence_id"] for entry in state["evidence"]}
    checks = {entry["evidence_ref"]: entry for entry in state["verification_chronology"]}
    reasons = []
    for artifact in completion.get("instruction_recomposition_required", []):
        target = completion.get("instruction_recomposition_targets", {}).get(artifact)
        record = next((x for x in reversed(records) if x["artifact"] == artifact and x["target_identity"] == target), None)
        if record is None:
            reasons.append({"code": "INSTRUCTION_RECOMPOSITION_MISSING", "artifact": artifact})
            continue
        if record["whole_file_review_ref"] not in known | checks.keys():
            reasons.append({"code": "INSTRUCTION_WHOLE_FILE_REVIEW_MISSING", "artifact": artifact})
        active = checks.get(record["active_check_ref"])
        if not active or active["status"] != "PASS" or not active.get("consumer_point") or active.get("target_identity") != target or (record.get("installation_required") and active.get("artifact_revision") != revision):
            reasons.append({"code": "INSTRUCTION_ACTIVE_CHECK_MISSING", "artifact": artifact})
        installation_required = artifact in completion.get("instruction_installation_required", [])
        if installation_required and (not record.get("installation_required") or record.get("installed_revision") != completion.get("instruction_source_revision")):
            reasons.append({"code": "INSTRUCTION_INSTALLATION_MISSING", "artifact": artifact})
    return reasons
