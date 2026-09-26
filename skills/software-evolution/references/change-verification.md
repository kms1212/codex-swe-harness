# Change Execution and Verification

Use this reference for concrete implementation and verification decisions. The main skill establishes the governing design and change boundary.

## Trace the execution boundary

Inspect the owning implementation and follow the dependency paths that can invalidate the design. Establish the actual entry point and its controlling configuration. Identify every affected consumer and the persistent state it relies on. Trace generated artifacts to their authoritative sources.

Include the actual build and deployment paths when they affect the changed behavior. Identify the tests and current documents that describe its contract. This investigation does not require changing every layer on every task.

When a change expands an existing pattern, inspect source-of-truth and dependency direction where relevant. Differences between a clean or standalone path and a path that succeeds only with existing generated, cached, or tracked state can reveal a hidden dependency.

Inspection and verification may extend beyond the implementation boundary to detect regressions and contract effects. Tracing a path or observing a pre-existing defect does not authorize modifying every inspected component.

## Implement the accepted design

Change the owner and all required consumers together. Regenerate affected artifacts through the established workflow. Remove rejected concepts from the operational system rather than retaining them under a new name or in a dormant execution path.

Rework affected tests around the accepted contract. Reconstruct current documentation from the resulting model. Preserve useful decision history only in a clearly historical record. The final system must be understandable without knowing the discarded approach.

Preserve real state through the transition established by the [compatibility evidence gate](compatibility-boundaries.md). Reconstruction does not authorize discarding data or user work.

## Select meaningful verification

Choose checks according to the affected contract and failure risk. Prefer observable behavior and architectural invariants. Exercise state transitions and integration failures that could invalidate the result.

A verification action is admissible when it distinguishes a live hypothesis, exercises evidence invalidated by the change, or provides required final acceptance evidence. Repeating an expensive path additionally requires a relevant state change, new evidence, a distinct hypothesis, or the final acceptance obligation.

Use diagnostic verification to isolate the cause with the smallest discriminating check. Use affected verification to exercise the changed contract and the paths whose evidence was invalidated. Use acceptance verification to establish the complete final outcome. A full end-to-end or release path can be required acceptance evidence without being the default diagnostic tool after every local edit.

Question tests tied to private implementation structure. Establish whether the contract changed before revising an assertion. New code alone does not justify a new test or duplicated coverage at another layer.

Use existing mechanical checks when they cover an invariant. When the task authorizes a reliable check for a recurring invariant, place it at the repository owner.

## Resolve failures without changing the goal

A failing gate requires diagnosis. Determine whether the failure was caused by the authorized change, exposes a correctness dependency of the confirmed result, reflects an induced contract update, or is a pre-existing adjacent defect. Correct the first three within the current causal closure. Preserve and report evidence of the last without repairing it merely to make a broader gate green or enlarging the current task.

Prefer a minimal reproduction or affected suffix when it can resolve the current uncertainty. Reuse a validated prefix when its prerequisites and contract remain independent of the failure and subsequent change.

Repeated same-class failure or modification-and-reversal churn is evidence that the hypothesis, shared contract, state ownership, change boundary, fixture, or test strategy may be wrong. Review that strategy before accumulating another local patch. Do not change direction merely because work is lengthy; base the review on the observed failure and evidence history.

Growing edit fanout, generated churn, repeated same-policy changes, widening package impact, and verification scope that grows with pattern instances can indicate loss of change locality. When these signals accompany pattern extension or promotion, apply the [architecture drift reassessment](architecture-drift.md) before adding more instances. These signals motivate investigation; they do not prove the architecture is wrong.

Do not conceal failure or weaken the meaning of a gate. A change to test execution needs evidence that it repairs the verification conditions rather than hides a product defect.

When equivalent runs on the same state disagree, investigate nondeterminism and shared state. When the repository changed after a green result, investigate regression before calling the failure flaky. Repetition warrants checking for a common cause.

## Keep evidence valid

A failure or later edit invalidates only evidence that depends on the failed or changed state. Track validated checkpoints, their relevant prerequisites, and the evidence invalidated by each change. Do not discard an independent successful prefix merely because a later stage failed.

Run diagnostic and affected checks as needed while repairing the result. Run every required acceptance gate after the final relevant change, including a full path when the final contract requires it. Completion relies only on evidence valid for the final state; independent validated evidence remains reusable while its supporting state stays unchanged.

Use these cases to calibrate verification reuse:

- If a fix changes an initialization contract on which the whole path depends, earlier prefix evidence is invalid and a full rerun is justified.
- If a late-stage handler changes while the validated prefix remains independent, verify the minimal reproduction and affected suffix before repeating the full path.
- After diagnostic and affected failures are resolved, rerun the required full acceptance path against the final state.

Review the whole affected system against the governing model. Confirm that every required consumer implements the accepted contract and that current documentation matches verified behavior. Any retained workaround must still have a real external cause. Report unresolved facts and remaining limitations.
