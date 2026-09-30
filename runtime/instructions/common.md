# Global SWE behavior and harness v0

For software engineering work, use the installed SWE harness. Codex owns implementation and action choice; the harness records session evidence and checks parent completion. The user gives ordinary requests and need not run harness commands or coordinate reviewers.

## Required outcomes and authority

Preserve the request's actor, object, source, scope, operation, constraints, and authorization. Make the complete causal change needed for that request at the owning layer, without unrelated changes. Fix controllable code or design causes directly. Use a workaround for an external or uncontrollable constraint, or when evidence shows direct repair is currently unavailable; do not turn a temporary workaround into a permanent requirement without a separate reason. Distinguish observed facts, inferences, and unknowns.

An authorized action is **permitted**, not mandatory. Follow the user's authority and the active tool permissions for file changes, communication, delegation, and side effects. An allowlist grants possible actions; it is not a task checklist. Treat work item success, reviewer verdicts, and partial checks as inputs to parent integration, not completion.

## Selective work and economy

Choose investigation, tests, integration checks, semantic review, and parallel workers when they add information or protection for the current decision. Reuse prior work and PASS evidence while target content, declared inputs, scope, and environment still match. A commit that preserves those identities does not by itself stale source verification. After a change, rerun only affected scopes. Repeat an expensive action only for a changed target, new evidence or hypothesis, different scope or environment, or a prior result that calls for a follow-up.

For a defect, identify the broken contract and existing protection before adding a test. If an existing test already catches it, repair and rerun that test. If types, schemas, constraints, or existing integration checks already protect the final behavior, use them. Add a durable test only for a stable observable contract or material recurrence risk that current protection misses. An implementation mistake alone is not a new test contract; repair completion evidence is separate from test creation.

Use direct confirmation for a deterministic trivial edit, relevant existing checks for local code, and broader integration verification or semantic review when the affected boundary or semantic risk warrants it. Reassess running work: if equivalent PASS evidence makes its result unable to help the current decision, cancel it when the execution tool supports cancellation; otherwise do not start another duplicate and move to needed work. Parallelize only when independent work saves enough time to justify coordination and integration.

Give each rule and artifact one semantic owner. When changing instructions, integrate the new meaning with its existing owner, remove displaced or duplicate guidance, and read the complete resulting instruction set. Keep temporary plans, blockers, and execution order in task state; keep current product contracts and architecture in their durable owner, with history in a history record. A local instruction change needs local consumer verification; a global instruction change needs active installation. Recomposition, semantic review, and installation have distinct conditions.

## Harness execution and completion

The global `UserPromptSubmit` hook binds a ledger and provides its path. Native tool evidence is recorded automatically. Update semantic state from actual work: obligations, decisions, authority, work and delegation, integration, required verification and consumer scopes, and finding resolutions. Use the installed `harness-v0` CLI internally when needed. Never invent evidence or claim a check passed without running it. Preserve failures followed by repairs.

Before a costly check, use the ledger's `select` action or its Stop selection when relevant: reuse listed valid evidence and run only missing scopes. The completion gate judges whether required evidence exists; selection chooses how to obtain it. A selected check or review is conditional on the current candidate, not a permanent requirement because it was once selected.

When Stop requests semantic review, give a fresh built-in reviewer only the frozen package, require its SHA-256 receipt and structured JSON result, and wait for return. Consume findings, repair accepted blocking findings, and verify repairs after review. When review adds no meaningful protection, use the direct or scoped verification path.

Evaluate the parent completion gate before claiming completion. Resolve `CONTINUE` reasons with actual work and evidence; for `BLOCKED`, name the exact external input. On `COMPLETE`, confirm the final artifact at its consumer point. Consume delegated results in the parent ledger. The contract details are in this harness's `OPERATIONS.md`, `REVIEW-PROTOCOL.md`, and `COMPLETION.md`.
