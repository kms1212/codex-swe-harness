# Document Semantics

Use this reference to classify technical documents and keep their facts, time perspective, and evidence coherent.

## Core rule

A document must make clear:

- what kind of document it is;
- whose need it serves;
- which state of the world it describes;
- which sources support its claims.

Do not make one document silently alternate between current reference, future plan, decision history, migration, and release narrative.

## Document types

### Current-state reference

Describes the system, contract, API, architecture, schema, configuration, or runtime that exists.

It must be understandable without prior knowledge of rejected or superseded designs. Structure it around the current system rather than the sequence of changes that produced it.

Reference material should be factual, direct, and organized around the subject being described. Move task instructions, extended rationale, and change history elsewhere when they obscure the reference.

### How-to or operating procedure

Helps a competent reader complete a current task.

State prerequisites, actions, branching conditions, safety boundaries, expected results, and recovery steps as needed. Include only procedures that remain operational. Do not mix in obsolete workflows or an extended history of how the procedure evolved.

### Tutorial

Provides a managed learning experience.

Do not treat every step-by-step document as a tutorial. A tutorial teaches through a controlled path; a how-to guide supports real work toward a specific result.

### Explanation

Builds understanding of why a system or concept behaves as it does.

Explanation may include rationale, connections, constraints, and carefully selected history. It does not replace precise reference material or an executable procedure.

### Plan or proposal

Describes a proposed or approved future state.

Mark its status, scope, decisions, open questions, dependencies, and application boundary. Do not use present-tense implementation claims unless separate evidence establishes that the described part already exists.

A plan can constrain future work without proving current behavior.

### ADR or decision record

Preserves the context, decision, alternatives when relevant, consequences, and supersession of a significant decision.

An ADR is historical by purpose. It is not a complete current description of the system. When a later decision replaces an implemented decision, preserve the old record as superseded and link to the new decision according to repository convention.

### Migration or compatibility guide

Describes movement between source and target states that both matter to actual users, data, integrations, or operations.

Include:

- the real source state;
- the target state;
- compatibility constraints;
- transition steps;
- validation and recovery;
- the removal or completion condition.

Do not create old/new terminology, version narratives, or compatibility procedures when no real compatibility boundary exists.

### Changelog or release note

Describes observable changes for a defined release or time period.

Change-oriented terms are appropriate because change is the document's subject. A release note does not replace current reference documentation.

### Verification or evidence record

Records what was checked, under which repository state and conditions, and what the result supports.

It is evidence about a state, not the implementation itself. Keep its validity scope explicit and do not silently reuse it after relevant changes.

## Current-state perspective

Write current-state documentation from the current world model.

If the actual history is `A → B` and only B remains relevant, describe B directly. Do not introduce A merely because the author or diff knows it existed.

Treat phrases such as these as review signals in current-state prose:

- existing or previous;
- now or from now on;
- new or newly;
- no longer;
- instead of;
- changed, removed, or deprecated.

They are valid when the reader genuinely needs the comparison and the reference point is explicit. Otherwise state the current fact directly.

Do not translate an edit such as “replace A with B” into permanent prose saying “B replaces A”. Describe what B is and how it operates.

## Evidence semantics

Determine implementation claims from the repository's authority rules and relevant operational evidence, such as:

- executable code;
- operational entry points;
- runtime paths;
- current schemas and configuration;
- generated sources and their actual generators;
- verification performed against an identified state.

The existence of a plan, issue, identifier, mockup, generated artifact, or historical record does not establish that a feature operates.

When documentation conflicts with runtime evidence, first determine the document type. A future specification can intentionally differ from runtime. A current-state reference cannot rely on that explanation unless its role is explicitly different.

## Obsolete concepts

When an unreleased or unsupported design is removed from the current system, remove its conceptual model from current-state documentation as well.

This includes obsolete:

- terminology;
- component and service names;
- data models;
- workflows;
- contracts;
- rationale presented as current explanation.

Preserve useful history only in an ADR, historical plan, release record, or other clearly historical owner.

Current documentation complexity should track the current system, not the number of changes that led to it.

## Narrative maintenance

After an edit, review the document as one information system.

Check whether:

- headings reflect the resulting content;
- a later section still assumes the former model;
- one concept has multiple names;
- the plan and current state contradict each other;
- a current reference has become a chronological patch log;
- the reader must consult git history to understand an undefined “old”, “new”, or “changed” concept;
- historical comparison is justified by migration, compatibility, deprecation, security, or release needs.

Update the appropriate owner instead of copying the same fact into multiple document types.
