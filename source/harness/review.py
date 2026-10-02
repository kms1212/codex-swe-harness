"""Frozen evidence contract, rubric routing, and native subagent handoff."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from .core import Ledger, canonical_bytes, digest, review_context_hash

RUBRIC = {
    1: "request fidelity", 2: "reason for each element", 3: "semantic ownership",
    4: "information lifetime", 5: "existing artifact fidelity", 6: "structural integration",
    7: "change completeness", 8: "root cause", 9: "version compatibility",
    10: "fact judgment uncertainty", 11: "current state accuracy",
    12: "user visible information", 13: "test quality", 14: "consumer verification",
    15: "completion",
}
PROJECTIONS = {
    "architecture": [1, 2, 3, 4, 5, 6, 10, 11, 15],
    "documentation": [1, 2, 3, 4, 5, 6, 10, 11, 15],
    "code": [1, 7, 8, 9, 10, 13, 14, 15],
    "user_artifact": [1, 2, 5, 6, 12, 14, 15],
    "integration": [1, 5, 6, 7, 9, 10, 14, 15],
    "completion": [1, 10, 11, 14, 15],
}


def route_review(change_types: list[str], semantic_risk: bool = False) -> dict:
    selected = sorted({criterion for kind in change_types for criterion in PROJECTIONS.get(kind, [])})
    required = bool(selected and (semantic_risk or any(kind in {"architecture", "documentation", "integration", "user_artifact", "completion"} for kind in change_types)))
    return {"required": required, "change_types": change_types, "criteria": selected,
            "rubric": [{"criterion": i, "description": RUBRIC[i]} for i in selected]}


def build_package(state: dict, routing: dict, candidate_result: dict, source_refs: list[str]) -> dict:
    required = {"artifact_refs", "aggregate_diff", "resulting_state"}
    if not required <= candidate_result.keys():
        raise ValueError("candidate result incomplete")
    chronology = state["verification_chronology"]
    if [item["chronology_index"] for item in chronology] != list(range(1, len(chronology) + 1)):
        raise ValueError("verification chronology incomplete")
    package = {
        "schema_version": 1, "package_id": f"{state['task_id']}-review-{len(state.get('review_schedule', {}).get('requests', [])) + 1}",
        "task_id": state["task_id"], "original_request": state["original_request"],
        "request_history": state["request_history"], "request_state": state["request_state"],
        "confirmed_requirements": [x for x in state["obligations"] if x["status"] not in {"REJECTED", "SUPERSEDED"}],
        "confirmed_decisions": [x for x in state["decisions"] if x["status"] == "CONFIRMED" and not x["superseded_by"]],
        "decision_history": state["decisions"],
        "review_context_hash": review_context_hash(state),
        "relevant_task_state": {key: state[key] for key in ("objective", "work_items", "delegated_work", "integration_state", "completion_state", "blockers")},
        "relevant_epistemic_state": state["epistemic"],
        "artifact_context": state["artifacts"], "instruction_changes": state.get("instruction_changes", []), "candidate_result": candidate_result,
        "verification_chronology": chronology,
        "unresolved_state": [x for x in state["epistemic"] if x["classification"] == "UNKNOWN"] + [x for x in state["blockers"] if x.get("status") != "RESOLVED"],
        "applicable_rubric": routing["rubric"], "source_refs": source_refs,
        "authority": state["authority"],
    }
    return package


class SemanticReview(Protocol):
    def review(self, package: dict, rubric_projection: list[dict]) -> dict: ...


def validate_result(result: dict, package_hash: str, adapter: str, criteria: set[int]) -> None:
    if not isinstance(result.get("review_id"), str) or not result["review_id"]:
        raise ValueError("review id required")
    if result.get("package_hash") != package_hash or result.get("reviewer_adapter") != adapter:
        raise ValueError("review receipt mismatch")
    if result.get("overall_completion_risk") not in {"low", "medium", "high", "unknown"}:
        raise ValueError("invalid completion risk")
    if not isinstance(result.get("findings"), list) or not isinstance(result.get("unresolved_unknowns"), list):
        raise ValueError("structured findings and unknowns required")
    for finding in result["findings"]:
        if not {"criterion", "severity", "evidence_refs", "violated_requirement", "blocking", "confidence"} <= finding.keys():
            raise ValueError("finding incomplete")
        if finding["criterion"] not in criteria or finding["severity"] not in {"minor", "major", "critical"}:
            raise ValueError("finding outside rubric")
        if not isinstance(finding["blocking"], bool) or not isinstance(finding["confidence"], (int, float)) or not 0 <= finding["confidence"] <= 1:
            raise ValueError("invalid finding calibration")
        if not finding["evidence_refs"] or not finding["violated_requirement"]:
            raise ValueError("finding needs evidence and requirement")


class BuiltinSubagentAdapter:
    """Native collaboration bridge: caller dispatches the generated request to a fresh subagent.

    Python cannot call the host's collaboration tools itself. The bridge records a frozen
    handoff and rejects a result unless the caller supplies native activation evidence.
    """
    name = "builtin_subagent"

    def __init__(self, ledger: Ledger):
        self.ledger = ledger

    def prepare(self, package: dict) -> dict:
        content = canonical_bytes(package)
        receipt = digest(package)
        package_path = self.ledger.directory / f"{package['package_id']}.json"
        if package_path.exists():
            raise FileExistsError(package_path)
        package_path.write_bytes(content)
        state = self.ledger.read()
        state["completion_state"]["pending_review_hash"] = receipt
        state["completion_state"]["status"] = "CONTINUE"
        state["review_schedule"]["requests"].append({"package_hash": receipt, "candidate_revision": state["completion_state"].get("candidate_revision"), "request_revision": state["request_state"]["semantic_revision"], "status": "pending", "package_path": str(package_path.absolute())})
        self.ledger._write_state(state)
        request = {"adapter": self.name, "package_path": str(package_path.absolute()), "package_hash": receipt,
                   "instruction": "Fresh semantic evaluator. Read only the frozen package. Verify SHA-256 of its bytes. Return one JSON ReviewResult with package_hash, reviewer_adapter=builtin_subagent, findings, overall_completion_risk and unresolved_unknowns. Do not edit artifacts."}
        self.ledger.append_event("review_requested", request)
        return request

    def ingest(self, package: dict, result: dict, activation: dict) -> dict:
        package_path = self.ledger.directory / f"{package['package_id']}.json"
        expected_hash = digest(package)
        if package_path.read_bytes() != canonical_bytes(package):
            raise ValueError("package changed after freeze")
        if not activation.get("native_subagent_id") or activation.get("package_hash_verified") != expected_hash or not activation.get("package_received") or activation.get("role_integrity") != "read-only semantic evaluator":
            self.ledger.append_event("review_activation_failed", {"package_hash": expected_hash, "activation": activation})
            raise ValueError("native subagent activation not evidenced")
        self.ledger.append_event("reviewer_activated", {"native_subagent_id": activation["native_subagent_id"], "package_hash": expected_hash})
        self.ledger.append_event("package_received", {"native_subagent_id": activation["native_subagent_id"], "package_hash": expected_hash})
        self.ledger.append_event("package_hash_verified", {"native_subagent_id": activation["native_subagent_id"], "package_hash": expected_hash})
        try:
            validate_result(result, expected_hash, self.name, {x["criterion"] for x in package["applicable_rubric"]})
        except ValueError as error:
            self.ledger.append_event("review_result_invalid", {"package_hash": expected_hash, "error": str(error)})
            raise
        self.ledger.append_event("review_completed", {"package_hash": expected_hash, "result": result})
        review = {"review_id": result["review_id"], "evidence_package_hash": expected_hash, "reviewer_adapter": self.name,
                  "findings": result["findings"], "disposition": "RESOLVED" if not result["findings"] else "UNRESOLVED", "resolution_evidence": [], "activation": activation,
                  "verification_cutoff_index": max((entry["chronology_index"] for entry in package["verification_chronology"]), default=0),
                  "candidate_revision": package["relevant_task_state"]["completion_state"].get("candidate_revision"),
                  "review_context_hash": package["review_context_hash"]}
        review["activation"] = dict(activation, isolation="instruction", write_capability_removed=False)
        self.ledger.update("reviews", review, event_kind="findings_received")
        receipt_ref = f"review:{result['review_id']}"
        self.ledger.update("evidence", {"evidence_id": receipt_ref, "producer": activation["native_subagent_id"],
            "operation": "native semantic review receipt", "observable_result": json.dumps(result, ensure_ascii=False), "scope": "review-receipt",
            "chronology_index": max(1, len(self.ledger.read()["verification_chronology"])), "artifact_refs": [str(package_path)]})
        state = self.ledger.read()
        for item in state["work_items"]:
            if item.get("owner") == activation["native_subagent_id"]:
                item.update(semantic_role="reviewer", status="INTEGRATED", evidence_refs=[receipt_ref], integration_notes="Role reconciled from validated native package receipt")
        for item in state["delegated_work"]:
            if item.get("owner") == activation["native_subagent_id"]:
                item.update(semantic_role="reviewer", status="CONSUMED", result_refs=[receipt_ref], consumed_refs=[receipt_ref], integration_refs=[receipt_ref])
        for request in state["review_schedule"]["requests"]:
            if request["package_hash"] == expected_hash:
                request.update(status="returned", native_subagent_id=activation["native_subagent_id"])
                self.ledger.append_event("native_review_identity_reconciled", {"package_hash": expected_hash, "native_subagent_id": activation["native_subagent_id"], "evidence_ref": receipt_ref})
        self.ledger._write_state(state)
        if state["completion_state"].get("pending_review_hash") == expected_hash:
            state["completion_state"]["pending_review_hash"] = None
            self.ledger._write_state(state)
            self.ledger.append_event("findings_consumed", {"review_id": result["review_id"], "package_hash": expected_hash})
        return review


def record_disposition(ledger: Ledger, review_id: str, finding_index: int, disposition: str, evidence_refs: list[str]) -> dict:
    if disposition not in {"accepted", "partially_accepted", "rejected", "unresolved", "superseded"}:
        raise ValueError("invalid disposition")
    state = ledger.read()
    review = next((x for x in state["reviews"] if x["review_id"] == review_id), None)
    if review is None or not 0 <= finding_index < len(review["findings"]):
        raise ValueError("unknown finding")
    known_evidence = {item["evidence_id"] for item in state["evidence"]} | {item["evidence_ref"] for item in state["verification_chronology"]}
    if disposition != "unresolved" and not evidence_refs:
        raise ValueError("resolved disposition requires evidence")
    if any(ref not in known_evidence for ref in evidence_refs):
        raise ValueError("resolution evidence not found in ledger")
    review["findings"][finding_index]["disposition"] = disposition
    review["findings"][finding_index]["resolution_evidence"] = evidence_refs
    review["resolution_evidence"] = sorted({ref for finding in review["findings"] for ref in finding.get("resolution_evidence", [])})
    review["disposition"] = "RESOLVED" if all(f.get("disposition") in {"accepted", "partially_accepted", "rejected", "superseded"} and f.get("resolution_evidence") for f in review["findings"]) else "UNRESOLVED"
    ledger._write_state(state)
    ledger.append_event("finding_disposition", {"review_id": review_id, "finding_index": finding_index, "disposition": disposition, "evidence_refs": evidence_refs})
    return review
