"""Select the smallest useful next check from scoped evidence and live work."""
from __future__ import annotations

from typing import Iterable


def verification_reusable(entry: dict | None, expected_identity: str | None, candidate_revision: str | None, environment: str | None = None, input_identities: dict[str, str] | None = None) -> bool:
    if not entry or entry.get("status") != "PASS":
        return False
    if expected_identity is not None:
        if entry.get("target_identity") != expected_identity:
            return False
    elif entry.get("artifact_revision") != candidate_revision:
        return False
    if environment is not None and entry.get("execution_environment") != environment:
        return False
    if entry.get("related_inputs") and (input_identities is None or entry.get("input_identities") != input_identities or set(input_identities) != set(entry["related_inputs"])):
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
    if "code" in change_types:
        return "scoped_checks" if len(change_types) == 1 else "semantic_review"
    if deterministic and len(change_types) == 1:
        return "lightweight"
    if "documentation" in change_types or "user_artifact" in change_types:
        return "semantic_review"
    return "scoped_checks"


def is_trivial_diff(paths: list[str], diff: str) -> bool:
    if len(paths) != 1 or "--- /dev/null" in diff:
        return False
    edits = [line for line in diff.splitlines() if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))]
    return 1 <= len(edits) <= 2 and sum(line.startswith("+") for line in edits) <= 1 and sum(line.startswith("-") for line in edits) <= 1 and not any(word in " ".join(edits).lower() for word in ("permission", "security", "auth", "compatib", "version"))


def duplicate_expensive_action(history: Iterable[dict], proposed: dict) -> dict | None:
    if not proposed.get("expensive"):
        return None
    for prior in reversed(list(history)):
        if all(prior.get(key) == proposed.get(key) for key in ("command_or_tool", "scope", "target_identity", "input_identities", "execution_environment")) and prior.get("status") == "PASS":
            return prior
    return None


def running_work_value(work: dict, available_evidence: Iterable[dict]) -> str:
    """A completed equivalent result makes cancelable running work obsolete."""
    if work.get("status") != "ACTIVE":
        return "not_running"
    target = work.get("target_identity")
    scope = work.get("verification_scope")
    if target and scope and any(item.get("scope") == scope and item.get("target_identity") == target and item.get("input_identities") == work.get("input_identities") and item.get("status") == "PASS" for item in available_evidence):
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


def select_next_actions(state: dict, proposed: dict | None = None) -> dict:
    """Select evidence to reuse and only the checks still needed by this candidate.

    This is advisory for Codex tool choice; the completion evaluator remains the
    authority on whether the declared evidence is sufficient.
    """
    completion = state["completion_state"]
    history = state["verification_chronology"]
    reuse, run = {}, []
    for scope in dict.fromkeys(completion["required_verification_scopes"] + completion["required_consumer_scopes"]):
        identity = completion.get("scope_identities", {}).get(scope)
        environment = completion.get("scope_environments", {}).get(scope)
        inputs = completion.get("scope_input_identities", {}).get(scope)
        matches = [entry for entry in history if entry["scope"] == scope
                   and (identity is None or entry.get("target_identity") == identity)
                   and (environment is None or entry.get("execution_environment") == environment)
                   and (inputs is None or entry.get("input_identities") == inputs)]
        latest = matches[-1] if matches else None
        if verification_reusable(latest, identity, completion.get("candidate_revision"), environment, inputs) and (scope not in completion["required_consumer_scopes"] or latest.get("consumer_point")):
            reuse[scope] = latest["evidence_ref"]
        else:
            run.append(scope)
    cancel = [item["work_item_id"] for item in state["work_items"]
              if running_work_value(item, history) == "cancel_if_possible"]
    result = {"reuse_verification": reuse, "run_verification": run,
              "cancel_running_if_supported": cancel,
              "modalities": {"REQUIRED": {"missing_declared_scopes": run},
                             "PERMITTED": {"authority_model": state["authority"]["policy_model"],
                                           "capabilities": state["authority"].get("capabilities", [])},
                             "CONDITIONAL": {"review_and_extra_tests": "select for current semantic risk and protection gap"},
                             "STOP_ECONOMY": {"reused_scopes": reuse, "obsolete_running_work": cancel}}}
    if proposed is not None:
        prior = duplicate_expensive_action(history, proposed)
        result["proposed_action"] = {"decision": "reuse" if prior else "run",
                                     "evidence_ref": prior.get("evidence_ref") if prior else None}
    return result
