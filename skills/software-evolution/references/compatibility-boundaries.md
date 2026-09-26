# Compatibility Boundaries

Read this reference only when considering a version, legacy path, compatibility adapter, fallback representation, parallel schema, migration mechanism, or staged old/new behavior.

Versioning is not a way to avoid correcting the current design. It represents a real boundary between independently meaningful contracts or persistent states.

Compatibility adapters and migrations serve different boundary needs. An adapter preserves contracts that must coexist. A migration preserves state while moving from one confirmed boundary to another and does not by itself require old and new contracts to coexist.

## Evidence gate

A compatibility mechanism or migration is admissible when all of the following are identified:

- the concrete consumer, persistent state, peer, or external contract that must be preserved;
- the source and target compatibility boundaries;
- the observable break that direct replacement would cause;
- why that break must be avoided;
- whether preservation requires temporary coexistence or a one-time state transition;
- the completion, recovery, and removal conditions that apply to the chosen mechanism.

When these facts are absent, direct replacement is the admitted design.

## Conditions that can establish a real boundary

A separate version or compatibility path may be justified when at least one verified condition applies:

- a published API has independent external consumers;
- clients and servers cannot be updated together because they deploy independently;
- real persistent state must survive a transition between independently meaningful contract boundaries;
- peers with different protocol versions must coexist;
- external implementations depend on a public plugin, extension, ABI, or SDK contract;
- a real staged rollout requires old and new behavior to coexist temporarily;
- the user explicitly requires preservation of the earlier contract.

The existence of a condition does not determine the mechanism automatically. Choose the smallest boundary that preserves the verified need.

## Facts that do not establish a boundary

None of the following is sufficient by itself:

- old code or tests exist;
- past documentation describes the old design;
- the behavior was implemented once;
- an earlier design decision differs from the approved design;
- an internal development API currently has callers that can be updated together;
- disposable development data exists;
- a system is released or unreleased;
- adding `V2` is easier than repairing the owning abstraction;
- a schema or data model changed;
- a design iteration received a new plan or document identifier.

Distinguish product release versions, compatibility versions, and design iterations. A design iteration does not require parallel runtime contracts.

## Default decisions

When all consumers can move together, update them together.

For changes that remain within one compatibility boundary:

- replace the current contract in place;
- update all consumers, tests, generated artifacts, and current documentation;
- remove the rejected implementation and unused aliases;
- do not preserve `Legacy`, `Old`, `Compat`, fallback, parallel version paths, or migrations for intermediate states.

For data-model changes:

- identify whether the change stays within the current compatibility boundary or crosses into a confirmed new boundary;
- within one boundary, collapse intermediate changes into the current schema and prefer reset or atomic replacement when the verified environment permits it;
- when crossing confirmed boundaries and persistent state must survive, create and verify one transition from the source boundary to the target boundary;
- do not preserve development-step migrations merely because intermediate schemas once existed;
- define transition validation and recovery without requiring old and new contracts to coexist unless rollout evidence requires coexistence;
- do not add compatibility columns or fallback parsers without a real coexistence requirement.

When historical provenance remains useful, keep it in a clearly historical plan or verification record, not in the current operational model.

## If compatibility is justified

Keep the mechanism at the nearest boundary to the incompatible consumer or state.

Record:

- preservation target;
- old and new contracts;
- translation or migration responsibility;
- coexistence period, when coexistence is required;
- completion, recovery, and removal conditions;
- verification for both transition and removal.

Avoid leaking compatibility branches into unrelated higher layers. Do not duplicate an entire implementation when a narrower boundary can preserve the required contract.

## Completion audit

Before retaining a compatibility mechanism, verify:

1. Which concrete consumer or state still requires it?
2. Why can that target not move now?
3. Is the mechanism an adapter for coexistence or a migration between boundaries?
4. If old/new coexistence occurs, how long must it last?
5. What evidence verifies the transition, recovery, and any coexisting paths?
6. What event completes the transition or permits removal?
7. Is the cleanup owner and location clear?

If the answers no longer establish a real boundary, remove the mechanism rather than normalizing it as permanent architecture.
