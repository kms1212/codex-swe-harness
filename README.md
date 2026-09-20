# Codex SWE Harness

A user-global software engineering harness for Codex. It combines a small global routing policy with three focused skills for long-term software evolution, product UI work, and technical documentation.

## Contents

| Path | Responsibility |
| --- | --- |
| `global/AGENTS.md` | Global working rules, governance, permissions, skill routing, and completion discipline |
| `skills/software-evolution/` | Root-cause ownership, change boundaries, compatibility, migrations, verification, and repository harnesses |
| `skills/product-ui/` | Task-oriented information architecture, interaction semantics, accessibility, UI states, and anti-generic review |
| `skills/technical-documentation/` | Document types, temporal correctness, evidence semantics, narrative maintenance, and Korean technical writing |

`software-evolution` owns cross-domain change-boundary decisions. Relevant domain skills supply evidence, constraints, semantics, and techniques that inform those decisions before they are finalized; they do not replace its ownership.

## Requirements

The installer supports macOS and Linux with Bash 3.2 or newer and standard system utilities. It has no language-package dependencies. Native Windows is not supported because this installation model relies on POSIX symbolic links; see [the installation research](docs/installation-research.md) for the evidence and tradeoffs behind that scope.

Codex uses `~/.codex` by default. If `CODEX_HOME` is set, the installer and Codex use that directory instead. User skills are installed under `~/.agents/skills` unless `--skills-dir` selects another location.

## Install or update

Clone the repository to a location you intend to keep, review the global instructions and skills, then run:

```sh
./scripts/install.sh
```

The installer shows all targets and asks before changing them. For automation:

```sh
./scripts/install.sh --dry-run
./scripts/install.sh --yes
```

Installation creates symbolic links from the Codex user paths to this checkout:

| Target | Source |
| --- | --- |
| `$CODEX_HOME/AGENTS.md` (default `~/.codex/AGENTS.md`) | `global/AGENTS.md` |
| `~/.agents/skills/software-evolution` | `skills/software-evolution/` |
| `~/.agents/skills/product-ui` | `skills/product-ui/` |
| `~/.agents/skills/technical-documentation` | `skills/technical-documentation/` |

The source files in this repository remain the only content copies. Pulling an update into the same checkout updates the installed harness immediately. Running the installer again verifies the managed installation; if the checkout moved, it repoints links after checking ownership and creates a recovery backup.

Use explicit paths for a separate Codex profile or a test environment:

```sh
./scripts/install.sh \
  --codex-home /absolute/path/to/codex-home \
  --skills-dir /absolute/path/to/user-skills \
  --yes
```

Both overrides must be absolute. To relocate target directories after installation, uninstall with the original path options and install again with the new ones.

## Safety and recovery

The installer records only link ownership and source paths in `$CODEX_HOME/.codex-swe-harness/manifest.tsv`. It never merges or overwrites an existing `AGENTS.md`, skill directory, or changed managed target. A collision stops the full operation during preflight, before any target changes.

If an operation fails after changes begin, the installer rolls its managed links back. Updates that repoint links and uninstalls preserve the prior manifest under `$CODEX_HOME/.codex-swe-harness/backups/<timestamp>/manifest.tsv` and print that backup path.

Verify installed paths against their recorded repository sources:

```sh
./scripts/install.sh --check
```

Remove only links still owned by this installer:

```sh
./scripts/install.sh --uninstall
```

The checkout and recovery backup remain. Restore an uninstall while the original checkout is still available:

```sh
./scripts/install.sh --restore /absolute/path/to/backup-directory
```

To return to a backup made before a checkout relocation, first uninstall the current managed links, then restore that earlier backup. Restoration requires the repository path recorded in the backup to remain available; backups preserve link metadata, not repository contents.

`--uninstall` and `--restore` also accept `--dry-run` and `--yes`. If a user-owned file blocks installation, move or merge it manually; the installer intentionally has no force option.

Repository-specific facts, commands, architecture, terminology, and verification requirements belong in the closest applicable repository guidance. Do not copy project-specific rules into the global harness.

## Validation

Run the installer contract tests:

```sh
bash tests/install_test.sh
```

The tests cover dry-run behavior, exact source links, idempotent and relocated-checkout updates, unmanaged collisions, rollback after a partial failure, uninstall/restore, and externally changed managed targets. CI runs the same suite on macOS and Linux.

Codex installations that include the bundled skill validator can validate each skill with:

```sh
python "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" skills/software-evolution
python "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" skills/product-ui
python "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" skills/technical-documentation
```

Validation checks skill structure and frontmatter. It does not replace review of instruction ownership, reference routing, or behavioral quality.

## License

MIT. See [LICENSE](LICENSE).
