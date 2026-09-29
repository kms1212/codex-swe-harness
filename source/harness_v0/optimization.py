"""Select the smallest useful next check from scoped evidence and live work."""
from __future__ import annotations

from typing import Iterable


def verification_reusable(entry: dict | None, expected_identity: str | None, candidate_revision: str | None, environment: str | None = None) -> bool:
    if not entry or entry.get("status") != "PASS":
        return False
    if expected_identity is not None:
        if entry.get("target_identity") != expected_identity:
            return False
    elif entry.get("artifact_revision") != candidate_revision:
        return False
    if environment is not None and entry.get("execution_environment") != environment:
        return False
    return True


def impacted_scopes(changed_inputs: Iterable[str], checks: Iterable[dict]) -> list[str]:
    changed = set(changed_inputs)
    return sorted({check["scope"] for check in checks if changed.intersection(check.get("related_inputs", []))})


def select_checks(changed_inputs: Iterable[str], checks: Iterable[dict]) -> list[dict]:
    changed = set(changed_inputs)
    return [check for check in checks if changed.intersection(check.get("related_inputs", []))]


def review_path(change_types: list[str], *, deterministic: bool = False, semantic_risk: bool = False) -> str:
    if semantic_risk or "architecture" in change_types or "integration" in change_types:
        return "semantic_review"
    if deterministic and len(change_types) == 1:
        return "lightweight"
    if "documentation" in change_types or "user_artifact" in change_types:
        return "semantic_review"
    return "scoped_checks"


def is_trivial_diff(paths: list[str], diff: str) -> bool:
    if len(paths) != 1 or "--- /dev/null" in diff:
        return False
    edits = [line for line in diff.splitlines() if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))]
    return len(edits) == 1 and not any(word in edits[0].lower() for word in ("permission", "security", "auth", "compatib", "version"))


def duplicate_expensive_action(history: Iterable[dict], proposed: dict) -> dict | None:
    if not proposed.get("expensive"):
        return None
    for prior in reversed(list(history)):
        if all(prior.get(key) == proposed.get(key) for key in ("command_or_tool", "scope", "target_identity", "execution_environment")) and prior.get("status") == "PASS":
            return prior
    return None


def running_work_value(work: dict, available_evidence: Iterable[dict]) -> str:
    """A completed equivalent result makes cancelable running work obsolete."""
    if work.get("status") != "ACTIVE":
        return "not_running"
    target = work.get("target_identity")
    scope = work.get("verification_scope")
    if target and scope and any(item.get("scope") == scope and item.get("target_identity") == target and item.get("status") == "PASS" for item in available_evidence):
        return "cancel_if_possible" if work.get("cancelable", False) else "ignore_duplicate_result"
    return "continue"


def parallelizable(left: dict, right: dict, *, priority: str = "balanced") -> bool:
    if left.get("work_item_id") in right.get("dependencies", []) or right.get("work_item_id") in left.get("dependencies", []):
        return False
    if set(left.get("write_targets", [])) & set(right.get("write_targets", [])):
        return False
    if priority == "cost" and (left.get("integration_cost", 0) + right.get("integration_cost", 0)) >= left.get("estimated_wall_time", 0) + right.get("estimated_wall_time", 0):
        return False
    return True
