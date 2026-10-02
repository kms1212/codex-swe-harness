"""Index frozen packages, validated results, and event streams with content hashes."""
import hashlib
import json
import shutil
from pathlib import Path

from harness.core import canonical_bytes

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "eval-results"


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    traces = OUT / "raw-traces"
    traces.mkdir(parents=True, exist_ok=True)
    rows = []
    for case in sorted((OUT / "controlled").iterdir()):
        if not case.is_dir():
            continue
        events = case / "events.jsonl"
        if not events.exists():
            continue
        copy = traces / f"{case.name}-events.jsonl"
        shutil.copyfile(events, copy)
        packages = [path for path in sorted(case.glob("*review-*.json")) if not path.name.startswith("review-result") and path.name != "repair-review-result.json"]
        rows.append({"kind": "controlled", "case_id": case.name, "events": str(copy.relative_to(ROOT)), "events_sha256": file_hash(copy),
                     "packages": [{"path": str(path.relative_to(ROOT)), "sha256": file_hash(path)} for path in packages],
                     "results": [{"path": str(path.relative_to(ROOT)), "sha256": file_hash(path)} for path in sorted(case.glob("*result*.json"))]})
    for case in sorted((OUT / "real-work").iterdir()) if (OUT / "real-work").exists() else []:
        events = case / "events.jsonl"
        if events.exists():
            copy = traces / f"{case.name}-events.jsonl"
            shutil.copyfile(events, copy)
            rows.append({"kind": "real-work", "case_id": case.name, "events": str(copy.relative_to(ROOT)), "events_sha256": file_hash(copy),
                         "packages": [{"path": str(path.relative_to(ROOT)), "sha256": file_hash(path)} for path in sorted(case.glob(f"{case.name}-review-*.json"))],
                         "results": [{"path": str(path.relative_to(ROOT)), "sha256": file_hash(path)} for path in sorted(case.glob("review-result-*.json"))]})
    for path in [OUT / "raw-traces" / "fresh-reruns.jsonl", OUT / "raw-traces" / "native-trace-index.jsonl", OUT / "raw-traces" / "installed-create.json", OUT / "raw-traces" / "installed-completion.json", OUT / "raw-traces" / "current-parent-completion.json", OUT / "raw-traces" / "installed-cli-risk-smoke.json", OUT / "raw-traces" / "isolated-hook-final.jsonl", OUT / "raw-traces" / "isolated-hook-continuation-events.jsonl", OUT / "raw-traces" / "isolated-hook-no-work.jsonl", OUT / "raw-traces" / "isolated-hook-no-work-events.jsonl", OUT / "raw-traces" / "source-tests-final.txt", OUT / "raw-traces" / "installed-tests-final.txt", OUT / "raw-traces" / "install-final.txt", OUT / "completion-set-audit.json", OUT / "completion-set-audit-current.json", OUT / "source-to-runtime.json", OUT / "controlled" / "score.json", ROOT / "evals" / "observed-results.jsonl"]:
        if path.exists():
            rows.append({"kind": "supporting", "path": str(path.relative_to(ROOT)), "sha256": file_hash(path)})
    (OUT / "run-index.jsonl").write_bytes(b"".join(canonical_bytes(row) for row in rows))
    print(json.dumps({"indexed": len(rows), "controlled": sum(row["kind"] == "controlled" for row in rows), "real_work": sum(row["kind"] == "real-work" for row in rows)}))


if __name__ == "__main__":
    main()
