"""Install the committed harness into this user's Codex global configuration."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
HOME = Path.home() / ".codex"
INSTALL = HOME / "harness-v0"
VENV = INSTALL / "venv"
EVENTS = ("SessionStart", "UserPromptSubmit", "PostToolUse", "SubagentStart", "SubagentStop", "Stop")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_owned(target: Path, data: bytes, backup: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.read_bytes() != data:
        backup.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, backup / target.name)
    with tempfile.NamedTemporaryFile(dir=target.parent, prefix=f".{target.name}.", delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(data)
    temporary.replace(target)


def main() -> None:
    if not (ROOT / "source/harness_v0/always_on.py").is_file():
        raise SystemExit("missing always-on source")
    revision = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    if subprocess.check_output(["git", "-C", str(ROOT), "status", "--porcelain"], text=True).strip():
        raise SystemExit("commit the complete source before installing")
    INSTALL.mkdir(parents=True, exist_ok=True)
    if not (VENV / "bin/python").exists():
        subprocess.run([sys.executable, "-m", "venv", str(VENV)], check=True)
    subprocess.run([str(VENV / "bin/python"), "-m", "pip", "install", "--upgrade", str(ROOT)], check=True)
    command = f"{VENV / 'bin/python'} -m harness_v0.always_on"
    config = {"description": "Purpose-built SWE harness v0 global lifecycle", "hooks": {
        name: [{"hooks": [{"type": "command", "command": command, "timeout": 15,
                           "statusMessage": "SWE harness v0"}]}] for name in EVENTS}}
    backup = INSTALL / "backups" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    write_owned(HOME / "AGENTS.md", (ROOT / "runtime/global-AGENTS.md").read_bytes(), backup)
    write_owned(HOME / "hooks.json", (json.dumps(config, indent=2) + "\n").encode(), backup)
    installed = Path(subprocess.check_output([str(VENV / "bin/python"), "-c", "import harness_v0; print(harness_v0.__file__)"], text=True).strip()).parent
    modules = {}
    for name in ("core.py", "review.py", "completion.py", "cli.py", "always_on.py"):
        source_hash = sha(ROOT / "source/harness_v0" / name)
        installed_hash = sha(installed / name)
        if source_hash != installed_hash:
            raise SystemExit(f"installed module differs: {name}")
        modules[name] = source_hash
    report = {"revision": revision, "source_root": str(ROOT), "installed_package": str(installed),
              "modules": modules, "global_instructions": str(HOME / "AGENTS.md"),
              "global_hooks": str(HOME / "hooks.json"), "hooks_sha256": sha(HOME / "hooks.json"),
              "backup": str(backup) if backup.exists() else None}
    (INSTALL / "installation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
