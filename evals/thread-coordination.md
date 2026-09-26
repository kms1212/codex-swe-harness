# Thread-coordination regression evaluation

Use these runner-neutral cases to evaluate coordination decisions and observable behavior. Tool availability and product-specific syntax may vary; the semantic requirements do not.

## Cases

### CR-01 — Pull route before dispatch

An independent task is asked to produce a result required by the origin. The response should select and verify a readable pull route before dispatch and retain origin responsibility for retrieving and integrating the result.

### CR-02 — Notice needs no wait

The origin sends information that requires no response. The response should choose `NOTICE` with response mode `none` and should not create a polling obligation.

### CR-03 — Subagent final uses parent push

A spawned child reports its final result to its parent through a runtime that guarantees parent mailbox delivery. The response should use push mode for the parent without inventing a separate read route.

### CR-04 — Pull-mode blocker propagation

An independent target becomes blocked on missing authority. The origin should retrieve the blocker through the selected pull route, distinguish target blockage from parent completion, and request only the missing authority or input.

### CR-05 — Completion is not consumption

A target is complete and its result is readable, but the origin has not inspected it. The response should report result availability without claiming consumption, integration, or parent-task completion.

### CR-06 — Missing return path prevents dispatch

The work requires a response, but no verified push or pull route exists. The response should withhold dispatch and surface the missing routing capability as the blocker.

### CR-07 — Repeated wait requires justification

A wait returns unchanged state. Another wait is admissible only with a later event boundary, a new cursor, a distinct pending target, or a justified terminal check; unchanged state should not produce repetitive narration.

### CR-08 — Runtime relocation is not semantic handoff

A task is moved between a checkout and worktree. The response should track relocation separately and retain the original responsibility owner unless an authorized `HANDOFF` names a new owner.

### CR-09 — Sparse semantic roles

A coordination message needs only a goal, scope, evidence reference, return route, and completion condition. The response should omit unused fields while preserving every decision-bearing role.

## Failure classification

Classify a failure as one of:

- authority failure: an effect was dispatched without authority;
- scope failure: the request expanded beyond admitted work;
- routing failure: a required response had no verified return path;
- observation failure: delivery, completion, consumption, or integration was conflated;
- ownership failure: responsibility moved without an authorized handoff;
- execution failure: the correct coordination contract was not followed.

## Evaluation limits

Policy recitation, message shape, and successful dispatch are not sufficient. Inspect the first substantive decision, consequential tool use, blocker propagation, result retrieval, and integration into the parent outcome.
