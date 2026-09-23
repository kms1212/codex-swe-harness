---
name: software-evolution
description: Derive and apply software engineering decisions from governing requirements. Use for reasoning about software change even before implementation and for repository engineering guidance.
---

# Software Evolution

## Governing model

Derive the present change from a design for the complete confirmed work. The affected system must be coherent as though the accepted premises had governed it from the outset. Confirmed upcoming work constrains today's responsibility boundaries; it does not authorize speculative features.

Group behavior that changes for the same policy reason under one owner. This is the change-axis test. Correct the cause at its owner and reconstruct the dependent work around that design. Current diff size cannot justify leaving the cause or rejected model in place. Keep unrelated improvements outside the task.

Preserved requirements constrain the design. Verification supplies evidence that the final affected system fulfills them. A successful procedure cannot replace that judgment.

## Establish the boundary

Use authoritative requirements to establish the target and the known change horizon. Use executable behavior to establish current implementation. A confirmed plan constrains the design but does not prove that it has been implemented.

When competing causes would require different fixes, inspect a case that distinguishes them. The first failing line and existing file boundaries do not establish the cause's owner. A repeated failure calls for investigating the common cause.

Follow the contract from its actual entry point through the owning responsibility and every affected consumer. Establish what state must survive. Required scope follows these dependencies rather than the current path inventory. Before choosing the boundary, establish what evidence could show that the proposed design fails its contract.

Preserve an earlier contract only for an evidenced consumer or state that cannot move with the change. Existing code and release status alone do not establish that need. Read [Compatibility boundaries](references/compatibility-boundaries.md) before retaining an earlier contract or introducing a transition mechanism.

If delivery must be incremental, make each step converge on the target structure without creating an accidental parallel model. An unavoidable external workaround belongs at the nearest affected boundary. Establish its external constraint and removal condition.

## Apply the model

This skill owns the software change boundary and the validity of verification evidence. Domain skills supply the constraints needed to choose that boundary. Repository guidance establishes local authority and executable requirements. Use `git-workflow` for Git operations.

When the task requires concrete implementation or verification decisions, read [Change execution and verification](references/change-verification.md). It governs dependency tracing through runtime paths and keeps final-state checks meaningful.

Before deciding the content or placement of repository guidance, read [Repository harness](references/repository-harness.md). Create such guidance only when inspected local facts need a durable owner. Follow the global approval requirement for `AGENTS.md` changes.

Scale the investigation to the requested judgment. A local change can have a brief model. Cross-boundary work needs enough evidence to choose the whole boundary before implementation. Do not turn the model into a mandatory report. Use single-agent self-review by default.
