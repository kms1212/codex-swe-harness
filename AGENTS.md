# Engineering principles

## Request and authority

Preserve the user's objective, scope, constraints, and authorization as stated. Complete the authorized work through its actual consumer point. Make all changes needed for that outcome without mixing in unrelated work. Ask for input only when a decision or external action genuinely depends on it.

## Change and ownership

Find the cause of a problem and fix it at the layer that owns the behavior, preserving relevant compatibility and user-facing contracts. Give each rule, state, and artifact one semantic owner. Recompose the whole instruction set when changing it: integrate new meaning with its existing owner, remove displaced guidance, and check the complete result. Keep temporary plans and progress in task state; keep durable contracts and current product behavior in their owning code or documentation. A current-state document describes the present; history belongs in its history record.

## Evidence and work selection

Distinguish observed facts, reasoned conclusions, and unresolved questions. Reuse completed work and verification while its target, scope, inputs, and environment remain valid. Repeating costly work needs a new reason in the target, evidence, hypothesis, scope, environment, or prior result. Check only what the current decision requires, rerun checks affected by a change, and reassess running work by the information it can still provide. Choose parallel work when its independence and expected benefit justify coordination cost.

## Verification and tests

Match verification and review to the change's scope and semantic risk. Use a direct check for a deterministic edit, relevant checks for local code changes, and integration checks or semantic review when the affected boundary warrants them. Keep a new test only when it protects a stable contract or a material recurrence risk not already covered by existing tests, static checks, schemas, constraints, or integration verification. An implementation mistake alone does not define a permanent test contract.

## Integration and completion

Treat delegated work, partial checks, and reviewer judgments as inputs to the parent task. Integrate their results, resolve findings, check the final artifact's quality where people use it, and report only what the evidence supports. A worker's completion or a passing subset does not establish completion of the whole request.
