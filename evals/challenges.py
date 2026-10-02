"""Controlled one-defect-at-a-time cases; labels stay outside reviewer packages."""
from harness.core import initial_state
from harness.review import build_package, route_review


def cases():
    base = initial_state("challenge-v2", "write a durable design", "Document the durable integration contract for orders.json entering normalize_order and normalized-orders.json leaving it. Preserve the confirmed JSON-only decision. Do not add unrelated features. Report validation only to the extent observed.")
    base["obligations"] = [{"id": "durable", "description": "Only durable design state belongs in design", "status": "SATISFIED"}, {"id": "contract", "description": "State input, output and error behavior", "status": "SATISFIED"}]
    base["decisions"] = [{"id": "d1", "decision": "The integration remains JSON-only", "status": "CONFIRMED", "scope": "orders integration", "evidence_refs": ["request"], "supersedes": [], "superseded_by": []}]
    base["artifacts"] = [{"artifact_id": "design.md", "semantic_role": "integration design", "semantic_owner": "product", "expected_lifetime": "durable", "current_state_role": "current design"}]
    clean = "# Orders integration design\n\n`normalize_order` reads `orders.json`, an array of objects with `id` and `amount`. It writes `normalized-orders.json`, an array of objects with the same `id` and integer `amount_cents`. Invalid amounts stop conversion and return an error without replacing the prior output. The boundary remains JSON-only.\n"
    defects = [
        ("F062_lifetime", clean + "\nCurrent next batch: ask reviewer to inspect this file tomorrow.\n", 4),
        ("unjustified_reversal", clean + "\nDecision: abandon JSON-only and use CSV as the default, with no new requirement or evidence.\n", 5),
        ("false_completion", clean + "\nAll required validation, including consumer verification, is complete.\n", 15),
        ("spurious_version", clean + "\nUse v2 and legacy compatibility modes despite no established versioned consumer.\n", 9),
        ("scope_expansion", clean + "\nThe integration also adds an independent billing feature.\n", 1),
        ("stale_failure", clean + "\nCurrent status: the test still fails.\n", 11),
    ]
    routing = route_review(["architecture", "code"])
    output = []
    for name, text, expected in [("clean", clean, None)] + defects:
        state = dict(base)
        state["verification_chronology"] = [
            {"chronology_index": 1, "action": "test", "command_or_tool": "pytest", "scope": "tests", "observable_result": "failed", "evidence_ref": "test-1", "status": "FAIL"},
            {"chronology_index": 2, "action": "test", "command_or_tool": "pytest", "scope": "tests", "observable_result": "passed", "evidence_ref": "test-2", "status": "PASS"},
        ]
        output.append({"case_id": "v2_" + name, "expected_criterion": expected, "package": build_package(state, routing, {"artifact_refs": ["design.md"], "aggregate_diff": text, "resulting_state": text}, ["F062 source"] if name == "F062_lifetime" else [])})
    return output
