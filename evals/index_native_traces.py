"""Index native child transcripts without copying private session internals."""
import hashlib
import json
from pathlib import Path

from harness_v0.core import canonical_bytes

ROOT = Path(__file__).resolve().parents[1]
SESSIONS = Path("/Users/kms1212/.codex/sessions/2026/09/28")
PARENT_ID = "01a0e746-040e-7263-82bb-41ec904d41b3"


def main():
    parent = next(SESSIONS.glob(f"*{PARENT_ID}.jsonl"))
    rows = []
    for line in parent.read_text().splitlines():
        event = json.loads(line)
        payload = event.get("payload", {})
        item = payload.get("item", {}) if isinstance(payload, dict) else {}
        if item.get("type") != "SubAgentActivity" or item.get("kind") != "started":
            continue
        thread_id = item.get("agent_thread_id")
        files = list(SESSIONS.glob(f"*{thread_id}.jsonl"))
        for path in files:
            rows.append({"agent_path": item.get("agent_path"), "thread_id": thread_id,
                         "trace_path": str(path), "trace_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                         "parent_event_ordinal": event.get("ordinal")})
    out = ROOT / "eval-results" / "raw-traces" / "native-trace-index.jsonl"
    out.write_bytes(b"".join(canonical_bytes(row) for row in rows))
    print(json.dumps({"native_child_traces": len(rows), "parent_trace": str(parent)}))


if __name__ == "__main__":
    main()
