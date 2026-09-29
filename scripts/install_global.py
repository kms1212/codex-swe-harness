"""Install the committed harness into the current user's Codex configuration."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
EVENTS = ("SessionStart", "UserPromptSubmit", "PostToolUse", "SubagentStart", "SubagentStop", "Stop", "PermissionRequest")
START = "<!-- BEGIN purpose-built SWE harness v0 -->"
END = "<!-- END purpose-built SWE harness v0 -->"
LEGACY_SHA256 = "bac3fa94575a6e903310f67130225f31d11c9862ea924046ac3ca973deea2f67"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def os_fragment(system: str) -> str:
    fragments = {"Darwin": "macos.md", "Linux": "linux.md"}
    if system not in fragments:
        raise ValueError(f"unsupported host OS: {system}")
    return fragments[system]


def render_instructions(root: Path, system: str, revision: str) -> tuple[str, list[str]]:
    names = ["common.md", os_fragment(system)]
    parts = [(root / "runtime/instructions" / name).read_text(encoding="utf-8").strip() for name in names]
    return f"{START}\n<!-- revision: {revision}; host_os: {system}; fragments: {', '.join(names)} -->\n\n" + "\n\n".join(parts) + f"\n{END}\n", names


def merge_instructions(existing: str, managed: str) -> str:
    if existing.count(START) != existing.count(END) or existing.count(START) > 1:
        raise ValueError("malformed harness-managed global instructions")
    if START in existing:
        begin, end = existing.index(START), existing.index(END) + len(END)
        if begin > end:
            raise ValueError("malformed harness-managed global instructions")
        return existing[:begin] + managed.rstrip("\n") + existing[end:]
    if hashlib.sha256(existing.encode("utf-8")).hexdigest() == LEGACY_SHA256:
        return managed
    return existing.rstrip("\n") + ("\n\n" if existing.strip() else "") + managed


def write_owned(target: Path, data: bytes, backup: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.read_bytes() == data:
        return
    if target.exists():
        backup.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, backup / target.name)
    with tempfile.NamedTemporaryFile(dir=target.parent, prefix=f".{target.name}.", delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(data)
    temporary.replace(target)


def install(root: Path = ROOT, codex_home: Path | None = None, system: str | None = None) -> dict:
    codex_home = codex_home or Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    system = system or platform.system()
    if not (root / "source/harness_v0/always_on.py").is_file():
        raise ValueError("missing always-on source")
    revision = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    if subprocess.check_output(["git", "-C", str(root), "status", "--porcelain"], text=True).strip():
        raise ValueError("commit the complete source before installing")
    managed, fragments = render_instructions(root, system, revision)
    install_dir = codex_home / "harness-v0"
    venv = install_dir / "venv"
    install_dir.mkdir(parents=True, exist_ok=True)
    python = venv / ("Scripts/python.exe" if system == "Windows" else "bin/python")
    if not python.exists():
        subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
    subprocess.run([str(python), "-m", "pip", "install", "--upgrade", str(root)], check=True, stdout=sys.stderr)
    command = f"{python} -m harness_v0.always_on"
    config = {"description": "Purpose-built SWE harness v0 global lifecycle", "hooks": {
        name: [{"hooks": [{"type": "command", "command": command, "timeout": 15,
                           "statusMessage": "SWE harness v0"}]}] for name in EVENTS}}
    backup = install_dir / "backups" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    global_path = codex_home / "AGENTS.md"
    existing = global_path.read_text(encoding="utf-8") if global_path.exists() else ""
    merged = merge_instructions(existing, managed)
    write_owned(global_path, merged.encode("utf-8"), backup)
    write_owned(codex_home / "hooks.json", (json.dumps(config, indent=2) + "\n").encode(), backup)
    installed = Path(subprocess.check_output([str(python), "-c", "import harness_v0; print(harness_v0.__file__)"], text=True).strip()).parent
    modules = {}
    for source_file in sorted((root / "source/harness_v0").glob("*.py")):
        name = source_file.name
        if sha(source_file) != sha(installed / name):
            raise ValueError(f"installed module differs: {name}")
        modules[name] = sha(source_file)
    actual = global_path.read_text(encoding="utf-8")
    if managed.rstrip("\n") not in actual:
        raise ValueError("global instructions verification failed")
    report = {"revision": revision, "source_root": str(root), "installed_package": str(installed),
              "modules": modules, "host_os": system, "instruction_fragments": fragments,
              "global_instructions": str(global_path), "instructions_sha256": sha(global_path),
              "global_hooks": str(codex_home / "hooks.json"), "hooks_sha256": sha(codex_home / "hooks.json"),
              "backup": str(backup) if backup.exists() else None}
    (install_dir / "installation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    print(json.dumps(install(), indent=2))


if __name__ == "__main__":
    main()
