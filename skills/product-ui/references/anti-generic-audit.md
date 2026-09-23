# Product-specific UI Audit

Apply this audit before completing a non-trivial product UI task. It tests whether the interface is justified by the product's actual task. It is a design review, not a claim about the statistical frequency or training origin of visual patterns.

## Task and hierarchy

Identify the primary decision the user must make. Follow the actual scanning path and check whether the information needed for that decision is apparent.

When text or nested containers explain a relationship that the layout should communicate, repair the hierarchy. Deleting the explanation alone does not establish a usable interface.

Choose density from the work. A sparse layout can hide comparisons just as a crowded layout can obscure priority. Neither density is a universal default.

## Element purpose

For each persistent element, identify what the user would lose if it were absent. Retain it when that loss matters to the task or the established product identity. Remove it when no useful function remains.

Text should contribute information. A subtitle that repeats its heading does not clarify the task. Repeated help treatment can indicate that a control or group needs redesign.

A container should express a meaningful group. A badge should communicate a real status or another established product meaning. An icon should aid recognition rather than decorate every label. Require the same justification for a repeated page template as for an individual component.

Visual effects can serve the product's identity. Their popularity or a generic claim of modernity does not establish that purpose. Do not impose a blanket ban on a treatment that has a concrete role in this product.

## Semantic structure

Check that the interface preserves the relationships in its data. Comparable records need a comparison structure. Different attributes must not become a punctuation-separated string that erases their roles.

Forms should follow the user's task rather than implementation field order. Controls need visible labels and correct interaction semantics. Essential guidance must remain available while the user acts.

Different causes need different recovery behavior when the contract requires it. An absent record and a failed request must not share a misleading empty state. Apply [UI semantics and states](ui-semantics-and-states.md) to verify the actual state model.

## Composed behavior

Verify that the accessibility tree communicates the same important relationships as the visual layout. Follow keyboard navigation through the complete task and check that focus remains meaningful after state changes.

At narrow widths, preserve the user's decision and access to its actions. Check relevant overflow and content expansion. A layout that only shrinks or stacks has not yet demonstrated that the task remains usable.

Use the project's established components and tokens when their contracts fit. Do not replace them merely to produce a different style.

## Ownership

Apply the `software-evolution` change-axis test. Shared product policy can justify a shared component. Similar appearance alone cannot.

When consumers repeatedly compensate for one component's limitation, inspect the owning contract. Avoid accumulating variants around an owner that can be corrected. Do not introduce a new abstraction for speculative future use.

## Completion judgment

The primary task must be evident and achievable in the relevant states. Necessary information must remain accessible without redundant commentary. The result must preserve the product's design language and interaction contract.

Report missing evidence and unresolved assumptions. Removing familiar visual patterns is not a substitute for verifying the completed experience.
