---
name: product-ui
description: Design, implement, refactor, or review task-oriented product interfaces across web and native projects. Use for non-trivial screens, forms, tables, lists, dashboards, navigation, workflows, responsive changes, UI states, accessibility, or feedback that an interface is generic, AI-like, or hard to scan. Preserve the project's design system and use software-evolution for architecture and change-boundary decisions.
---

# Product UI

Translate real user tasks, information relationships, and interaction contracts into clear product interfaces. Do not begin from a generic visual template or optimize for the fewest visible elements.

This skill owns UI-specific judgment. `software-evolution` continues to own root-cause analysis, abstraction and change boundaries, compatibility, and contract verification.

## Precedence

Before applying global guidance, inspect the product's:

- purpose, users, and primary workflows;
- established design system and component library;
- tokens, typography, spacing, iconography, and content conventions;
- nearby screens and interaction patterns;
- platform conventions and accessibility requirements.

Preserve coherent project-specific decisions. Global guidance supplies a decision procedure and quality criteria, not a replacement visual identity.

Reuse an existing component when its semantics and interaction contract fit. If reuse would force the wrong behavior or meaning, apply `software-evolution` to improve the owning abstraction instead of preserving a bad fit for superficial consistency.

## Scale the procedure

Use a brief internal pass for a small, local UI change whose task, semantics, states, and project pattern are already clear.

Use the complete procedure for:

- a new screen or page;
- a dashboard, form, data table, list, navigation surface, or workflow;
- onboarding, settings, or a major component;
- responsive restructuring;
- loading, empty, error, permission, or other state design;
- a substantial UI refactor;
- an interface reported as generic, AI-like, confusing, or difficult to scan.

Do not turn the procedure into mandatory long user-facing design prose.

## 1. Inspect

Establish:

- the user's primary task and decision;
- the information they need before acting;
- the current UI and nearby product patterns;
- the actual data shape and interaction contract;
- the existing design system, components, and tokens;
- permissions, failure behavior, and platform constraints;
- the states the product contract can actually produce.

Inspect rendered behavior when available. Do not infer a design system only from package names or isolated artifacts.

## 2. Structure

Before selecting components, answer:

1. What is the main job of this surface?
2. What must be recognized first?
3. Which information forms semantic groups?
4. Which values must be compared?
5. Which items are states, actions, navigation, or supplementary detail?
6. What must remain visible, and what can be progressively disclosed?
7. How do frequency and importance differ?
8. What density supports the actual scanning and decision pattern?
9. How must the structure change at narrow widths?
10. Which loading, empty, error, disabled, read-only, permission, and partial states are real?

Choose an information and action hierarchy before decorative treatment. Simplicity means removing unnecessary complexity while keeping the information required for the task; it does not mean minimizing visible information or whitespace-maximizing every surface.

## 3. Implement

- Establish semantic structure before visual decoration.
- Choose components by interaction meaning, not by preferred shape.
- Use layout, typography, alignment, proximity, and contrast to communicate hierarchy.
- Use spacing to express relationships, not to manufacture emptiness.
- Keep persistent UI text only when it adds information, a constraint, a consequence, or necessary guidance.
- Preserve the project's visual language before introducing new styles or primitives.
- Make responsive behavior preserve task priority, comparison, actions, navigation, and readable overflow rather than merely shrinking or stacking the desktop layout.
- Include accessibility semantics and interaction behavior while constructing the UI, not as a later repair.
- Inspect the rendered result at representative states and widths when the task and available tools permit it.

Read [UI semantics and states](references/ui-semantics-and-states.md) when the work includes structured metadata, forms, content, errors, empty or loading states, complex interactions, responsive restructuring, or accessibility-sensitive behavior.

For shared UI abstractions, use the `software-evolution` change-axis test. Similar appearance alone does not justify extraction. Repeated ownership of the same product policy or interaction contract may justify a shared owner. Promote tokens only after a stable repeated design decision exists; do not repeat raw values when an established token already owns the decision.

## 4. Verify

Verify the completed interface against its actual task and contract:

- The scanning path reveals priority without explanatory prose.
- Labels and actions identify what they control or do.
- Structured information remains structured rather than becoming a delimiter-separated string.
- Components express the correct navigation, action, selection, status, and disclosure semantics.
- Relevant states are distinct and recoverable.
- Keyboard order, focus visibility, accessible names, relationships, and announcements are correct.
- Meaning is not conveyed by color or visual position alone.
- Long content, localization expansion, narrow widths, and overflow remain usable where relevant.
- Project-specific design and content conventions remain coherent.
- Applicable repository UI, accessibility, and interaction tests pass for the final repository state.

After the final relevant change, re-run required verification according to `software-evolution`; do not reuse stale rendered or automated evidence.

## 5. Audit before completion

For every non-trivial UI task, read and apply [Anti-generic UI audit](references/anti-generic-audit.md).

When the audit identifies a disposable text, box, badge, icon, or effect, determine which information-architecture or interaction weakness it was compensating for before deleting it. Repair the underlying structure first.

Report unresolved product assumptions, missing states, unavailable rendered verification, or design-system conflicts explicitly.
