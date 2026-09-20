# Repository Harness

Use this procedure to establish durable engineering guidance in a repository that has no adequate `AGENTS.md` or mechanical engineering checks.

Do not create repository guidance merely because it is absent. Create it when verified repository-specific knowledge or recurring decisions need a durable owner.

## 1. Establish scope

Determine:

- the exact repository root;
- the working directory and any relevant subtrees;
- whether root, parent, nested, or override instruction files already exist;
- whether the request is to propose, create, normalize, or extend repository guidance;
- which teams, packages, or execution environments the guidance will affect.

A request for repository guidance authorizes investigation and a proposal. It does not authorize an unshown `AGENTS.md` write.

## 2. Gather authoritative evidence

Inspect the smallest sufficient set of sources:

- executable entry points;
- package manifests and task definitions;
- build, test, lint, format, generation, and deployment scripts;
- CI configuration;
- architecture and operational documentation;
- schema and generated-artifact sources;
- directory dependency structure;
- active plans and current verification records;
- existing static, architecture, contract, and integration checks.

Verify commands from their executable definitions. Do not infer a command merely from ecosystem convention or a historical document.

Distinguish:

- current runtime and executable behavior;
- current operational procedure;
- confirmed future constraints;
- historical evidence;
- speculative plans.

## 3. Classify each candidate rule

Place a rule in repository guidance only when it is repository-specific, durable, actionable, and not better enforced mechanically.

Typical repository guidance includes:

- authoritative sources for architecture and status;
- repository structure and ownership;
- allowed dependency directions;
- supported setup and development commands;
- required verification selection;
- destructive project commands and their preconditions;
- deployment-impact classification;
- repository-specific definition of done.

Do not copy global policy concerning permissions, generic evidence handling, general software design philosophy, or `AGENTS.md` governance into a repository file.

Do not store formatting, generated consistency, dependency cycles, schema validity, or other mechanically decidable invariants only as prose when a reliable repository check is practical.

## 4. Choose placement

Use the repository-root `AGENTS.md` for rules that apply across the repository.

Use a nested `AGENTS.md` or `AGENTS.override.md` only when a subtree has materially different commands, ownership, constraints, or verification. Do not split files merely to make them shorter.

Keep operating procedures beside the relevant code or deployment tooling when agents and humans need the same procedure. Keep design intent and historical evidence in the repository's established design or documentation area.

## 5. Design the minimal repository harness

Select only sections supported by the repository. A useful root file may contain:

- project state and authoritative sources;
- architecture and directory responsibilities;
- development commands;
- repository-specific engineering invariants;
- verification and deployment-impact rules;
- definition of done.

This is a content checklist, not a fixed template. Omit unsupported sections and use the repository's terminology.

For each proposed rule, be able to state:

- the evidence supporting it;
- why it will recur;
- why repository guidance is its correct owner;
- whether a mechanical check should own all or part of it;
- which paths it governs.

## 6. Propose before writing

For a new `AGENTS.md`, show:

- its exact absolute path;
- its complete proposed content;
- any accompanying check or documentation files;
- the evidence behind non-obvious rules;
- how it avoids duplicating global guidance.

For an existing file, show only localized additions, replacements, and removals with identifying context.

Obtain explicit approval for the exact proposal before writing. Approval for one repository or path does not authorize another.

## 7. Apply and verify

After approval:

- make only the approved changes;
- validate Markdown and any new check syntax;
- run new or affected mechanical checks;
- verify documented commands against their actual definitions;
- verify instruction discovery from the intended repository and working directory;
- inspect the final diff for invented facts, duplicated policy, stale alternatives, and unintended scope;
- report any instruction, command, or invariant that remains unverified.

Do not claim that an `AGENTS.md` is effective merely because the file exists. Verify that Codex discovers it in the intended scope.

## 8. Evolve the harness

Update repository guidance when a durable repository fact changes or recurring evidence shows a general gap.

Do not add a rule for every isolated mistake. Identify the general cause and prefer:

1. correcting the owning code or abstraction;
2. adding a mechanical invariant when feasible;
3. improving repository guidance when model judgment or repository context is genuinely required.

Remove or consolidate stale rules when their owner moves to code, checks, or a more specific instruction layer.
