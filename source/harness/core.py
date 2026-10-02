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
        "request_state": {k: v for k, v in state.get("request_state", {}).items() if k != "interpreted_through"},
        "confirmed_requirements": [{k: v for k, v in item.items() if k not in {"status", "evidence_refs"}} for item in state["obligations"] if item["status"] not in {"REJECTED", "SUPERSEDED"}],
        "decision_history": state["decisions"],
        "authority": state["authority"],
        "epistemic": state["epistemic"],
        "work_items": [{k:v for k,v in item.items() if k not in {"status", "evidence_refs", "verification_refs"}} for item in state["work_items"] if item.get("semantic_role") not in {"reviewer", "unclassified"}],
        "delegated_work": [{k:v for k,v in item.items() if k not in {"status", "result_refs", "consumed_refs", "integration_refs"}} for item in state["delegated_work"] if item.get("semantic_role") not in {"reviewer", "unclassified"}],
        "integration_state": {k:v for k,v in state["integration_state"].items() if k not in {"verification_refs", "consumer_refs"}},
        "blockers": state["blockers"],
        "artifacts": state["artifacts"],
        "instruction_changes": [{k:v for k,v in item.items() if k not in {"active_check_ref", "installed_revision", "candidate_revision", "whole_file_review_ref"}} for item in state.get("instruction_changes", [])],
        "completion_requirements": {key: state["completion_state"].get(key) for key in ("required_verification_scopes", "required_consumer_scopes", "semantic_review_required", "scope_identities", "scope_environments", "scope_input_identities", "instruction_recomposition_required", "instruction_recomposition_targets", "instruction_installation_required")},
    })


