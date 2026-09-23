---
name: product-ui
description: Design or improve task-oriented product interfaces. Use for substantial UI work when information structure or interaction quality matters and for interfaces reported as generic or difficult to use.
---

# Product UI

## Governing outcome

The interface must let the user understand the relevant information and perform the intended task. Its structure must express the actual product contract. Familiar visual patterns are not evidence that this outcome is satisfied.

Choose the information and action hierarchy before decorative treatment. Simplicity removes unnecessary complexity while preserving what the task requires. Neither fewer visible elements nor more whitespace is an independent goal.

When the task model changes, apply the global reconstruction principle to the whole affected experience. Removing a decorative symptom is insufficient if the structure that produced it remains unclear.

## Responsibility

This skill owns UI semantics and presentation. Use `software-evolution` for the underlying software boundary and contract verification. Let the product's established design system govern visual decisions rather than imposing a global style.

Inspect the actual product and its nearby patterns. Package names and isolated screenshots do not establish the complete design system. Reuse an existing component when its interaction contract fits. When consumers repeatedly compensate for a bad fit, improve the owning abstraction with `software-evolution`.

## Establish the task model

Identify the user's primary decision or action. Determine what they must recognize before acting and which information they must compare. Inspect the actual data and permissions that determine the experience.

Establish the states the product can produce. Separate conditions when they have different causes or require different next actions. Do not invent states merely to fill a generic checklist.

Inspect rendered behavior when available. Use a brief internal pass for a local change whose task and established pattern are clear. A substantial interface change requires forming the complete task model before choosing components; it does not require a long design report.

## Derive the structure

Represent information according to its relationships. Preserve meaningful groups and comparison structure. A delimiter-separated string cannot substitute for a layout when the fields have different roles.

Give the primary task an evident scanning path. Distinguish essential information from detail that can safely be disclosed later. Choose density according to the work the user performs rather than a generic page template.

Choose controls by their interaction meaning. Accessibility relationships must express the same structure as the visible interface. Include those semantics while building the experience rather than repairing them after decoration.

Read [UI semantics and states](references/ui-semantics-and-states.md) when the task depends on structured content or nontrivial interaction behavior. Apply its state and accessibility criteria to the product's actual contract.

## Implement the product model

Use the established visual language to express hierarchy. Spacing should communicate relationships. Persistent text must add information the user needs rather than explain a title or compensate for an unclear control.

Responsive structure must preserve the task at the relevant widths. Reconsider priority and interaction when space changes; uniform shrinking or unconditional stacking does not establish usability.

Use the `software-evolution` change-axis test for shared UI abstractions. Similar appearance alone does not justify a component. Shared product policy can justify a common owner. Reuse a token that already owns a decision and introduce a new token only when a stable repeated design decision warrants it.

## Verify the actual experience

Read and apply [Anti-generic UI audit](references/anti-generic-audit.md) for every non-trivial UI task. Each persistent element must serve the task or the product's established identity. If an element is compensating for a structural weakness, repair that weakness before removing the element.

Inspect the rendered interface at representative states and widths when tools permit. Check whether the intended scanning path and actions are clear without supplementary explanation. Verify that the controls and recovery paths match the actual contract.

Verify keyboard use and accessible relationships in the composed interface. Independently accessible components do not establish that the screen as a whole is accessible. Exercise relevant content expansion and overflow behavior.

Run the required repository UI checks for the final relevant state. A later relevant edit invalidates earlier rendered or automated evidence under `software-evolution`.

## Completion judgment

Judge the completed interface by successful task use and contract fidelity. Removing generic styling does not by itself establish either. Confirm that the resulting structure fits the product and remains usable in the relevant states.

Report unresolved product assumptions and unavailable verification. Do not present an unrendered implementation as a visually verified result.
