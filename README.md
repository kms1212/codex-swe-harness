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

## Installation

Review the files before installing them. They are personal workflow policy and should be merged with existing user-global instructions rather than blindly overwriting unrelated rules.

For a fresh skill installation:

```sh
mkdir -p ~/.agents/skills
cp -R skills/software-evolution ~/.agents/skills/
cp -R skills/product-ui ~/.agents/skills/
cp -R skills/technical-documentation ~/.agents/skills/
```

For a fresh global-instructions installation:

```sh
mkdir -p ~/.codex
cp global/AGENTS.md ~/.codex/AGENTS.md
```

If either destination already exists, compare and merge the files instead of running the corresponding copy command.

Repository-specific facts, commands, architecture, terminology, and verification requirements belong in the closest applicable repository guidance. Do not copy project-specific rules into the global harness.

## Validation

Codex installations that include the bundled skill validator can validate each skill with:

```sh
python "$CODEX_HOME/skills/.system/skill-creator/scripts/quick_validate.py" skills/software-evolution
python "$CODEX_HOME/skills/.system/skill-creator/scripts/quick_validate.py" skills/product-ui
python "$CODEX_HOME/skills/.system/skill-creator/scripts/quick_validate.py" skills/technical-documentation
```

Validation checks skill structure and frontmatter. It does not replace review of instruction ownership, reference routing, or behavioral quality.

## License

MIT. See [LICENSE](LICENSE).
