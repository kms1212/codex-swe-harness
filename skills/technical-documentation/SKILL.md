---
name: technical-documentation
description: Create or maintain durable technical documents with explicit purpose and evidence. Use when the document's temporal perspective and complete narrative affect how readers understand or operate a system.
---

# Technical Documentation

## Governing outcome

A document must give its intended reader one coherent account of the state it describes. Its meaning must hold without the conversation or diff that produced it.

Current-state documentation describes the actual system directly. When a premise changes, rebuild the complete affected narrative from the accepted model. Remove obsolete assumptions wherever they influence that narrative.

The document's declared purpose determines its temporal perspective. A plan describes intended work. It does not establish current behavior. Preserve decision history only where history serves the reader's task.

## Responsibility

This skill owns document meaning and prose. `software-evolution` owns the underlying software contract and the validity of implementation evidence. Use them together when the document makes software claims.

Repository conventions determine document authority and placement. Follow established terminology and maintained templates. Inspect the source of generated documentation before editing its output.

Use `product-ui` for interface content. Use the relevant format skill when the deliverable needs document rendering or layout verification.

## Establish the document model

### Purpose and perspective

Determine the document type and the reader's task before choosing a structure. Establish which state the document describes and which sources can substantiate it.

Read [Document semantics](references/document-semantics.md) for substantial technical documents or when their temporal perspective is unclear. Apply the distinctions for the document at hand rather than copying a generic template.

### Evidence

Read the whole affected document and its authoritative sources. Inspect nearby documents when their meaning depends on the same contract. For current implementation claims, inspect actual operational paths.

Keep confirmed facts separate from proposed work. Treat historical decisions as evidence of their own period. A document name or plan identifier does not prove implementation.

When a claim is uncertain, resolve it from the relevant authority or state the uncertainty. Do not fill gaps with a plausible explanation or treat agreement as corroboration.

### Narrative structure

Form the complete model the reader needs. Decide which concepts remain valid and where their definitions belong. Derive the affected narrative from that model rather than from the easiest paragraph to patch.

For a current-state reference, every section must make sense without knowing a superseded design. For a plan, distinguish the target from the observed baseline. A request to write a plan does not authorize implementation or a rewrite of current operating instructions as though the plan had shipped.

Use a brief internal pass for a small correction whose meaning is established. A substantial change requires reviewing the complete affected narrative, even if only one sentence first revealed the problem.

## Write from the model

Organize the document around its subject and the reader's task. Define concepts before relying on them. Keep a consistent temporal perspective within each clearly delimited section.

Write the resulting state directly. Use established terminology consistently. State concrete responsibilities and observable behavior. Include rationale only when it helps the reader understand the contract.

Remove editing history from current-state explanations. If comparison is necessary for a real transition, identify the source and target states explicitly and use the appropriate historical or migration document.

For non-trivial prose, apply [General LLM prose tropes](references/tropes.md). For Korean prose, also apply [Korean technical writing](references/korean.md). Use these to improve meaning and readability rather than as mechanical word bans.

## Verify the complete document

### Meaning

Read the entire affected document after the final edit. Confirm that its structure matches its declared purpose and that later sections use the same model as earlier ones. Check definitions and cross-references against their actual owners.

Trace implementation claims back to appropriate evidence. Keep plans distinct from implemented behavior. Retain superseded concepts only where the document's historical purpose requires them.

### Prose

Check that each paragraph adds a necessary fact or decision. Consolidate repetition at its owner. Prefer a general rule when several examples express the same cause. Use a list only when the reader needs to distinguish its members.

Correct semantic contradictions before polishing style. The completed narrative must be understandable without reading the editing history.

### Mechanical evidence

Run the applicable document checks after the final relevant change. When documentation is generated, verify its source and regenerated output together. Follow `software-evolution` for verification validity.

Structural validation establishes document structure. It does not establish factual accuracy or reader comprehension. Report missing evidence and unresolved claims as limitations.
