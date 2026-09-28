"""Canonical task state, provenance, and append-only runtime events."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def review_context_hash(state: dict) -> str:
    """Fingerprint the task semantics a reviewer must see for a candidate."""
    return digest({
        "original_request": state["original_request"],
        "confirmed_requirements": [item for item in state["obligations"] if item["status"] != "REJECTED"],
        "decision_history": state["decisions"],
        "authority": state["authority"],
        "epistemic": state["epistemic"],
        "work_items": state["work_items"],
        "delegated_work": state["delegated_work"],
        "integration_state": state["integration_state"],
        "blockers": state["blockers"],
        "artifacts": state["artifacts"],
        "completion_requirements": {key: state["completion_state"][key] for key in ("required_verification_scopes", "required_consumer_scopes", "semantic_review_required")},
    })


def initial_state(task_id: str, objective: str, original_request: str) -> dict:
    if not all((task_id, objective, original_request)):
        raise ValueError("task id, objective and original request are required")
    return {
        "schema_version": 1, "task_id": task_id, "objective": objective,
        "original_request": original_request, "obligations": [], "blockers": [],
        "work_items": [], "delegated_work": [],
        "integration_state": {"candidate_changes": [], "integrated_changes": [], "conflicts": [], "unresolved_dependencies": [], "verification_refs": [], "consumer_refs": [], "artifact_refs": []},
        "completion_state": {"status": "CONTINUE", "candidate_revision": None, "pending_review_hash": None, "required_verification_scopes": [], "required_consumer_scopes": [], "semantic_review_required": False, "evidence_refs": []},
        "decisions": [], "epistemic": [],
        "authority": {"policy_model": "unspecified", "default_admissibility": None, "closure": None, "capabilities": [], "constraints": [], "exceptions": [], "scope": "task", "side_effect_scope": [], "delegation_scope": []},
        "evidence": [], "reviews": [], "verification_chronology": [], "artifacts": [],
    }


class Ledger:
    """One snapshot and an append-only JSONL audit trail. State is harness-owned."""

    def __init__(self, directory: str | Path):
        self.directory = Path(directory)
        self.state_path = self.directory / "state.json"
        self.events_path = self.directory / "events.jsonl"

    def create(self, task_id: str, objective: str, original_request: str) -> dict:
        self.directory.mkdir(parents=True, exist_ok=True)
        if self.state_path.exists() or self.events_path.exists():
            raise FileExistsError("ledger already exists")
        state = initial_state(task_id, objective, original_request)
        self._write_state(state)
        self.append_event("request_ingested", {"task_id": task_id, "request_hash": digest(original_request)})
        return state

    def read(self) -> dict:
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def events(self) -> list[dict]:
        if not self.events_path.exists():
            return []
        return [json.loads(line) for line in self.events_path.read_text(encoding="utf-8").splitlines() if line]

    def append_event(self, kind: str, data: dict) -> dict:
        event = {"sequence": len(self.events()) + 1, "kind": kind, "data": data}
        with self.events_path.open("ab") as stream:
            stream.write(canonical_bytes(event))
        return event

    def _write_state(self, state: dict) -> None:
        temporary = self.state_path.with_suffix(".tmp")
        temporary.write_bytes(canonical_bytes(state))
        temporary.replace(self.state_path)

    def update(self, section: str, record: dict, *, event_kind: str | None = None) -> dict:
        allowed = {"obligations", "blockers", "work_items", "delegated_work", "decisions", "epistemic", "evidence", "reviews", "verification_chronology", "artifacts"}
        if section not in allowed:
            raise ValueError(f"unsupported section: {section}")
        state = self.read()
        _validate_record(section, record, state)
        identity_key = {"obligations": "id", "blockers": "id", "work_items": "work_item_id", "delegated_work": "id", "decisions": "id", "epistemic": "id", "evidence": "evidence_id", "reviews": "review_id", "artifacts": "artifact_id"}.get(section)
        if identity_key and any(item[identity_key] == record[identity_key] for item in state[section]):
            raise ValueError(f"duplicate {section} identity")
        state[section].append(record)
        if section == "decisions":
            for prior in state["decisions"][:-1]:
                if prior["id"] in record["supersedes"]:
                    prior["superseded_by"].append(record["id"])
                    prior["status"] = "SUPERSEDED"
        self._write_state(state)
        self.append_event(event_kind or f"{section}_updated", {"record": record, "state_hash": digest(state)})
        return state

    def transition(self, section: str, record_id: str, changes: dict, evidence_refs: list[str]) -> dict:
        identity_key = {"obligations": "id", "blockers": "id", "work_items": "work_item_id", "delegated_work": "id"}.get(section)
        if not identity_key:
            raise ValueError("section does not support transitions")
        if not evidence_refs:
            raise ValueError("transition requires evidence")
        state = self.read()
        record = next((item for item in state[section] if item[identity_key] == record_id), None)
        if record is None:
            raise ValueError("unknown record")
        forbidden = {identity_key, "parent_id", "objective", "owner"}
        if forbidden & changes.keys() or not changes.keys() <= record.keys():
            raise ValueError("invalid transition fields")
        before = {key: record[key] for key in changes}
        record.update(changes)
        self._write_state(state)
        self.append_event(f"{section}_transition", {"id": record_id, "before": before, "after": changes, "evidence_refs": evidence_refs})
        return state

    def replace(self, section: str, value: dict, *, event_kind: str | None = None) -> dict:
        if section not in {"integration_state", "completion_state", "authority"}:
            raise ValueError(f"unsupported replacement: {section}")
        state = self.read()
        if section == "authority":
            validate_authority(value)
        if section == "completion_state":
            previous = state["completion_state"]
            if previous["semantic_review_required"] and not value.get("semantic_review_required"):
                raise ValueError("required semantic review cannot be cleared")
            if previous["pending_review_hash"] != value.get("pending_review_hash"):
                raise ValueError("pending review is adapter-owned")
            for key in ("required_verification_scopes", "required_consumer_scopes"):
                if not set(previous[key]) <= set(value.get(key, [])):
                    raise ValueError(f"{key} cannot be narrowed")
            if value.get("status") == "COMPLETE":
                raise ValueError("only the completion evaluator can record COMPLETE")
        state[section] = value
        self._write_state(state)
        self.append_event(event_kind or f"{section}_updated", {"value": value, "state_hash": digest(state)})
        return state


def validate_authority(authority: dict) -> None:
    policy = authority.get("policy_model")
    if policy not in {"unspecified", "allowlist", "denylist", "capability_set", "mixed", "schema_constrained", "state_machine_constrained"}:
        raise ValueError("invalid policy model")
    if policy == "unspecified":
        if authority.get("default_admissibility") is not None or authority.get("closure") is not None:
            raise ValueError("unspecified policy cannot imply admissibility or closure")
        if any(authority.get(key) for key in ("capabilities", "constraints", "exceptions", "side_effect_scope", "delegation_scope")):
            raise ValueError("unspecified policy cannot contain policy rules")
    elif authority.get("default_admissibility") not in {"allow", "deny"}:
        raise ValueError("default admissibility required")
    if policy != "unspecified" and authority.get("closure") not in {"open", "closed"}:
        raise ValueError("closure required")
    if policy in {"allowlist", "capability_set"} and authority["default_admissibility"] != "deny":
        raise ValueError("closed capability policies deny unspecified actions")
    if policy in {"allowlist", "capability_set"} and authority["closure"] != "closed":
        raise ValueError("capability policies must remain closed")
    if policy == "denylist" and authority["default_admissibility"] != "allow":
        raise ValueError("open denylist allows unspecified actions")
    if policy == "denylist" and authority["closure"] != "open":
        raise ValueError("denylist policy must remain open")
    for key in ("capabilities", "constraints", "exceptions", "side_effect_scope", "delegation_scope"):
        if not isinstance(authority.get(key), list):
            raise ValueError(f"{key} must be a list")


def _validate_record(section: str, record: dict, state: dict) -> None:
    required = {
        "obligations": ("id", "description", "status"),
        "blockers": ("id", "reason", "external", "required_input"),
        "work_items": ("work_item_id", "parent_id", "objective", "owner", "status", "dependencies", "produced_changes", "verification_refs", "evidence_refs", "remaining_issues", "integration_notes"),
        "delegated_work": ("id", "work_item_id", "owner", "expected_result", "return_destination", "status", "result_refs", "consumed_refs", "integration_refs"),
        "decisions": ("id", "decision", "status", "scope", "evidence_refs", "supersedes", "superseded_by"),
        "epistemic": ("id", "proposition", "classification", "evidence_refs", "scope"),
        "evidence": ("evidence_id", "producer", "operation", "observable_result", "scope", "chronology_index", "artifact_refs"),
        "reviews": ("review_id", "evidence_package_hash", "reviewer_adapter", "findings", "disposition", "resolution_evidence"),
        "verification_chronology": ("chronology_index", "action", "command_or_tool", "scope", "observable_result", "evidence_ref", "status"),
        "artifacts": ("artifact_id", "semantic_role", "semantic_owner", "expected_lifetime", "current_state_role"),
    }[section]
    missing = [key for key in required if key not in record]
    if missing:
        raise ValueError(f"{section}: missing {missing}")
    if section == "epistemic":
        if record["classification"] not in {"FACT", "INFERENCE", "UNKNOWN", "USER_ASSERTION"}:
            raise ValueError("invalid epistemic class")
        if record["classification"] in {"FACT", "INFERENCE"} and not record["evidence_refs"]:
            raise ValueError("fact or inference requires evidence")
    if section == "decisions":
        known = {item["id"] for item in state["decisions"]}
        if any(ref not in known for ref in record["supersedes"]):
            raise ValueError("superseded decision is unknown")
    if section == "verification_chronology":
        previous = state["verification_chronology"]
        if record["chronology_index"] != len(previous) + 1:
            raise ValueError("verification chronology must be contiguous")
        if record["status"] not in {"PASS", "FAIL", "UNKNOWN"}:
            raise ValueError("invalid verification status")
    if section == "evidence":
        if record["chronology_index"] < 1:
            raise ValueError("invalid chronology index")
    if section == "blockers":
        for key in ("work_item_ids", "obligation_ids"):
            if key in record and (not isinstance(record[key], list) or not all(isinstance(item, str) for item in record[key])):
                raise ValueError(f"blocker {key} must be a list of IDs")
