"""Evidence-based parent completion and progress evaluation."""
from __future__ import annotations

from .core import Ledger, review_context_hash
from .optimization import duplicate_expensive_action, parallelizable, running_work_value, select_next_actions, verification_reusable
from .instructions import recomposition_reasons


def _latest_verification(state: dict, scope: str) -> dict | None:
    completion = state["completion_state"]
    identity = completion.get("scope_identities", {}).get(scope)
    environment = completion.get("scope_environments", {}).get(scope)
    inputs = completion.get("scope_input_identities", {}).get(scope)
    matches = [entry for entry in state["verification_chronology"] if entry["scope"] == scope
               and (identity is None or entry.get("target_identity") == identity)
               and (environment is None or entry.get("execution_environment") == environment)
               and (inputs is None or entry.get("input_identities") == inputs)]
    return matches[-1] if matches else None


def _available_work_items(state: dict) -> list[dict]:
    status_by_id = {item["work_item_id"]: item["status"] for item in state["work_items"]}
    return [item for item in state["work_items"]
            if item["status"] in {"READY", "ACTIVE"}
            and not item["remaining_issues"]
            and all(status_by_id.get(dependency) == "INTEGRATED" for dependency in item["dependencies"])]


def evaluate_completion(state: dict) -> dict:
    """Return COMPLETE, CONTINUE or BLOCKED without equating worker success to parent success."""
    reasons: list[dict] = []
    if not state["obligations"]:
        reasons.append({"code": "OBLIGATIONS_UNDECLARED"})
    for obligation in state["obligations"]:
        if obligation["status"] != "SATISFIED":
            reasons.append({"code": "OBLIGATION_REMAINING", "id": obligation["id"]})
        elif not obligation.get("evidence_refs"):
            reasons.append({"code": "OBLIGATION_EVIDENCE_MISSING", "id": obligation["id"]})
    for item in state["work_items"]:
        if item["status"] != "INTEGRATED":
            reasons.append({"code": "WORK_ITEM_NOT_INTEGRATED", "id": item["work_item_id"]})
    for delegated in state["delegated_work"]:
        if delegated["status"] != "CONSUMED" or not delegated["consumed_refs"]:
            reasons.append({"code": "DELEGATED_RESULT_UNCONSUMED", "id": delegated["id"]})
    integration = state["integration_state"]
    if integration["conflicts"] or integration["unresolved_dependencies"]:
        reasons.append({"code": "INTEGRATION_UNRESOLVED"})
    candidate = set(integration["candidate_changes"])
    if candidate - set(integration["integrated_changes"]):
        reasons.append({"code": "CHANGES_NOT_INTEGRATED", "changes": sorted(candidate - set(integration["integrated_changes"]))})
    completion = state["completion_state"]
    if completion.get("pending_review_hash"):
        reasons.append({"code": "REVIEW_RESULT_PENDING", "package_hash": completion["pending_review_hash"]})
    evidence_refs = set(completion["evidence_refs"])
    known_refs = {item["evidence_id"] for item in state["evidence"]} | {item["evidence_ref"] for item in state["verification_chronology"]}
    revision = completion.get("candidate_revision")
    if not revision:
        reasons.append({"code": "CANDIDATE_REVISION_UNDECLARED"})
    if not completion["required_verification_scopes"] and not completion["required_consumer_scopes"]:
        reasons.append({"code": "VERIFICATION_REQUIREMENTS_UNDECLARED"})
    for obligation in state["obligations"]:
        evidence_refs.update(obligation.get("evidence_refs", []))
        if obligation["status"] == "SATISFIED" and any(ref not in known_refs for ref in obligation.get("evidence_refs", [])):
            reasons.append({"code": "OBLIGATION_EVIDENCE_UNKNOWN", "id": obligation["id"]})
    for scope in completion["required_verification_scopes"]:
        latest = _latest_verification(state, scope)
        if not verification_reusable(latest, completion.get("scope_identities", {}).get(scope), revision, completion.get("scope_environments", {}).get(scope), completion.get("scope_input_identities", {}).get(scope)):
            reasons.append({"code": "VERIFICATION_MISSING_OR_FAILING", "scope": scope})
        else:
            evidence_refs.add(latest["evidence_ref"])
    for scope in completion["required_consumer_scopes"]:
        latest = _latest_verification(state, scope)
        if not verification_reusable(latest, completion.get("scope_identities", {}).get(scope), revision, completion.get("scope_environments", {}).get(scope), completion.get("scope_input_identities", {}).get(scope)) or not latest.get("consumer_point"):
            reasons.append({"code": "CONSUMER_EVIDENCE_MISSING", "scope": scope})
        else:
            evidence_refs.add(latest["evidence_ref"])
    reasons.extend(recomposition_reasons(state))
    if completion["semantic_review_required"]:
        if not state["reviews"]:
            reasons.append({"code": "SEMANTIC_REVIEW_MISSING"})
        else:
            if state["reviews"][-1].get("candidate_revision") != revision:
                reasons.append({"code": "CURRENT_CANDIDATE_NOT_REVIEWED", "candidate_revision": revision})
            if state["reviews"][-1].get("review_context_hash") != review_context_hash(state):
                reasons.append({"code": "CURRENT_REQUIREMENTS_NOT_REVIEWED"})
    for review in state["reviews"]:
        if not review.get("activation", {}).get("native_subagent_id"):
            reasons.append({"code": "REVIEW_ACTIVATION_UNVERIFIED", "review_id": review["review_id"]})
        for index, finding in enumerate(review["findings"]):
            if not finding["blocking"]:
                continue
            if finding.get("disposition") not in {"accepted", "partially_accepted", "rejected"} or not finding.get("resolution_evidence"):
                reasons.append({"code": "BLOCKING_FINDING_UNRESOLVED", "review_id": review["review_id"], "finding_index": index})
            if finding.get("disposition") in {"accepted", "partially_accepted"}:
                finding_key = f"{review['review_id']}:{index}"
                later_pass_refs = {entry["evidence_ref"] for entry in state["verification_chronology"]
                                   if entry["chronology_index"] > review.get("verification_cutoff_index", -1)
                                   and finding_key in entry.get("resolves", [])
                                   and (finding["criterion"] != 14 or entry.get("consumer_point"))
                                   and verification_reusable(entry, completion.get("scope_identities", {}).get(entry["scope"]), revision,
                                                             completion.get("scope_environments", {}).get(entry["scope"]),
                                                             completion.get("scope_input_identities", {}).get(entry["scope"]))}
                if not set(finding.get("resolution_evidence", [])) & later_pass_refs:
                    reasons.append({"code": "REPAIR_VERIFICATION_MISSING", "review_id": review["review_id"], "finding_index": index})
        if review["disposition"] != "RESOLVED":
            reasons.append({"code": "REVIEW_NOT_CONSUMED", "review_id": review["review_id"]})
    live_blockers = [item for item in state["blockers"] if item.get("status") != "RESOLVED"]
    available_work = _available_work_items(state)
    blocked_items = {item["work_item_id"] for item in state["work_items"] if item["status"] == "BLOCKED"}
    linked_blocked_items = {work_item_id for blocker in live_blockers if blocker["external"] for work_item_id in blocker.get("work_item_ids", [])}
    linked_obligations = {obligation_id for blocker in live_blockers if blocker["external"] for obligation_id in blocker.get("obligation_ids", [])}
    def externally_blocked(reason: dict) -> bool:
        if reason["code"] == "WORK_ITEM_NOT_INTEGRATED":
            return reason["id"] in blocked_items and reason["id"] in linked_blocked_items
        if reason["code"] == "OBLIGATION_REMAINING":
            return reason["id"] in linked_obligations
        return False
    only_externally_blocked_work = bool(reasons) and all(externally_blocked(reason) for reason in reasons)
    if live_blockers and all(item["external"] for item in live_blockers) and not available_work and only_externally_blocked_work:
        return {"status": "BLOCKED", "reasons": reasons, "external_blockers": [{"id": x["id"], "required_input": x["required_input"]} for x in live_blockers], "completion_evidence_refs": []}
    if live_blockers:
        reasons.extend({"code": "EXTERNAL_BLOCKER" if x["external"] else "INTERNAL_BLOCKER", "id": x["id"]} for x in live_blockers)
    if reasons:
        return {"status": "CONTINUE", "reasons": reasons, "remaining_obligations": [x["id"] for x in state["obligations"] if x["status"] != "SATISFIED"], "completion_evidence_refs": []}
    return {"status": "COMPLETE", "reasons": [], "completion_evidence_refs": sorted(evidence_refs)}


