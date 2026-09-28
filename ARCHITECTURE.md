# Purpose-built Codex SWE Harness v0

This is a supervisory control layer around Codex's native execution. Codex still chooses and runs implementation tools. The harness owns task state, frozen review inputs, event provenance, and completion evaluation. Product files retain their own semantic ownership.

## Components and flow

`source/harness_v0/core.py` owns canonical state and append-only events. `review.py` projects a versioned evidence package, chooses rubric criteria, and validates structured results. `BuiltinSubagentAdapter` is a bridge to the native collaboration tool: the coordinator dispatches its returned request to a fresh subagent and records the native child ID and SHA-256 receipt. Python cannot independently instantiate a Codex child in the active desktop session. The transport interface is `SemanticReview`; a future separate invocation can implement the same contract. `completion.py` evaluates the parent task independent of worker topology. `cli.py` exposes local operations.

The dependency direction is task state → frozen package → reviewer finding → execution repair → verification → completion. Reviewer output cannot mutate the artifact. A native child identity is evidence of activation, not correctness. No model verdict alone marks a parent complete.

## Ownership and lifetime

Harness-owned transient state includes next work, blockers, delegation, review requests, and integration progress. Product-owned durable state includes architecture, API contracts, configuration, and deliverables. History-owned evidence includes prior decisions, supersession, and the event log. `artifact_context` declares owner and expected lifetime so the reviewer can detect F062-style leakage of temporary work status into durable design.

Source code is the current executable contract. `eval-results/` is generated history; its snapshots are evidence, not source. Old reviewer-isolation studies are historical evidence, with an unselected quality winner. Built-in review is the provisional v0 operating path because that study did not justify the cost of stronger isolation.

## Current Codex substrate

On this host, the harness is installed into `~/.codex/harness-v0/venv`; global `~/.codex/hooks.json` registers SessionStart, UserPromptSubmit, PostToolUse, SubagentStart, SubagentStop, and Stop. Global `~/.codex/AGENTS.md` gives the execution agent the ledger and review contract. The exact hook definition was trusted in the interactive Codex `/hooks` flow. Active ledgers live at `/private/tmp/harness-v0-sessions/<session_id>` and are mirrored to `~/.codex/harness-v0/archive/<session_id>` for continuation recovery. The Stop hook creates a frozen package and requests a fresh native reviewer through a model continuation; the SubagentStop hook ingests a structured result. Native non-review subagent dispatch/return is represented as delegated work. Official hook documentation specifies that non-managed hooks require trust and that Stop may request continuation.

Official sources: [Hooks](https://learn.chatgpt.com/docs/hooks), [plugin packaging](https://developers.openai.com/plugins/build/plugins), [multi-agent](https://developers.openai.com/api/docs/guides/agents-api/multi-agent).
