# UI Semantics and States

Use this reference when a product UI task includes structured information, content, forms, state handling, responsive restructuring, or accessibility-sensitive behavior.

## Structured information

Do not replace semantic structure with punctuation.

Use the representation that matches the relationship:

- lists for collections;
- tables for records whose fields must be compared;
- definition structures or label/value layouts for named attributes;
- headings and sections for meaningful groups;
- fieldsets and legends for related form controls;
- status treatment only for actual state;
- disclosure only for supplementary detail that can safely remain hidden.

A short delimiter-separated sequence can be appropriate for lightweight, homogeneous metadata. It is not a general layout primitive. If fields differ in meaning, importance, interaction, or comparison behavior, preserve those distinctions structurally.

Visual grouping and the accessibility tree should describe substantially the same relationships.

## Interaction semantics

Choose controls from the user's mental model and interaction contract:

- an action uses a button;
- navigation uses a link or navigation component;
- mutually exclusive choices use an appropriate radio group, select, or equivalent control;
- an independently selected option uses checkbox semantics;
- a switch is reserved for an immediate on/off setting when the project convention supports it;
- comparable structured records use an appropriate table or list;
- destructive actions use explicit destructive semantics and the project's confirmation policy;
- supplementary information uses an appropriate disclosure or help surface.

Do not turn every action into an icon-only button, every value into a badge, or every group into a card. An icon-only control needs a clear accessible name and must remain recognizable in its context.

Use native semantic elements where they provide the required contract. Add ARIA to express relationships or dynamic behavior that native semantics do not cover; do not use ARIA as the default repair for incorrect structure.

## UI content

Persistent text must contribute information.

Do not add a subtitle, description, helper, tooltip, or annotation merely to restate a visible title, label, component type, position, state, or action. Do not use generic product-marketing language in operational interfaces.

Prefer action labels that state the actual action over context-free labels such as “Continue”, “Confirm”, or “Get started” when the action can be named concisely.

Helper text is justified when it communicates:

- accepted values or required format;
- a real constraint;
- an important consequence;
- non-obvious behavior;
- guidance necessary to complete the task.

Keep essential information visible. Do not hide task-critical instructions behind a tooltip or info icon. Repeated need for help icons is evidence that the label, grouping, interaction, or information architecture may need redesign.

Keep visible labels for controls. Placeholder text may provide an optional example, but it does not replace a label and must not contain information that disappears when input begins.

## Forms

Order and group fields according to the user's task and mental model, not a database schema, DTO, or implementation decomposition.

Ask only for information the user actually needs to provide. Consider defaults and progressive disclosure where they reduce work without hiding required choices.

Validation errors must tell the user:

- what is wrong;
- where the problem is;
- how to correct it.

Preserve entered values when correction is possible.

Do not present permission, capacity, network, server, or other system failures as field-validation errors. System failures need a surface that explains the current condition, preserves safe user work where possible, and offers only actions that can actually help.

## Empty, loading, and result states

Distinguish states that imply different causes or next actions:

- first use;
- no existing data;
- no search results;
- no filtered results;
- insufficient permission;
- failed loading;
- partially available data;
- data that is stale while refresh failed.

An empty state should explain the relevant cause and, when useful, the single most important next action. It does not require an illustration, marketing copy, or a large decorative container.

Loading feedback should be attached to the affected scope. Prevent competing indicators and announce meaningful asynchronous state changes where assistive technology needs them.

## State completeness

Consider each state that can exist under the actual product contract:

- initial;
- loading;
- populated;
- empty;
- filtered or searched empty;
- validation error;
- system error;
- partial failure or stale data;
- disabled;
- read-only;
- permission denied;
- offline or retrying;
- success or confirmation;
- long content and localization expansion;
- narrow viewport and overflow;
- focus, hover, pressed, selected, and other relevant interaction states.

This is a discovery checklist, not a requirement to invent every state. Implement and verify the states that the product can actually produce.

## Responsive structure

Do not treat responsive design as uniform scaling or unconditional vertical stacking.

At relevant widths, reconsider:

- information priority and disclosure;
- navigation model;
- action placement;
- grouping and reading order;
- table comparison and overflow;
- line length;
- touch targets;
- what may be summarized or deferred without losing the task.

Desktop layouts need not imitate mobile card stacks. Narrow layouts may require reflow, repositioning, controlled disclosure, or a different interaction structure.

## Accessibility

Include accessibility in the initial structure and verify:

- semantic elements and heading order;
- accessible names and visible labels;
- logical keyboard and reading order;
- visible focus and sensible focus restoration;
- relationships between labels, descriptions, errors, groups, and controls;
- non-color status cues and sufficient contrast;
- usable pointer and touch targets;
- announcements for meaningful dynamic changes;
- content reflow and zoom behavior;
- alternatives for meaningful non-text content.

Use established accessible components correctly, but do not assume that an individually accessible component makes the composed screen accessible.
