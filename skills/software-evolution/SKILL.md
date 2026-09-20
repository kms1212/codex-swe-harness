---
name: software-evolution
description: Design, implement, refactor, fix, review, or verify software and establish evidence-based repository engineering guidance as stages in long-term codebase evolution. Use when ownership, architecture, contracts, tests, compatibility, migrations, workarounds, repository harnesses, or future change locality matter; apply proportionally so trivial local changes remain lightweight.
---

# Software Evolution

Treat each software task as one step in an evolving codebase. Optimize for coherent ownership and small future change surfaces, not for the smallest current patch.

This skill owns cross-domain change-boundary decisions. Repository instructions provide local facts and commands. Relevant specialized skills provide domain-specific evidence, constraints, semantics, and techniques that must inform those decisions before they are finalized; they do not replace this skill's ownership.

## Scale the procedure

Use a brief internal pass for a local, unambiguous change whose owner, contract, and verification are already clear.

Form the complete change model before implementation when any of these applies:

- the change crosses layers or components;
- it introduces a feature, data-model change, or abstraction;
- the bug pattern is repeated or the apparent fix is symptom-specific;
- a workaround, compatibility path, version, or migration is being considered;
- one policy is duplicated across multiple locations;
- an active or confirmed roadmap item affects the same responsibility;
- the proposed structure is likely to be changed again soon;
- tests would need substantial updates because implementation structure changes.

Do not turn the model into mandatory long user-facing prose. Make the decisions explicit enough to guide the work and report material tradeoffs.

## Repository guidance may be absent

Do not assume the repository already has an `AGENTS.md`, architecture checks, or documented verification procedure.

Absence alone does not justify creating them. Continue the current task from inspected repository evidence when durable guidance is unnecessary.

Read [repository harness](references/repository-harness.md) when:

- the user asks to establish or improve repository engineering guidance;
- a repository lacks durable guidance for commands, architecture, ownership, or verification that will recur across tasks;
- a mechanically decidable invariant is repeatedly enforced only through model judgment;
- existing repository guidance must be split, normalized, or moved closer to the code it governs.

Never create or modify an `AGENTS.md` without the proposal and approval required by global governance.

## 1. Frame the request

Separate:

- **Change:** behavior or contract that must change.
- **Preserve:** confirmed behavior, data, interfaces, or constraints that must remain.
- **Exclude:** adjacent improvements and speculative features outside the request.
- **Verification:** evidence required to establish completion.

Later user instructions override earlier assumptions. A structural change required to remove the task's root cause is necessary scope, not unrelated scope expansion.

## 2. Inspect the owning system

Inspect only the relevant breadth, including as applicable:

- applicable root and nested instructions, or confirmed absence of them;
- definitions and call sites;
- operational entry points and runtime paths;
- data ownership and transaction boundaries;
- generated artifacts and their sources;
- stable public or internal contracts;
- existing tests and the risks they protect;
- package manifests, build definitions, CI configuration, and executable scripts that establish actual commands;
- existing architecture, schema, generated-artifact, and contract checks;
- architecture documentation and current-state documentation;
- active plans and confirmed upcoming changes;
- boundary cases and failure semantics.

Treat executable behavior and operational paths as evidence of current implementation. Treat confirmed roadmap information as a future constraint, not as proof of current behavior.

## 3. Form the change model

For a non-trivial change, establish:

- observed requirement or symptom;
- general root cause;
- owning abstraction or responsibility;
- affected stable contract;
- known change horizon;
- expected future variation;
- chosen change boundary;
- expected future modification sites;
- compatibility boundary status;
- testing and required-gate strategy, including verification evidence validity;
- workaround status.

Do not choose an implementation until this model distinguishes the symptom from the owner of the cause.

## 4. Choose the boundary

- Optimize for small future diffs, not a small current diff.
- Minimize unrelated change, not necessary change.
- Group responsibilities that change for the same policy reason.
- Do not merge responsibilities merely because their current code looks similar.
- Fix a controllable defect at the abstraction that owns it, even when this requires a larger coherent current change.
- Use confirmed future changes to choose seams and ownership boundaries, but do not implement speculative features.
- When incremental delivery is necessary, identify the target structure and make the current step move toward it without leaving accidental parallel models.
- Do not create a workaround for a cause owned by the codebase. An unavoidable external workaround must identify the external cause, stay at the nearest boundary, avoid leaking special cases upward, and have a removal condition.
- Before introducing a version, legacy path, compatibility adapter, fallback representation, or migration mechanism, read [compatibility boundaries](references/compatibility-boundaries.md) and establish its evidence gate.

## 5. Implement coherently

