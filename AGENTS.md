# Harness repository development

The source of the installed harness is `source/harness_v0/`, `runtime/instructions/`, and `scripts/install_global.py`. Keep the ledger schema, lifecycle hooks, CLI, installer, and their contract tests aligned. `runtime/stop_hook.py` and `runtime/hooks.template.json` are isolated fixtures, not the active global entry point.

For changes that affect global consumers, follow the source → relevant tests → package/install → composed global instruction → active hook → fresh session path in `OPERATIONS.md`. Repository-only documents and fixtures need verification at their own consumer point. Installation is required when the managed global instruction or runtime changes, rather than for every edit to this repository.

Use `REVIEW-PROTOCOL.md` for frozen-package review and `COMPLETION.md` for the parent gate contract. Record actual evidence in the active ledger; these local documents describe the harness implementation, while general SWE judgment lives in the installed global instruction.
