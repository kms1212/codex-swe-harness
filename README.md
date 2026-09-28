# Purpose-built Codex SWE harness v0

This repository contains the globally installed Codex SWE harness v0. The Python package owns a canonical task ledger, append-only events, frozen review packages, native child-review activation records, and a parent completion gate. It does not call an external model API.

Run the contract tests from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=source python3 -m unittest discover -s tests -v
```

The active global install is managed by `scripts/install_global.py`. In ordinary Codex sessions, lifecycle hooks bind natural-language requests to a ledger and capture native tool evidence; the user need not run the CLI. See [OPERATIONS.md](OPERATIONS.md) for installation and recovery. [ARCHITECTURE.md](ARCHITECTURE.md), [STATE-SCHEMA.md](STATE-SCHEMA.md), [REVIEW-PROTOCOL.md](REVIEW-PROTOCOL.md), and [COMPLETION.md](COMPLETION.md) specify the contracts.

[V0-ACCEPTANCE.md](V0-ACCEPTANCE.md) records the release decision and limitations. [EVALUATION.md](EVALUATION.md) explains the challenge set; [eval-results/](eval-results/) contains raw and indexed evidence. The historical study excerpt and F063 fixture needed by the evaluation scripts are preserved under `eval-results/prior-evidence/`.
