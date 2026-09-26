---
name: thread-coordination
description: Coordinate already-authorized work across Codex tasks, threads, or subagents. Use for cross-thread requests, delegation, steering, handoffs, result retrieval, blocker propagation, and waits. This skill does not authorize creating threads, spawning agents, transferring ownership, or expanding task scope.
---

# Thread Coordination

## Governing outcome

Preserve the parent task contract when authorized work crosses a task, thread, or subagent boundary. Before dispatch, establish whether a response is required and verify its return path.

Track target completion, result availability, route readability, delivery, origin consumption, and integration as separate facts. A target can finish before its result is available to the origin, and delivery does not establish that the origin consumed or integrated it.

Preserve the semantic class and provenance of material claims across the boundary. Forwarding, repetition, and target completion do not turn an inference, preference, decision, unknown, or user-reported observation into a verified fact.

Loading this skill grants no authority to create a thread, spawn or delegate to an agent, mutate local or external state, expand scope, or transfer ownership.

## Responsibility

This skill owns request semantics, response requirements, return-path selection, result and blocker propagation, result consumption, wait admissibility, failure classification, and compact coordination messages.

Global governance owns mode, scope, authority, approvals, and stop boundaries. `software-evolution` owns engineering boundaries. `git-workflow` owns Git state. Domain skills own their subject judgments.

The origin retains responsibility for the parent outcome unless an explicitly authorized `HANDOFF` transfers named ownership. Runtime relocation alone is not semantic ownership transfer.

## Coordination state

Track only the distinctions needed by the task:

- target state: accepted, working, blocked, failed, or complete;
- result state: absent or available;
- route state: unreadable, readable, or delivered;
- origin state: unconsumed, consumed, or integrated.

Request delivery, target execution, and response observation are independent events. State each one only when evidence establishes it.

## Coordination acts

Use the act that matches the requested effect:

- `ASK`: request analysis or information without transferring execution ownership;
- `DO`: request execution within stated scope and authority;
- `STEER`: update an active request while preserving unaffected terms;
- `REPORT`: return result, evidence, uncertainty, or status;
- `BLOCK`: return a blocker and the exact input or authority needed;
- `HANDOFF`: transfer named responsibility when separately authorized;
- `NOTICE`: send information with no response requirement.

## Sparse message grammar

Use only fields that change the receiver's decision:

```text
<ACT> [req=<id>]
goal=
scope=
authority=
change=
preserve=
ref=
evidence=
fact=
infer=
requirement=
decision=
preference=
result=
unknown=
block=
need=
return=
done=
```

These fields represent task and goal, scope, authority, steering delta, preservation duties, references and evidence, facts, inferences, requirements, decisions, preferences, result, uncertainty, blocker or requested input, response routing, and completion. Omit empty roles rather than filling a template mechanically.

## Preserve epistemic roles

Use epistemic fields only when the distinction changes the receiver's decision. A `fact` carries its evidence provenance and validity scope when those matter. An `infer` remains an inference until the receiver verifies it. A user-reported observation travels as attributed `evidence`; any proposed cause travels separately as `infer`. User-controlled outcomes travel as `requirement`, and admissible choices or preferences travel as `decision` or `preference`.

Do not relabel a claim merely to simplify a message. The receiver evaluates a reported claim against the parent task's evidence and authority rather than treating the sender's confidence or completion status as validation.

## Response modes

Choose one response mode before dispatch:

- **push**: the runtime reliably delivers the target response to the origin;
- **pull**: the origin has a verified read or wait operation and remains responsible for invoking it;
- **none**: no response is required, as with a pure notice.

If a response is required and neither push nor pull is verified, dispatch is inadmissible. Read [Current tool mapping](references/current-tool-mapping.md) before selecting a route from runtime-specific tools.

## Dispatch decision

Before dispatch:

1. Confirm that cross-thread coordination and the requested effect are authorized.
2. Identify the exact target and the work it already owns or may receive.
3. Choose the coordination act.
4. State goal, admitted scope, authority, preservation duties, material claim types, and completion condition at the precision the target needs.
5. Decide whether a response is required.
6. Select and verify push, pull, or none.
7. Record how blockers and uncertainty return.
8. Dispatch only when the origin can observe every required terminal state.

## Target behavior

Interpret the message inside the stated authority and scope. Preserve omitted terms from the active request when handling `STEER`. Return `BLOCK` when the next required action needs missing information, authority, or approval.

For a completed request, return the result, evidence, material facts and inferences, remaining uncertainty, and completion status through the selected route. Preserve user requirements, decisions, and preferences as their own roles. Do not imply parent-task completion unless the origin assigned that judgment.

## Origin behavior

In pull mode, perform the promised read or wait until the required terminal state is observable or a genuine stop boundary occurs. In push mode, verify that the runtime actually delivered the response before relying on it.

Consume the result by checking identity, scope, claim types, evidence provenance, validity scope, uncertainty, and preservation obligations. Integrate only the portion that remains valid under the parent contract. A child or target report is evidence, not automatic acceptance, and its inference does not become a fact without an admissible epistemic update.

## Wait admissibility

A wait is admissible when a required result is outstanding and the runtime can still change the observable state. Repeating a wait requires a later state, a new cursor or event boundary, a distinct pending target, or a justified terminal check. Unchanged state alone is not a blocker and does not justify narration.

## Boundary examples

- A subagent whose final response is automatically returned to its parent can use push mode for that parent; a sibling still needs a verified route.
- An independent Codex task normally requires pull through a read or wait operation unless a documented tool provides verified delivery.
- Sending a user-visible message to another task is a side effect and requires its own authority even when coordination is otherwise allowed.
- Moving a runtime task between a checkout and worktree changes execution location; it does not transfer semantic responsibility without an authorized `HANDOFF`.
