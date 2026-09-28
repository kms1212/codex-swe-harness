"""Small local control surface. Native subagent invocation stays with Codex."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .completion import evaluate_and_record, progress_snapshot
from .core import Ledger
from .review import BuiltinSubagentAdapter, build_package, record_disposition, route_review


def main() -> None:
    parser = argparse.ArgumentParser(prog="harness-v0")
    parser.add_argument("ledger", type=Path)
    sub = parser.add_subparsers(dest="operation", required=True)
    create = sub.add_parser("create")
    create.add_argument("task_id")
    create.add_argument("objective")
    create.add_argument("original_request")
    add = sub.add_parser("add")
    add.add_argument("section")
    add.add_argument("record_file", type=Path)
    replace = sub.add_parser("replace")
    replace.add_argument("section")
    replace.add_argument("value_file", type=Path)
    prepare = sub.add_parser("prepare-review")
    prepare.add_argument("candidate_file", type=Path)
    prepare.add_argument("--type", action="append", required=True)
    prepare.add_argument("--semantic-risk", action="store_true", help="require review for semantic risk, including code-only changes")
    prepare.add_argument("--source", action="append", default=[])
    ingest = sub.add_parser("ingest-review")
    ingest.add_argument("package_file", type=Path)
    ingest.add_argument("result_file", type=Path)
    ingest.add_argument("activation_file", type=Path)
    disposition = sub.add_parser("disposition")
    disposition.add_argument("review_id")
    disposition.add_argument("finding_index", type=int)
    disposition.add_argument("value")
    disposition.add_argument("evidence_refs", nargs="*")
    sub.add_parser("complete")
    sub.add_parser("progress")
    args = parser.parse_args()
    ledger = Ledger(args.ledger)
    if args.operation == "create":
        result = ledger.create(args.task_id, args.objective, args.original_request)
    elif args.operation == "add":
        result = ledger.update(args.section, json.loads(args.record_file.read_text()))
    elif args.operation == "replace":
        result = ledger.replace(args.section, json.loads(args.value_file.read_text()))
    elif args.operation == "prepare-review":
        state = ledger.read()
        prior_required = state["completion_state"]["semantic_review_required"]
        prior_types = [kind for event in ledger.events() if event["kind"] == "review_routed" and event["data"]["required"] for kind in event["data"]["change_types"]]
        effective_types = sorted(set(args.type) | (set(prior_types) if prior_required else set()))
        routing = route_review(effective_types, semantic_risk=args.semantic_risk or prior_required)
        ledger.append_event("review_routed", routing)
        state["completion_state"]["semantic_review_required"] = routing["required"]
        ledger._write_state(state)
        package = build_package(state, routing, json.loads(args.candidate_file.read_text()), args.source)
        result = BuiltinSubagentAdapter(ledger).prepare(package)
    elif args.operation == "ingest-review":
        result = BuiltinSubagentAdapter(ledger).ingest(json.loads(args.package_file.read_text()), json.loads(args.result_file.read_text()), json.loads(args.activation_file.read_text()))
    elif args.operation == "disposition":
        result = record_disposition(ledger, args.review_id, args.finding_index, args.value, args.evidence_refs)
    elif args.operation == "complete":
        result = evaluate_and_record(ledger)
    else:
        result = progress_snapshot(ledger.read())
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
