# Purpose-built Codex SWE harness

A local supervisory harness for Codex: ordered user requests and current interpretation, scoped verification reuse, execution-time semantic review, proven scratch cleanup and a strong parent completion gate. Codex chooses and executes work; users give ordinary requests. No external model API is used.

Run source checks with `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=source python3 -m unittest discover -s tests -v`. [OPERATIONS.md](OPERATIONS.md) describes source installation and native consumer verification. [ARCHITECTURE.md](ARCHITECTURE.md), [STATE-SCHEMA.md](STATE-SCHEMA.md), [REVIEW-PROTOCOL.md](REVIEW-PROTOCOL.md) and [COMPLETION.md](COMPLETION.md) own current contracts.

Historical release evidence is in [history/initial-acceptance.md](history/initial-acceptance.md) and `eval-results/`. It describes earlier candidates, not current acceptance. Native reviewer isolation is instruction-level; Python scheduling depends on Codex dispatch. Persistent hook trust and live behavior must be verified separately from source tests.
