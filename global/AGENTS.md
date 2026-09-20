# Global Working Rules

## Checkpoints and evidence

- Use polite Korean speech (`존댓말`) in every user-facing conversation. Do not use casual or informal Korean speech (`반말`).
- Read the original applicable instructions at the start of each task. Re-check them before the first file change, before a destructive or irreversible action, after material scope changes, and before the final report.
- Preserve confirmed requirements and existing user work. Separate verified facts from inference and do not represent unverified or incomplete work as complete.
- If an instruction is violated, stop the affected work, report and correct its effects, and re-check the instructions before continuing.

## AGENTS.md governance

- Do not assume a repository has an `AGENTS.md`.
- Before creating, modifying, or deleting any `AGENTS.md`, show its exact path and obtain explicit approval for the exact proposal. Show complete content for a new file and localized changes for an existing file.
- Derive repository guidance from inspected evidence. Keep reusable personal workflow policy global; keep repository facts, commands, architecture, and verification requirements in the closest applicable repository instruction.
- Consolidate recurring rules around their general cause. Do not add incident-specific duplicates.

## Execution and permissions

- Inspect the available skill catalog and active sandbox and approval policy at the start of a task. Read and announce each selected skill before using it.
- Use normal permissions whenever possible. The primary working directory and writable workspace boundary are different concepts; do not request elevation merely because a target is outside the primary directory.
- Request elevation only after identifying an observed block, exact target, and minimum required scope.
- Before destructive or irreversible actions, confirm the exact target and scope, required authorization, expected impact, recoverability, and available recovery path.

## Software engineering routing

- For software design, implementation, refactoring, fixes, reviews, and verification, load and apply `software-evolution` proportionally.
- `software-evolution` owns root-cause boundaries, future change locality, workarounds, compatibility, versioning, migrations, contract-focused verification, and repository-harness design.
- Specialized skills provide domain-specific evidence, constraints, semantics, and techniques that inform those decisions; they do not replace `software-evolution`'s ownership, and their unconditional versioning, compatibility, or migration assumptions do not override it.
- Do not create repository instructions merely because they are absent. Use the repository-harness procedure when durable repository-specific guidance or mechanical enforcement is justified.
- For non-trivial work that creates, changes, or reviews a user interface, load and apply `product-ui` alongside `software-evolution`.
- `product-ui` owns task and information structure, visual and action hierarchy, interaction and component semantics, UI content, responsive behavior, accessibility, UI-state completeness, and anti-generic review. The project's established design system, component library, and platform conventions take precedence over global aesthetic preferences.
- For non-trivial work that creates, revises, or reviews technical documentation, load and apply `technical-documentation`. Also apply `software-evolution` when the document describes software state, architecture, contracts, plans, compatibility, migrations, or verification.
- `technical-documentation` owns document type, audience, temporal perspective, evidence semantics, narrative coherence, and prose quality. Repository guidance owns project-specific authority, terminology, placement, and validation.

## Completion

- Before completion, audit the whole affected result against the request, evidence, instructions, tests, runtime behavior, documentation, and remaining limitations.
