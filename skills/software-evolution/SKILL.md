---
name: software-evolution
description: Derive and apply software engineering decisions from governing requirements. Use for reasoning about software change even before implementation and for repository engineering guidance.
---

# Software Evolution

## Governing model

Derive the present change from a design for the complete confirmed work. Bound that work by its minimal causal closure: all and only the changes whose omission would make the confirmed result incorrect, internally inconsistent, unverifiable, or immediately nonfunctional. The affected system must be coherent as though the accepted premises had governed it from the outset.

Root-cause analysis determines how deep the current fix must go; it does not authorize unlimited lateral expansion. Group behavior that changes for the same policy reason under one owner, correct the cause there, and reconstruct every induced consumer around that design. Current diff size cannot justify leaving the cause or a required consequence in place. Proximity to that owner cannot justify absorbing an independent defect or cleanup.

Confirmed future work constrains design and responsibility boundaries inside the current causal closure. It does not authorize implementation of future features or enlarge the present scope. Among designs that satisfy the current closure, prefer the one that keeps confirmed future variation local.

Preserved requirements constrain the design. Verification supplies evidence that the final affected system fulfills them. A successful procedure cannot replace that judgment.

## Establish the boundary

Use authoritative requirements to establish the target and the known change horizon. Use executable behavior to establish current implementation. A confirmed plan constrains the current design but does not prove that future behavior has been implemented or authorize implementing it now.

When competing causes would require different fixes, inspect a case that distinguishes them. The first failing line and existing file boundaries do not establish the cause's owner. A repeated failure calls for investigating the common cause.

Follow the contract from its actual entry point through the owning responsibility and every affected consumer. Establish what state must survive and what evidence could show that the design fails its current contract.

Current scope admits confirmed work, required root-cause dependencies, and induced consequences whose omission would break the confirmed result. User steering can admit independent adjacent work. Known future work and opportunistic cleanup remain outside the current scope; future requirements constrain choices inside it without entering it.

For any item admitted beyond the initial request, identify the current requirement it serves and the concrete failure caused by omission. Graph reachability, subsystem proximity, shared terminology, possible future influence, and simultaneous improvement are discovery signals rather than admission criteria.

Preserve an earlier contract only for an evidenced consumer or state that cannot move with the change. Existing code and release status alone do not establish that need. Read [Compatibility boundaries](references/compatibility-boundaries.md) before retaining an earlier contract or introducing a transition mechanism.

If delivery must be incremental, make each step converge on the target structure without creating an accidental parallel model. A compatibility mechanism or workaround is admissible only through the evidence gate and belongs at the nearest affected boundary, with its external constraint, verification, and removal condition established.

## Apply the model

This skill owns the software change boundary and the validity of verification evidence. Domain skills supply the constraints needed to choose that boundary. Repository guidance establishes local authority and executable requirements. Use `git-workflow` for Git operations.

When the task requires concrete implementation or verification decisions, read [Change execution and verification](references/change-verification.md). It governs dependency tracing through runtime paths and keeps final-state checks meaningful.

Before deciding the content or placement of repository guidance, read [Repository harness](references/repository-harness.md). Create such guidance only when inspected local facts need a durable owner. Follow the global approval requirement for `AGENTS.md` changes.

Scale the investigation to the requested judgment. A local change can have a brief model. Cross-boundary work needs enough evidence to choose the whole boundary before implementation. Do not turn the model into a mandatory report. Use single-agent self-review by default.