def initial_state(task_id: str, objective: str, original_request: str) -> dict:
    if not all((task_id, objective, original_request)):
        raise ValueError("task id, objective and original request are required")
    return {
        "schema_version": 1, "task_id": task_id, "objective": objective,
        "original_request": original_request,
        "request_history": [{"revision": 1, "turn_id": None, "content": original_request}],
        "request_state": {"interpreted_through": 1, "semantic_revision": 1, "summary": original_request, "scope": original_request, "priorities": []},
        "review_schedule": {"assessment": None, "requests": []}, "resources": [], "verification_plans": [], "executions": {},
        "lifecycle": {"status": "active"}, "commit_scope": None,
        "obligations": [], "blockers": [],
        "work_items": [], "delegated_work": [],
        "integration_state": {"candidate_changes": [], "integrated_changes": [], "conflicts": [], "unresolved_dependencies": [], "verification_refs": [], "consumer_refs": [], "artifact_refs": []},
        "completion_state": {"status": "CONTINUE", "candidate_revision": None, "pending_review_hash": None, "required_verification_scopes": [], "required_consumer_scopes": [], "scope_identities": {}, "scope_environments": {}, "scope_input_identities": {}, "semantic_review_required": False, "instruction_recomposition_required": [], "instruction_recomposition_targets": {}, "instruction_installation_required": [], "instruction_source_revision": None, "evidence_refs": []},
        "decisions": [], "epistemic": [],
        "authority": {"policy_model": "unspecified", "default_admissibility": None, "closure": None, "capabilities": [], "constraints": [], "exceptions": [], "scope": "task", "side_effect_scope": [], "delegation_scope": []},
        "evidence": [], "reviews": [], "verification_chronology": [], "artifacts": [], "instruction_changes": [],
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
        allowed = {"obligations", "blockers", "work_items", "delegated_work", "decisions", "epistemic", "evidence", "reviews", "verification_chronology", "artifacts", "instruction_changes", "verification_plans"}
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
        if section not in {"integration_state", "completion_state", "authority", "commit_scope"}:
            raise ValueError(f"unsupported replacement: {section}")
        state = self.read()
        if section == "authority":
            validate_authority(value)
        if section == "commit_scope":
            if not all(value.get(k) for k in ("candidate_revision", "scope", "message")) or not isinstance(value.get("remaining_required_work"), list):
                raise ValueError("commit scope must identify content, semantic scope, message and remaining required work")
        if section == "completion_state":
            previous = state["completion_state"]
            if previous["pending_review_hash"] != value.get("pending_review_hash"):
                raise ValueError("pending review is adapter-owned")
            if previous["pending_review_hash"] and not value.get("semantic_review_required"):
                raise ValueError("pending semantic review cannot be cleared")
            for key in ("required_verification_scopes", "required_consumer_scopes"):
                if not set(previous[key]) <= set(value.get(key, [])):
                    raise ValueError(f"{key} cannot be narrowed")
            if not set(previous.get("instruction_recomposition_required", [])) <= set(value.get("instruction_recomposition_required", [])):
                raise ValueError("instruction recomposition requirements cannot be narrowed")
            global_installation = {path for path in previous.get("instruction_installation_required", []) if path.startswith("runtime/instructions/")}
            if not global_installation <= set(value.get("instruction_installation_required", [])):
                raise ValueError("global instruction installation requirements cannot be narrowed")
            targets = value.get("instruction_recomposition_targets", {})
            if not isinstance(targets, dict) or not all(isinstance(k, str) and isinstance(v, str) and v for k, v in targets.items()):
                raise ValueError("instruction recomposition targets must map paths to identities")
            for key in ("scope_identities", "scope_environments"):
                if not isinstance(value.get(key, {}), dict) or not all(isinstance(k, str) and isinstance(v, str) and v for k, v in value.get(key, {}).items()):
                    raise ValueError(f"{key} must map scopes to nonempty strings")
            inputs = value.get("scope_input_identities", {})
            if not isinstance(inputs, dict) or not all(isinstance(scope, str) and isinstance(identities, dict) and all(isinstance(k, str) and isinstance(v, str) and v for k, v in identities.items()) for scope, identities in inputs.items()):
                raise ValueError("scope input identities must map scopes to input identity maps")
            if value.get("status") == "COMPLETE":
                raise ValueError("only the completion evaluator can record COMPLETE")
        state[section] = value
        self._write_state(state)
        self.append_event(event_kind or f"{section}_updated", {"value": value, "state_hash": digest(state)})
        return state


    def receive_request(self, content: str, turn_id: str | None = None) -> dict:
        state = self.read()
        if turn_id and any(x.get("turn_id") == turn_id for x in state["request_history"]):
            return state
        revision = len(state["request_history"]) + 1
        state["request_history"].append({"revision": revision, "turn_id": turn_id, "content": content})
        state["completion_state"]["status"] = "CONTINUE"
        self._write_state(state)
        self.append_event("request_received", {"revision": revision, "turn_id": turn_id, "content": content})
        return state

    def confirm_request(self, interpretation: dict) -> dict:
        state = self.read()
        revision = len(state["request_history"])
        if interpretation.get("through_revision") != revision:
            raise ValueError("interpretation must cover the latest request revision")
        if interpretation.get("change") not in {"none", "add", "remove", "modify", "priority", "cancel"}:
            raise ValueError("request change classification required")
        for key in ("summary", "scope", "reason"):
            if not isinstance(interpretation.get(key), str) or not interpretation[key].strip():
                raise ValueError(f"request {key} required")
        if not isinstance(interpretation.get("priorities"), list):
            raise ValueError("priorities must be explicit and separate from scope")
        previous = state["request_state"]
        semantic = {key: interpretation[key] for key in ("summary", "scope", "priorities")}
        changed = any(previous.get(k) != v for k, v in semantic.items())
        if interpretation["change"] == "none" and changed:
            raise ValueError("no semantic change must preserve confirmed state")
        # A material correction reopens commitments; the integrator can re-satisfy unaffected ones with valid evidence.
        if interpretation["change"] != "none":
            for obligation in state["obligations"]:
                if obligation["status"] == "SATISFIED":
                    obligation["status"] = "IN_PROGRESS"
        if interpretation["change"] == "none" and interpretation.get("obligations"):
            current = {x["id"]: x for x in state["obligations"]}
            for item in interpretation["obligations"]:
                prior = current.get(item.get("id"))
                if not prior or any(item.get(k) != prior.get(k) for k in set(item) - {"status", "evidence_refs"}):
                    raise ValueError("no-change acknowledgment cannot alter requirements")
        for obligation in interpretation.get("obligations", []):
            _validate_record("obligations", obligation, state)
        if "obligations" in interpretation:
            old = {x["id"]: x for x in state["obligations"]}
            for item in interpretation["obligations"]:
                old[item["id"]] = item
            state["obligations"] = list(old.values())
        state["request_state"] = dict(semantic, interpreted_through=revision,
            semantic_revision=previous["semantic_revision"] + (interpretation["change"] != "none"))
        state["request_history"][-1]["interpretation"] = interpretation
        if interpretation["change"] == "cancel":
            state["lifecycle"]["status"] = "cancelled"
        self._write_state(state)
        self.append_event("request_confirmed", {"interpretation": interpretation, "state_hash": digest(state)})
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
        "verification_plans": ("command_or_tool", "scope", "target_identity", "input_identities", "execution_environment"),
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
        "instruction_changes": ("artifact", "target_identity", "candidate_revision", "requirement", "owner", "outcome", "existing_principle", "integration", "displaced_guidance", "whole_file_review_ref", "active_check_ref"),
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
        if "related_inputs" in record and (not isinstance(record["related_inputs"], list) or not all(isinstance(x, str) for x in record["related_inputs"])):
            raise ValueError("related_inputs must be a list of paths or contracts")
        for key in ("target_identity", "execution_environment"):
            if key in record and (not isinstance(record[key], str) or not record[key]):
                raise ValueError(f"{key} must be a nonempty string")
        if "input_identities" in record and (not isinstance(record["input_identities"], dict) or not all(isinstance(k, str) and isinstance(v, str) and v for k, v in record["input_identities"].items())):
            raise ValueError("input identities must map inputs to nonempty identities")
    if section == "evidence":
        if record["chronology_index"] < 1:
            raise ValueError("invalid chronology index")
    if section == "blockers":
        for key in ("work_item_ids", "obligation_ids"):
            if key in record and (not isinstance(record[key], list) or not all(isinstance(item, str) for item in record[key])):
                raise ValueError(f"blocker {key} must be a list of IDs")
    if section == "instruction_changes":
        from .instructions import OUTCOMES
        if record["outcome"] not in OUTCOMES:
            raise ValueError("invalid instruction recomposition outcome")
        for key in ("artifact", "target_identity", "candidate_revision", "requirement", "owner", "integration", "whole_file_review_ref", "active_check_ref"):
            if not isinstance(record[key], str) or not record[key].strip():
                raise ValueError(f"instruction {key} must be nonempty")
        if record["outcome"] != "new_owner" and not record["existing_principle"]:
            raise ValueError("existing principle must be identified")
        if not isinstance(record["displaced_guidance"], list) or not all(isinstance(x, str) for x in record["displaced_guidance"]):
            raise ValueError("displaced guidance must be a list")
