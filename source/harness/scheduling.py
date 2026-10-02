"""Candidate-bound review selection and coalescing, independent of transport."""
from __future__ import annotations

from .core import Ledger, review_context_hash
from .review import BuiltinSubagentAdapter, build_package, route_review


def coverage(state: dict) -> bool:
    return any(review.get("candidate_revision") == state["completion_state"].get("candidate_revision")
               and review.get("review_context_hash") == review_context_hash(state)
               for review in state["reviews"])


def assess(ledger: Ledger, assessment: dict) -> dict:
    state = ledger.read()
    if assessment.get("candidate_revision") != state["completion_state"].get("candidate_revision"):
        raise ValueError("review assessment must identify the current candidate")
    if not isinstance(assessment.get("semantic_risk"), bool) or not assessment.get("reason"):
        raise ValueError("current semantic risk and additional protection rationale required")
    if not assessment.get("change_types") or any(x not in {"code", "documentation", "architecture", "integration", "user_artifact", "completion"} for x in assessment["change_types"]):
        raise ValueError("semantic change types required")
    assessment = dict(assessment, request_revision=state["request_state"]["semantic_revision"])
    state["review_schedule"]["assessment"] = assessment
    state["completion_state"]["semantic_review_required"] = assessment["semantic_risk"]
    pending = state["completion_state"].get("pending_review_hash")
    for request in state["review_schedule"]["requests"]:
        if request["package_hash"] == pending and (request["candidate_revision"] != assessment["candidate_revision"] or request["request_revision"] != assessment["request_revision"]):
            request["status"] = "obsolete"
            state["completion_state"]["pending_review_hash"] = None
    ledger._write_state(state)
    ledger.append_event("review_assessed", assessment)
    return assessment


def schedule(ledger: Ledger, candidate: dict, *, fallback: bool = False) -> dict | None:
    state = ledger.read()
    assessment = state["review_schedule"]["assessment"]
    if state["request_state"]["interpreted_through"] != len(state["request_history"]):
        return None
    if not assessment or assessment["candidate_revision"] != state["completion_state"].get("candidate_revision") or assessment["request_revision"] != state["request_state"]["semantic_revision"]:
        return None
    if not assessment["semantic_risk"] or coverage(state):
        return None
    if state["completion_state"].get("pending_review_hash"):
        return None  # Coalesce updates until a new stable boundary is assessed.
    routing = route_review(assessment["change_types"], semantic_risk=True)
    package = build_package(state, routing, candidate, candidate["artifact_refs"])
    request = BuiltinSubagentAdapter(ledger).prepare(package)
    ledger.append_event("review_scheduled", {"phase": "stop_catchup" if fallback else "execution", **request})
    return request
