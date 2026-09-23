# Installation design research

This note records the installation approaches considered for the repository. It is decision evidence, not an installation guide; current commands and behavior are documented in the [README](../README.md).

Research was checked on 2026-09-21 against project-owned documentation and repositories.

## Compared approaches

| Project or authority | Observed approach | Decision for this repository |
| --- | --- | --- |
| [OpenAI: Build skills](https://developers.openai.com/codex/skills/) | Codex discovers user skills in `$HOME/.agents/skills` and follows symlinked skill directories. OpenAI recommends plugins for distributing reusable bundles. | Adopt the documented user skill location and symlinks. Do not use a plugin as the only installer because this harness also owns a user-global `AGENTS.md`, which the plugin bundle does not install. |
| [OpenAI: Custom instructions with AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md) | Codex reads global guidance from `CODEX_HOME/AGENTS.md`, with `~/.codex` as the default home. | Adopt `CODEX_HOME/AGENTS.md` as the instruction target and expose `--codex-home` for explicit profiles and tests. |
| [OpenAI skill installer](https://github.com/openai/skills/blob/main/skills/.system/skill-installer/SKILL.md) | The installer downloads or sparse-checks out skills and aborts when a destination already exists. | Adopt collision refusal. Reject copied payloads here because the checkout's skill and instruction files must remain the single source of truth. |
| [Superpowers](https://github.com/obra/superpowers#installation) | Current releases prefer each harness's native plugin or package manager; older OpenCode installation used a clone plus symlinks and now has an explicit migration procedure. | Adopt a harness-specific install path and explicit recovery procedure. Do not introduce a package-manager dependency for the local links. |
| [GitHub Spec Kit installation](https://github.com/github/spec-kit/blob/main/docs/installation.md) | A versioned CLI provides explicit integration selection, `--non-interactive`, verification, updates, and platform-specific script choices. Existing non-empty destinations require an explicit force acknowledgement. | Adopt explicit non-interactive operation (`--yes`), `--dry-run`, verification, and documented platform scope. Reject `--force`: this installer can avoid overwriting user content entirely. |
| [GSD installer and user guide](https://github.com/gsd-build/get-shit-done/blob/main/docs/USER-GUIDE.md) | The installer distinguishes runtime and global/local destinations, supports flag-only automation, and backs up locally modified files during updates. | Adopt flag-only automation and recovery records. Do not merge or patch local destination files: unmanaged content remains untouched, while managed paths are links to the checkout. |

## Resulting boundary

The checkout is the content owner. Installation creates five absolute symlinks and a small ownership manifest under `CODEX_HOME/.codex-swe-harness/`. The manifest contains paths only; it does not copy instruction or skill content.

Manifests from the earlier four-link layout remain valid update inputs. The installer verifies those four owned links, refuses an occupied `git-workflow` target, backs up the old manifest, adds the fifth link, and writes the current layout. Check mode requires the current five-link layout, while uninstall and restore continue to honor either recorded layout so recovery remains exact.

A missing manifest means a new installation. Any occupied target is then an unmanaged collision and stops the operation during preflight. A valid manifest means an update. Updates may repair missing managed links or repoint links after the repository moves, but they stop if a managed target was replaced outside the installer.

Every update that changes link metadata and every uninstall stores the previous manifest in the backup directory. All targets are preflighted before mutation. If a link operation fails after mutation begins, the installer restores the earlier managed links before exiting.

## Platform decision

The implementation targets macOS and Linux with Bash 3.2 or newer and standard userland commands (`mkdir`, `ln`, `readlink`, `rm`, `mv`, `cp`, `date`, and `dirname`). The script deliberately avoids GNU-only flags so the same path runs under macOS's system Bash and common Linux distributions. The repository test workflow exercises both `macos-latest` and `ubuntu-latest`.

Native Windows is not claimed. The design depends on POSIX symlink and shell behavior, while Windows symlink permissions and semantics vary. A future PowerShell implementation should provide the same manifest, collision, rollback, and verification contracts rather than silently falling back to copies.