def evaluate_and_record(ledger: Ledger) -> dict:
    result = evaluate_completion(ledger.read())
    ledger.append_event("completion_evaluated", result)
    state = ledger.read()
    state["completion_state"]["status"] = result["status"]
    state["completion_state"]["evidence_refs"] = result["completion_evidence_refs"]
    ledger._write_state(state)
    return result


def progress_snapshot(state: dict) -> dict:
    actions = _available_work_items(state)
    history = state["verification_chronology"]
    repetitions = []
    for previous, current in zip(history, history[1:]):
        if previous["command_or_tool"] == current["command_or_tool"] and previous["scope"] == current["scope"] and previous["observable_result"] == current["observable_result"]:
            repetitions.append([previous["chronology_index"], current["chronology_index"]])
    redundant = []
    for index, entry in enumerate(history):
        prior = duplicate_expensive_action(history[:index], entry)
        if prior:
            redundant.append([prior["chronology_index"], entry["chronology_index"]])
    running = {item["work_item_id"]: running_work_value(item, history) for item in state["work_items"] if item["status"] == "ACTIVE"}
    parallel_pairs = [[left["work_item_id"], right["work_item_id"]] for i, left in enumerate(actions) for right in actions[i + 1:] if parallelizable(left, right)]
    return {"authorized_remaining_work": [x["id"] for x in state["obligations"] if x["status"] != "SATISFIED"],
            "available_next_actions": [x["work_item_id"] for x in actions],
            "selection": select_next_actions(state),
            "unresolved_blockers": [x["id"] for x in state["blockers"] if x.get("status") != "RESOLVED"],
            "repeated_actions": repetitions, "duplicate_expensive_actions": redundant,
            "running_work_value": running, "parallelizable_pairs": parallel_pairs}
