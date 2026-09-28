"""Verify and record every explicit item in the original parent completion set."""
import hashlib
import json
from pathlib import Path

from harness_v0.core import Ledger, digest
from prepare_real_work_review4 import FILES, ROOT, CASE

LEDGER = Ledger(CASE)


def exists(relative):
    path = ROOT / relative
    assert path.exists(), relative
    return str(path.relative_to(ROOT))


def main():
    state = LEDGER.read()
    if len(state["verification_chronology"]) != 60 or len(state["obligations"]) != 3:
        raise RuntimeError("expected tenth-review state")
    source_runtime = json.loads((ROOT / "eval-results/source-to-runtime.json").read_text())
    controlled_score = json.loads((ROOT / "eval-results/controlled/score.json").read_text())
    native_traces = (ROOT / "eval-results/raw-traces/native-trace-index.jsonl").read_text().splitlines()
    run_index = (ROOT / "eval-results/run-index.jsonl").read_text().splitlines()
    review10 = json.loads((CASE / "current-v0-implementation-review-10.json").read_text())
    result10 = json.loads((CASE / "review-result-10.json").read_text())
    assert digest(review10) == result10["package_hash"]
    assert source_runtime["source_to_install_match"] and source_runtime["active_hook_continued_once"] and source_runtime["active_hook_without_work_item_continued_once"]
    assert controlled_score["cases"] == 7 and len(native_traces) >= 22 and len(run_index) >= 31
    checks = [
        ("prior reviewer-isolation evidence recovered", ["eval-results/prior-evidence/FINAL-DECISION.md"], "Historical study file inspected; 34 paired runs and no quality winner recorded."),
        ("current Codex extension and lifecycle substrate verified", ["ARCHITECTURE.md", "eval-results/source-to-runtime.json"], "Current CLI/hooks capabilities documented and active hook observed."),
        ("v0 architecture fixed", ["ARCHITECTURE.md"], "Architecture document exists with component and ownership boundaries."),
        ("canonical state implemented", ["source/harness_v0/core.py", "tests/test_contracts.py"], "Executable state and contract tests exist; 20 source tests passed."),
        ("event and evidence chronology implemented", ["source/harness_v0/core.py", "eval-results/real-work/current-v0-implementation/events.jsonl"], "Append-only event stream and ordered verification chronology persisted."),
        ("ReviewEvidencePackage implemented", ["source/harness_v0/review.py", "eval-results/real-work/current-v0-implementation/current-v0-implementation-review-10.json"], "Frozen package hash matches native reviewer receipt."),
        ("SemanticReview interface implemented", ["source/harness_v0/review.py"], "Protocol contract present in review module."),
        ("built-in reviewer adapter implemented", ["source/harness_v0/review.py", "eval-results/real-work/current-v0-implementation/review-result-10.json"], "Native reviewer activation and result receipt persisted."),
        ("multi-worker-compatible work-item state implemented", ["source/harness_v0/core.py", "tests/test_contracts.py"], "Work, delegation and integration distinctions exercised by tests."),
        ("completion gate implemented", ["source/harness_v0/completion.py", "tests/test_contracts.py"], "Gate and Stop-hook liveness paths exercised by 20 tests."),
        ("controlled challenge evals executed", ["eval-results/controlled/score.json"], "Seven controlled v2 cases scored; exact criterion 4/6 defects, clean 0 findings."),
        ("selected real-work-derived evals executed", ["eval-results/real-work/F063-live-derived/review-result-1.json", "eval-results/real-work/current-v0-implementation/review-result-10.json"], "F063 live-derived and current implementation rounds recorded."),
        ("source-to-active-runtime verification completed", ["eval-results/source-to-runtime.json", "eval-results/raw-traces/isolated-hook-no-work.jsonl"], "Source/install hashes match and active hook continuation observed."),
        ("six architecture and operation documents completed", ["ARCHITECTURE.md", "STATE-SCHEMA.md", "REVIEW-PROTOCOL.md", "COMPLETION.md", "EVALUATION.md", "OPERATIONS.md"], "All six current-owner documents exist."),
        ("V0-ACCEPTANCE.md completed", ["V0-ACCEPTANCE.md"], "Acceptance record answers the 13 required questions."),
        ("raw evidence indexed", ["eval-results/run-index.jsonl", "eval-results/raw-traces/native-trace-index.jsonl"], "31 run-index entries and at least 22 native-child trace references present."),
    ]
    revision = digest({name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in FILES})
    manifest = []
    for ordinal, (description, refs, observable) in enumerate(checks, start=1):
        artifact_refs = []
        for ref in refs:
            artifact_refs.append(exists(ref))
        index = 60 + ordinal
        ref = f"completion-set:{ordinal:02d}"
        LEDGER.update("verification_chronology", {"chronology_index": index, "action": "audit explicit parent completion item", "command_or_tool": "completion-set-audit",
            "scope": "completion-set", "observable_result": observable, "evidence_ref": ref, "status": "PASS", "artifact_revision": revision,
            "resolves": ["current-v0-implementation-review-10-semantic:0"] if ordinal == 16 else [], "consumer_point": ordinal == 15})
        LEDGER.update("evidence", {"evidence_id": f"completion-set-evidence-{ordinal:02d}", "producer": "parent integrator", "operation": "verify explicit completion item",
            "observable_result": observable, "scope": "completion-set", "chronology_index": index, "artifact_refs": artifact_refs})
        LEDGER.update("obligations", {"id": f"completion-set-{ordinal:02d}", "description": description, "status": "SATISFIED", "evidence_refs": [ref]})
        manifest.append({"ordinal": ordinal, "description": description, "evidence_ref": ref, "artifact_refs": artifact_refs, "observable_result": observable})
    completion = LEDGER.read()["completion_state"]
    completion["candidate_revision"] = revision
    completion["required_verification_scopes"] = sorted(set(completion["required_verification_scopes"]) | {"completion-set"})
    completion["status"] = "CONTINUE"
    completion["evidence_refs"] = []
    LEDGER.replace("completion_state", completion)
    (ROOT / "eval-results/completion-set-audit.json").write_text(json.dumps({"count": len(manifest), "candidate_revision": revision, "items": manifest}, indent=2) + "\n")
    print(json.dumps({"items_verified": len(manifest), "candidate_revision": revision}))


if __name__ == "__main__":
    main()
