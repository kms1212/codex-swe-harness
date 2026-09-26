# Commits and History

Read this reference when staging, committing, amending, or reorganizing unpublished local commits.

## Commit authorization

A commit is admissible when the user requests it or the applicable repository workflow explicitly requires it. Implementation completion by itself does not supply that authority.

A task can be complete with uncommitted changes. When a commit is authorized, completion includes recording and verifying it.

Before committing, identify the repository-specific commit convention from applicable instructions, contribution guidance, or recent relevant commits. Do not impose a global language or message format.

## Choose the semantic boundary

Use the change boundary established by `software-evolution`.

A commit should be conceptually coherent, not mechanically small. Separate unrelated changes, but do not divide one correct engineering change merely because it spans multiple files or layers.

Evaluate a candidate boundary with these questions:

1. Can the changes be described accurately in one sentence?
2. Would removing one part leave the remainder incomplete or incorrect?
3. Do the changes implement the same contract, policy, or design decision?
4. Does a separate revert represent a real operational or review boundary?
5. Would separation improve review, or only create an artificial intermediate state?

File boundaries do not determine commit boundaries. Different reasons for changing the same file may justify separate commits; one reason spanning service, schema, callers, tests, generated artifacts, and current documentation may justify one commit.

Do not preserve attempts, rejected implementations, temporary repairs, or cleanup order as separate commits merely because they occurred sequentially.

Avoid known-broken intermediate commits unless the broken or transitional state is itself an intentional, reviewable migration step with an explicit delivery purpose.

## Select staged content explicitly

Treat the index as the exact change asserted by the next commit. Repository-wide staging is admissible only when every included path has established provenance and belongs to that conceptual unit.

Do not default to repository-wide staging such as `git add -A` or `git add .` when unrelated or uncertain changes may exist.

Select exact paths or hunks when needed to separate provenance or change axes. Do not require partial staging mechanically when all changes in the affected files belong to one coherent unit.

After staging, inspect both:

- the staged file list;
- the complete staged diff.

Do not use the working-tree diff as a substitute for staged-diff review.

If partial staging would create an invalid file state, an incoherent generated/source relationship, or a misleading commit, choose a safer boundary rather than forcing hunk-level separation.

## Inspect the proposed commit

Before committing, check for:

- pre-existing user changes outside the requested scope;
- unrelated formatting;
- debug code or temporary instrumentation;
- rejected implementation remnants;
- accidental file deletions;
- unexpected binary changes;
- unexpected generated output;
- source-of-truth and generated-artifact mismatch;
- dependency and lockfile mismatch;
- credentials, tokens, keys, private certificates, local configuration, personal paths, or private source material;
- tests or documentation that no longer describe the final contract.

Large diffs are not inherently wrong. Unexpected or unexplained diffs require investigation.

If the project commits generated artifacts, keep the source-of-truth and required generated output in the same meaningful change. If project policy excludes generated output, do not add it globally.

If a dependency change requires a lockfile update, include the required update. If no dependency change was intended, investigate an unexpected lockfile rewrite rather than committing or deleting it automatically.

## Keep contracts and verification coherent

Tests belong with the contract or regression risk they demonstrate, not in a mechanically separate “tests” commit.

Do not create this pattern unless it expresses real delivery boundaries:

`implementation → tests → fix tests → docs`

When implementation, contract tests, generated artifacts, and current-state documentation collectively establish one independently meaningful change, keep them together.

Run required verification against the final relevant repository state. A green result from before a relevant code, configuration, test, schema, dependency, or generated-artifact change is stale.

Do not push an unverified state merely to use remote CI as the default local development loop when repository policy defines required local gates. CI-only checks remain valid remote evidence when they cannot run locally.

## Represent conceptual evolution

History should present the meaningful resulting change, not every edit attempt.

Local unpublished commits may be reorganized when:

- the operation is authorized;
- the commits form the same conceptual change;
- no shared consumer depends on the current commit identities;
- the resulting history is coherent and recoverable.

Do not rewrite shared history merely to improve aesthetics.

Git history already preserves past implementations. Its existence does not justify retaining obsolete aliases, fallback branches, `Legacy` or `V2` paths, or historical explanation in current-state documentation. `software-evolution` determines whether a real compatibility boundary exists.

## Write the commit message

Follow repository conventions when they exist.

Otherwise, state the meaningful conceptual change concisely. Prefer what changed in the system over a list of editing actions or files.

The message must match the staged diff. Do not use a broad architectural claim for a narrow patch or a narrow message for a cross-cutting contract change.

## Handle sensitive material

If uncommitted sensitive material is discovered, keep it out of the staged set and report it without exposing its value.

If a secret was already committed, a later deletion does not remove it from history or invalidate the credential. Report the separate history-remediation and credential-rotation risk. Do not rewrite shared history or rotate credentials without the required authorization.

## Commit completion check

Immediately before commit, confirm:

- the staged set is the intended conceptual unit;
- no unrelated or uncertain-provenance change is staged;
- the commit message describes that exact set;
- required verification remains valid;
- source and required derived artifacts agree;
- no sensitive or local-only material is included.

After commit, verify the resulting commit and report any remaining staged, unstaged, or untracked state without treating it as failure.
