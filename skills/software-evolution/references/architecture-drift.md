# Architecture Drift

Read this reference when a proposed change materially amplifies an existing pattern, carries it across a subsystem boundary, promotes it into stable infrastructure, or exhibits growing change and verification fanout. Ordinary local reuse does not require this reassessment.

## Evidence boundary

Executable code, runtime paths, schemas, configuration, and tracked artifacts establish current state. They can also establish real consumers and preservation obligations. Their existence alone does not establish that the pattern is intended, healthy, or approved for further propagation.

Architectural intent needs separate evidence such as an applicable repository rule, approved design or ADR, authoritative current contract, enforced architecture invariant, explicit user decision, real compatibility boundary, or a stable abstraction whose owner and change axis are established.

Repeated agent-generated precedent remains implementation evidence. Repetition may indicate a stable intentional pattern or an accumulated accident; instance count alone does not distinguish them.

## Classify the proposed use

### Local reuse

The change adds an instance within the same owner, contract, subsystem, and dependency direction without materially increasing future change cost. Local reuse is admissible at ordinary review cost when the existing authority remains valid.

### Pattern extension

The change carries the pattern to a new subsystem, package, consumer class, or persistent boundary, or materially increases instance count, edit fanout, verification surface, or removal cost. Extension requires the short reassessment below.

### Pattern promotion

The change makes the pattern a source of truth, stable public or internal interface, persistent state, build input, CI gate, release contract, or compatibility obligation. Promotion requires architecture-level evidence or an authorized architecture decision before implementation proceeds.

## Amplification events

Reassess when one or more of these events materially changes the pattern's significance:

- crossing a package or subsystem boundary;
- adding many instances, consumers, affected paths, or repeated derived artifacts;
- promoting a runtime-local detail into build, CI, release, or source-of-truth infrastructure;
- creating a compatibility or migration burden;
- repeating the same policy or translation in multiple owners;
- making clean or standalone execution depend on pre-existing generated, cached, or tracked state;
- increasing cross-package edit fanout, generated churn, or required verification with each instance;
- relying on “it already exists” as the reason for further propagation.

Use project scale and consequence rather than universal numeric thresholds. Existing architecture evidence can satisfy a recurring decision without reopening it on every task.

## Short reassessment

1. Identify the pattern's authoritative owner and the evidence that it is intentional.
2. Classify the proposed change as reuse, extension, or promotion.
3. Trace authoritative source, derived state, generators, consumers, and dependency direction.
4. Estimate accumulated cost through instance count, change fanout, verification, manual synchronization, compatibility, and removal or migration obligations.
5. Apply the change-axis test: determine whether repeated instances change together for the same policy reason and therefore indicate a missing shared owner.
6. When the current evidence warrants the cost, inspect history for recurring churn, rapid instance growth, or repeated compatibility patches.
7. Decide whether to reuse the pattern, redesign the current extension, require an architecture decision before promotion, or prevent further amplification and record a follow-up.

History is longitudinal evidence, not authority. Several earlier tasks choosing the same pattern can establish longevity and consumer reliance without establishing architectural quality.

## Source-of-truth and hidden dependencies

For derived artifacts, establish the authoritative source, generator, consumers, regeneration path, and clean-checkout behavior. Investigate a direction such as `source → derived artifact → another generator or build input` when derived state begins acting as authority or requires in-place edits.

Generated artifacts can be valid tracked contracts. The decision depends on provenance, ownership, dependency direction, reproducibility, and delivery needs rather than a universal generated-file policy.

## Scope decision

The reassessment changes the implementation approach when the current proposal would create or amplify the problem inside the confirmed causal closure. It does not authorize unrelated cleanup.

When existing repository debt is outside the current closure, avoid adding new dependence on it where the confirmed result permits, preserve real consumers, and record a separate architecture follow-up. Continue the authorized task unless the next required action needs an unresolved architecture decision or other genuine stop boundary.

## Boundary examples

- One compatibility adapter can belong to a verified external boundary. Repeating adapters across versions and callers can trigger reassessment of the compatibility owner and translation direction.
- A copied permission check can be valid local enforcement. Repeated same-policy edits across endpoints can indicate that the policy owner is distributed incorrectly.
- A generated tree can be an intentional release artifact. Its expansion into other generators, standalone builds, or CI contracts requires reassessing provenance and source-of-truth direction.

The reassessment evaluates whether amplification is intentional and sustainable. It does not prescribe centralization, prohibit generated files, or require redesign whenever code repeats.
