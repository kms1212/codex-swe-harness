---
name: technical-documentation
description: Create, revise, review, or maintain durable technical documentation whose type, audience, temporal perspective, factual evidence, narrative coherence, and prose quality matter. Use for READMEs, reference material, how-to guides, plans, proposals, ADRs, architecture documents, migration guides, release notes, verification records, and Korean technical prose.
---

# Technical Documentation

Treat documentation as an information system with an explicit purpose, audience, time perspective, and evidence base. Do not write current documentation as a narrative of the edits that produced it.

This skill owns documentation semantics and prose quality. `software-evolution` owns the underlying software facts, contracts, architecture, compatibility boundaries, and verification validity.

## Responsibility and precedence

Inspect and preserve repository-specific:

- document authority and placement;
- established terminology;
- document templates and status conventions;
- current-state, plan, history, and verification directories;
- generated-document sources and validation commands.

Repository evidence and terminology take precedence over generic examples in this skill.

Use `product-ui` for labels, helper text, errors, empty states, and other interface content. Use this skill when a durable technical document explains the product or system. If the output is a Word or other formatted document artifact, use the relevant document-format skill for layout and rendering in addition to this skill.

## Scale the procedure

Use a brief internal pass for a local correction whose document type, facts, terminology, and surrounding narrative are already clear.

Use the complete procedure when:

- creating a document or substantial section;
- changing architecture, API, runtime, operational, or contract documentation;
- writing or revising a plan, ADR, migration guide, release note, or verification record;
- removing or superseding a design;
- resolving disagreement between documentation and runtime evidence;
- changing terminology across a document;
- rewriting prose reported as historical, repetitive, inflated, translated, or difficult to follow.

Do not produce a long process report for a small edit.

## 1. Classify

Before writing, determine:

- the document type;
- the intended reader and their necessary prior knowledge;
- the temporal perspective;
- the authoritative sources for its claims;
- the reader outcome the document must support.

Do not begin from the diff or from a generic document template.

Read [Document semantics](references/document-semantics.md) for every non-trivial document that describes current state, future work, decisions, migration, releases, or verification, and whenever the document type or time perspective is unclear.

## 2. Inspect

Inspect the breadth required to establish the document's truth model:

- applicable repository instructions;
- the whole affected document and nearby documents;
- executable code, runtime paths, schemas, and configuration when current implementation is described;
- plans and proposals when future state is relevant;
- ADRs or historical records when decision history is relevant;
- verification evidence and the repository state to which it applies;
- established project terminology and style references.

An artifact, plan, issue, or document name is not by itself implementation evidence.

Do not inspect history merely to add history. Use it only when the document type or a real compatibility boundary requires it.

## 3. Model

Before drafting, separate:

- verified current facts;
- approved or proposed future state;
- historical decisions;
- migration or compatibility facts;
- verification evidence;
- unresolved assumptions;
- obsolete concepts that the document must not preserve.

Decide what the reader must know and what would only expose internal editing history.

For current-state documentation, form a complete model of the current system that does not require knowledge of rejected or superseded designs.

## 4. Write

- Write the resulting state directly.
- Maintain one temporal perspective within each document or clearly delimited section.
- Match the structure and voice to the document type.
- Define concepts before using relative descriptions of them.
- Preserve stable project terminology.
- Prefer concrete actors, actions, contracts, conditions, and observable properties.
- Include history only when it serves the declared document purpose.
- Remove obsolete terminology and conceptual models from current-state prose.
- Avoid adding prose that merely narrates the edit.

## 5. Audit semantics and time

Confirm:

- current state, plan, history, migration, release information, and verification evidence are not conflated;
- every implementation claim has evidence appropriate to the repository;
- current-state prose does not require knowledge of superseded designs;
- relative terms such as “previous”, “new”, or “now” have a necessary and explicit reference point;
- a plan or artifact is not represented as implemented behavior;
- migration language corresponds to an actual source state, target state, and compatibility boundary;
- superseded concepts remain only in documents whose purpose is historical;
- the document does not accumulate change history in place of a current model.

Correct semantic and temporal defects before polishing style.

## 6. Audit prose

For non-trivial prose, read and apply [General LLM prose tropes](references/tropes.md).

For Korean prose, also read and apply [Korean technical writing](references/korean.md).

Treat these references as review criteria, not mechanical word bans. Preserve technically necessary terms and constructions.

## 7. Audit the complete narrative

Read the complete affected document after the final edit, not only the changed lines.

Check:

- headings still describe their sections;
- definitions and terminology remain consistent;
- later sections do not preserve superseded assumptions;
- adjacent sections do not contradict the new model;
- the same claim is not repeated without a distinct reader need;
- reference, procedure, explanation, decision history, and release narrative remain properly separated;
- links and cross-references still point to the correct authority;
- the document can be understood without reading the git diff or the conversation that produced it.

Run applicable documentation generation, link, schema, formatting, or repository checks after the final relevant change. Apply `software-evolution` verification-validity rules and do not use stale results.

Report unresolved facts, unavailable evidence, and deliberate historical context explicitly.
