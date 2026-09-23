# Change Execution and Verification

Use this reference for concrete implementation and verification decisions. The main skill establishes the governing design and change boundary.

## Trace the execution boundary

Inspect the owning implementation and follow the dependency paths that can invalidate the design. Establish the actual entry point and its controlling configuration. Identify every affected consumer and the persistent state it relies on. Trace generated artifacts to their authoritative sources.

Include the actual build and deployment paths when they affect the changed behavior. Identify the tests and current documents that describe its contract. This investigation does not require changing every layer on every task.

## Implement the accepted design

Change the owner and all required consumers together. Regenerate affected artifacts through the established workflow. Remove rejected concepts from the operational system rather than retaining them under a new name or in a dormant execution path.

Rework affected tests around the accepted contract. Reconstruct current documentation from the resulting model. Preserve useful decision history only in a clearly historical record. The final system must be understandable without knowing the discarded approach.

Preserve real state through the transition established by the [compatibility evidence gate](compatibility-boundaries.md). Reconstruction does not authorize discarding data or user work.

## Select meaningful verification

Choose checks according to the affected contract and failure risk. Prefer observable behavior and architectural invariants. Exercise state transitions and integration failures that could invalidate the result.

Question tests tied to private implementation structure. Establish whether the contract changed before revising an assertion. New code alone does not justify a new test or duplicated coverage at another layer.

Use existing mechanical checks when they cover an invariant. When the task authorizes a reliable check for a recurring invariant, place it at the repository owner.

## Resolve failures without changing the goal

A failing gate requires diagnosis. Determine whether the defect belongs to the implementation or its verification conditions. Correct the evidenced cause while preserving the intended contract.

Do not conceal failure or weaken the meaning of a gate. A change to test execution needs evidence that it repairs the verification conditions rather than hides a product defect.

When equivalent runs on the same state disagree, investigate nondeterminism and shared state. When the repository changed after a green result, investigate regression before calling the failure flaky. Repetition warrants checking for a common cause.

## Keep evidence valid

Verification applies only to the repository state and execution conditions checked. Track each required gate's scope and state with its result. Mark evidence stale when a later change can affect it.

Run required gates after the final relevant change. Classify impact before repeating expensive checks, but never use stale success to claim completion.

Review the whole affected system against the governing model. Confirm that every required consumer implements the accepted contract and that current documentation matches verified behavior. Any retained workaround must still have a real external cause. Report unresolved facts and remaining limitations.
