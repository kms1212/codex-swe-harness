"""Audit source, isolated install, active hook, native reviewer, and behavior."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENV = Path("/tmp/codex-swe-harness-v0-rc")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    installed_root = Path(subprocess.check_output([str(VENV / "bin" / "python"), "-c", "import harness_v0; print(harness_v0.__file__)"], text=True).strip()).parent
    modules = {}
    for name in ("core.py", "review.py", "completion.py", "cli.py"):
        source = ROOT / "source" / "harness_v0" / name
        installed = installed_root / name
        modules[name] = {"source_sha256": sha(source), "installed_sha256": sha(installed), "matched": sha(source) == sha(installed)}
    hook_events = [json.loads(line) for line in (ROOT / "eval-results" / "raw-traces" / "isolated-hook-continuation-events.jsonl").read_text().splitlines()]
    active_hook = [event for event in hook_events if event["kind"] == "stop_hook_evaluated"]
    controlled = [json.loads(line) for line in (ROOT / "eval-results" / "run-index.jsonl").read_text().splitlines()] if (ROOT / "eval-results" / "run-index.jsonl").exists() else []
    latest_turn = active_hook[-1]["data"].get("turn_id") if active_hook else None
    latest_turn_events = [event for event in active_hook if event["data"].get("turn_id") == latest_turn]
    no_work_events = [json.loads(line) for line in (ROOT / "eval-results" / "raw-traces" / "isolated-hook-no-work-events.jsonl").read_text().splitlines()]
    no_work_evaluations = [event for event in no_work_events if event["kind"] == "stop_hook_evaluated"]
    no_work_latest_turn = no_work_evaluations[-1]["data"].get("turn_id") if no_work_evaluations else None
    no_work_latest_turn_events = [event for event in no_work_evaluations if event["data"].get("turn_id") == no_work_latest_turn]
    no_work_agent_messages = [json.loads(line) for line in (ROOT / "eval-results" / "raw-traces" / "isolated-hook-no-work.jsonl").read_text().splitlines() if json.loads(line).get("type") == "item.completed" and json.loads(line).get("item", {}).get("type") == "agent_message"]
    report = {"source_to_install_match": all(row["matched"] for row in modules.values()), "modules": modules,
              "installed_entrypoint": str(VENV / "bin" / "harness-v0"), "active_hook_evaluations": len(active_hook),
              "active_hook_continued_once": len(latest_turn_events) == 2,
              "active_hook_without_work_item_continued_once": len(no_work_latest_turn_events) == 2 and len(no_work_agent_messages) == 2,
              "active_native_review_cases": len([row for row in controlled if row.get("kind") == "controlled" and row.get("case_id", "").startswith("v2_")]),
              "installed_completion_result": json.loads((ROOT / "eval-results" / "raw-traces" / "installed-completion.json").read_text()),
              "current_parent_completion_result": json.loads((ROOT / "eval-results" / "raw-traces" / "current-parent-completion.json").read_text()) if (ROOT / "eval-results" / "raw-traces" / "current-parent-completion.json").exists() else None}
    out = ROOT / "eval-results" / "source-to-runtime.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
