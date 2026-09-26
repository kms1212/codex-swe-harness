# Current Tool Mapping

This mapping records the Codex runtime observed on 2026-09-26. Active tool descriptions are authoritative when they differ from this reference.

## Same multi-agent tree

The collaboration runtime exposes `spawn_agent`, `send_message`, `followup_task`, `wait_agent`, `list_agents`, and `interrupt_agent`.

- A child agent's final response is delivered to its parent mailbox, so the parent can use push mode for that response.
- `send_message` delivers information to an existing agent but does not itself create a new turn.
- `followup_task` sends a request and triggers a turn when the target is idle.
- `wait_agent` observes mailbox updates and terminal state; it is the pull mechanism when automatic parent delivery is insufficient.
- Tool availability does not authorize spawning, delegation, interruption, or ownership transfer.

## Independent Codex tasks

The desktop runtime can expose `list_threads`, `read_thread`, `send_message_to_thread`, `wait_threads`, `create_thread`, `fork_thread`, `handoff_thread`, and `get_handoff_status`.

- An independent task's final response is not automatically returned to the origin. Default to pull with `read_thread` or `wait_threads`.
- `send_message_to_thread` is a conditional push route only when the requested user-visible message is authorized and the receiver can treat it as the required delivery.
- `wait_threads` uses cursors to avoid redelivering already observed final text and is preferred for compact progress observation.
- `create_thread` may return a `clientThreadId` while setup is pending. That identifier is not a usable task ID for tools requiring `threadId`.
- `handoff_thread` relocates execution and associated Git state. Use `get_handoff_status` to observe the operation; relocation does not establish semantic ownership transfer.

## Availability check

Before choosing a route, confirm that the relevant tool is active in the current runtime and read its current contract. If a required response path cannot be verified, do not dispatch response-dependent work.