- Change the owning abstraction and all required consumers, contracts, generated artifacts, and current documentation together.
- Within one compatibility boundary, replace rejected, superseded, or intermediate behavior directly and update its consumers together. Release status alone does not determine whether a migration is needed.
- Remove obsolete branches, aliases, representations, and current-state documentation that no longer serve an operational contract.
- Preserve historical decisions only in clearly historical plans or evidence when that history remains useful.
- Do not add adjacent improvements unless they are required for the approved change boundary.
- Keep repository-specific invariants in repository code, configuration, tests, or checks rather than adding them to this global procedure.

## 6. Verify contracts, causes, and repository state

Verification success is evidence only for the exact repository state and execution conditions that were verified. Treat changes to relevant code, configuration, schemas, generated artifacts, dependencies, or tests as potentially invalidating earlier results.

Select verification from the affected risk and contract, not from the amount of new code.

During implementation, use targeted checks appropriate to the current change and cost. After the final relevant change, run the required gates for the completed scope. If a later change can affect a completed gate, mark that result stale, classify the impact, and rerun the affected required verification before completion.

Treat a required green state as an invariant to preserve while work continues, not as a permanent checkpoint. Do not claim completion using a successful result from an earlier repository state.

Prefer tests of:

- externally observable behavior;
- stable public or internal contracts;
- architectural invariants;
- state transitions and transaction semantics;
- meaningful failure behavior;
- important integration boundaries;
- the actual regression risk.

Question tests coupled to private helpers, internal call order, mock choreography, fixtures spanning unrelated subsystems, or decomposition that may change while the contract remains valid. New code alone does not justify a new test. Do not duplicate the same contract mechanically at multiple layers without a distinct risk.

When a gate fails, do not treat making it green as the complete objective. Establish the failure class, root cause, owning abstraction, and whether production code, test structure, configuration, environment, or workflow owns the defect.

If the same failure class has occurred before, investigate shared abstractions, fixtures, mutable state, configuration, and workflow before adding another local patch. Determine whether the earlier fix removed the general cause or only passed one observed instance.

Distinguish flakiness from regression:

- When the same repository state under equivalent conditions alternates between success and failure, investigate concurrency, shared mutable state, test order, timing, external dependencies, nondeterminism, environment leakage, caches, and resource contention.
- When repository state changed after the last green result, investigate regression or an incomplete root-cause fix before classifying the failure as flaky.

Do not use retries, longer timeouts, skipped or disabled tests, weakened assertions, unconditional snapshot updates, unsupported flaky classifications, failure-instance special cases, implementation-following test changes, or compatibility paths as substitutes for root-cause resolution. When one of these actions is actually justified, base it on an evidenced cause and verify that it preserves the intended contract.

Passing tests is not sufficient by itself. Before treating verification as complete, determine that:

- the evidence remains valid for the final relevant repository state;
- no relevant change occurred after the last required verification;
- the observed case is resolved;
- the general cause is removed at its owner;
- repeated instances of the same failure class no longer have an unaddressed shared cause;
- test or CI structure is not preserving an avoidable implementation coupling;
- the change applies across the affected behavior;
- no avoidable workaround or special case was introduced;
- confirmed near-term changes do not immediately invalidate the boundary;
- future similar changes have fewer or no more modification sites;
- current documentation matches runtime behavior.

## 7. Audit before completion

Review the complete affected result, not only the edited lines.

Confirm:

- Change, Preserve, Exclude, and Verification were honored;
- the final structure has one clear owner for each policy;
- rejected approaches and accidental compatibility remnants are absent;
- tests protect stable contracts at justified layers;
- plans, historical evidence, and current runtime are not conflated;
- repository guidance was not invented from conventions or plans unsupported by executable evidence;
- any newly proposed repository rule has one appropriate owner and is not duplicated from global governance;
- required verification was run after the final relevant change, and each result still applies to the final repository state;
- no stale verification result is used as completion evidence;
- repeated failures were not handled as an accumulation of isolated local patches;
- no avoidable retry, timeout, skip, weakened assertion, unsupported flaky classification, special case, or compatibility path was added merely to obtain green CI;
- every remaining limitation is reported;
- completion claims do not exceed the available evidence.

Use single-agent self-review by default. Do not require subagents for this procedure.

## Mechanical enforcement

Use existing repository linters, type checks, schema validators, architecture tests, generated-file checks, and contract validators when they cover the affected invariant.

If a durable invariant is mechanically decidable but has no check, propose or implement the narrowest repository-level check when that is within scope. Do not hard-code repository-specific commands or dependency rules into this global skill.

When repository guidance or checks do not yet exist, do not invent a universal check or copy a generic template blindly. Use the repository-harness procedure to derive the smallest useful structure from verified repository facts.
