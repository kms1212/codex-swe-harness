# Anti-generic UI Audit

Apply this audit before completing a non-trivial product UI task. Its purpose is not to detect a particular visual style. It tests whether every element is justified by the product's task, information structure, interaction contract, or visual identity.

## Element-purpose audit

For each persistent element or repeated treatment, ask:

1. Which user problem does it solve?
2. What information, relationship, or affordance would be lost if it were removed?
3. Does its text add information, or repeat what the surrounding UI already communicates?
4. Is the container, card, badge, or pill a real semantic or interaction group?
5. Is punctuation substituting for layout or structured markup?
6. Is there a product-specific reason for the visual treatment?
7. Does the hierarchy support the actual scanning path?
8. Does the component carry the correct interaction semantics?
9. Does the accessibility tree express the same important relationships?
10. Does the interface expose the data and decision directly, or explain them through avoidable prose?

If removal loses nothing, remove the element after correcting any hierarchy or grouping weakness it was masking.

## Statistical-default audit

Require a concrete product, semantic, or interaction reason before retaining:

- a subtitle under every heading;
- repeated helper text or info icons;
- long `·`, `|`, `/`, or dash-separated metadata chains;
- rounded cards around every section;
- pills or badges for ordinary values;
- icons beside every heading or label;
- icon-only actions where text is clearer;
- top-of-page three- or four-card KPI grids;
- generic dashboard templates reused across unrelated tasks;
- decorative gradients, glass effects, glow, shadows, or floating shapes;
- excessive rounded rectangles;
- generic stock illustration or meaningless sparklines;
- oversized empty states;
- uniformly low-density layouts;
- generic SaaS marketing copy in operational screens.

These patterns are not prohibited. “Modern”, “clean”, or “common in dashboards” is not sufficient justification.

## Structure and contract audit

Check for:

- hierarchy compensated for by explanatory prose or nested boxes;
- real lists, tables, groups, and label/value relationships implemented as strings or generic containers;
- forms ordered by schema or DTO rather than user task;
- placeholder text acting as a label;
- validation and system failures sharing the wrong treatment;
- first-use, filtered-empty, permission, and failure states collapsed into one generic empty state;
- loading, error, partial, read-only, permission, overflow, focus, or narrow-width states missing from a contract that can produce them;
- inaccessible names, focus order, grouping, status cues, or dynamic announcements;
- responsive behavior that only shrinks or blindly stacks;
- project design-system components or tokens ignored without a semantic reason.

## Abstraction audit

Apply the `software-evolution` ownership and change-axis criteria:

- Do not extract components solely because two regions look alike.
- Look for product policy or interaction behavior that must change together.
- Do not force new semantics through an implementation-coupled component API.
- Improve the owning component when multiple consumers are compensating for the same limitation.
- Do not introduce variants or tokens for one speculative use.
- Do not repeat raw decisions already owned by stable project tokens or primitives.

## Completion condition

The interface is ready only when:

- its primary task and scanning path are evident;
- visual and semantic structures agree;
- necessary information is present without redundant commentary;
- components and states match their contracts;
- project-specific design language is preserved;
- relevant accessibility and responsive behavior have been verified;
- remaining assumptions and unverified states are reported.

When a symptom is found, repair the underlying information structure, interaction, or owning abstraction. Do not treat deleting a decorative artifact as sufficient if the screen remains unclear.
