import json
import threading
from datetime import datetime
from pathlib import Path

LOG_FILE = Path(__file__).resolve().parent.parent / "logs" / "audit.jsonl"

# One lock guards BOTH the id counter and the file, so only one thread
# at a time can be inside the critical section below.
_lock = threading.Lock()
_next_id = None  # loaded once from the file, then kept in memory


def _load_next_id():
    if not LOG_FILE.exists():
        return 1
    with open(LOG_FILE, encoding="utf-8") as f:
        return sum(1 for _ in f) + 1


def log_event(event, agent_id, role, **details):
    """Append one record to the audit log and return it. Thread-safe."""
    global _next_id

    with _lock:  # ---- critical section starts ----
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        if _next_id is None:
            _next_id = _load_next_id()

        record = {
            "id": _next_id,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "event": event,
            "agent_id": agent_id,
            "role": role,
            "details": details,
        }
        _next_id += 1

        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    # ---- critical section ends ----
    return record


def read_events(limit=None):
    """Return logged events as a list of dicts (newest last). Thread-safe."""
    with _lock:  # never read while a writer is mid-write
        if not LOG_FILE.exists():
            return []
        with open(LOG_FILE, encoding="utf-8") as f:
            events = [json.loads(line) for line in f if line.strip()]
    return events[-limit:] if limit else events