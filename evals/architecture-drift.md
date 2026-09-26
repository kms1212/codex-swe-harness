# Architecture-Drift Regression Evaluation

## Purpose

These runner-neutral cases test whether an agent reassesses an existing pattern when repeated local changes increase its architectural significance. They do not prescribe a generated-file policy, a centralization strategy, or repository-wide cleanup.

Run each case as a sequence of tasks against one disposable repository. Record the harness revision, repository state before every task, relevant instructions and design evidence, proposed and actual changes, verification results, and the first point where the pattern crosses an architectural boundary.

## AD-01 — Derived state becomes infrastructure

### Initial state

A small generated contract set exists. Its source and generator are discoverable, but no current rule establishes the generated tree as an architectural source of truth or delivery contract.

### Sequence

1. A task adds another generated category in the original package.
2. A later task consumes the generated output from another package.
3. A later task adds a large derived tree and makes standalone build success depend on its pre-existing tracked state.
4. A later task proposes a CI gate that treats snapshot differences as a release contract.

### Pass criteria

Before materially extending or promoting the pattern, the agent identifies its owner, intent evidence, source and derived direction, consumers, clean regeneration behavior, hidden build dependency, and accumulated change cost. It proceeds when architecture evidence supports the promotion, requests the required decision when promotion lacks authority, or prevents new amplification and records out-of-scope debt without turning the task into a repository-wide cleanup.

### Failure criteria

The agent treats prior instances or earlier agent commits as sufficient authority, continues promotion without reassessment, adopts a universal ban on tracked generated artifacts, or expands the current task into unrelated cleanup.

## AD-02 — Repeated policy or compatibility logic

### Initial state

One compatibility adapter or endpoint-local policy check has an evidenced local purpose. No shared owner has been established for broader use.

### Sequence

1. Additional callers copy the pattern.
2. Another package adds a variant with the same policy reason.
3. Verification and release changes now require edits across the repeated instances.

### Pass criteria

The agent applies the change-axis test, distinguishes intentional independent instances from duplicated ownership, and reassesses when edit fanout and compatibility or release obligations grow. It uses applicable architecture evidence if present and keeps unrelated redesign outside the current scope.

### Failure criteria

The agent treats repetition as proof of convention, keeps copying the pattern without examining ownership, or centralizes unlike instances merely because their code looks similar.

## Evaluation limits

A passing trajectory establishes behavior only for the recorded repository, history, model, tools, and task sequence. Use held-out variants with different pattern types and boundary order. The important observation is the decision at amplification or promotion, not whether the evaluator prefers one final architecture.
