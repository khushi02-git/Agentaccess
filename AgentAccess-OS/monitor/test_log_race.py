import json
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path

import audit_log

THREADS = 20
PER_THREAD = 50


def unsafe_log_event(event, agent_id, role, **details):
    """The ORIGINAL version: no lock, and the id is computed from the file."""
    log_file = audit_log.LOG_FILE
    log_file.parent.mkdir(parents=True, exist_ok=True)

    next_id = 1
    if log_file.exists():
        with open(log_file, encoding="utf-8") as f:
            next_id = sum(1 for _ in f) + 1

    record = {
        "id": next_id,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "event": event,
        "agent_id": agent_id,
        "role": role,
        "details": details,
    }
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return record


def summarize(path):
    """Read a log file and report how healthy it is. Never crashes on bad lines."""
    ids = []
    corrupted = 0
    lines = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            lines += 1
            try:
                ids.append(json.loads(line)["id"])
            except (json.JSONDecodeError, KeyError):
                corrupted += 1  # a torn write: two records mixed into one line
    return {
        "lines": lines,
        "valid": len(ids),
        "corrupted": corrupted,
        "duplicates": len(ids) - len(set(ids)),
        "sequential": ids == list(range(1, len(ids) + 1)),
    }


def run(log_fn, label):
    audit_log.LOG_FILE = Path(tempfile.mkdtemp()) / "audit.jsonl"
    audit_log._next_id = None  # reset the in-memory counter

    def worker(n):
        for i in range(PER_THREAD):
            log_fn("test", f"agent_{n}", "read_only", i=i)

    threads = [threading.Thread(target=worker, args=(n,)) for n in range(THREADS)]
    start = time.time()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed = time.time() - start

    s = summarize(audit_log.LOG_FILE)
    expected = THREADS * PER_THREAD
    print(f"{label}")
    print(f"  expected records     : {expected}")
    print(f"  valid records        : {s['valid']}")
    print(f"  corrupted lines      : {s['corrupted']}")
    print(f"  duplicate IDs        : {s['duplicates']}")
    print(f"  IDs are 1..N         : {s['sequential']}")
    print(f"  time                 : {elapsed:.2f}s\n")


if __name__ == "__main__":
    print(f"{THREADS} threads x {PER_THREAD} events each\n")
    run(unsafe_log_event, "WITHOUT lock (original code)")
    run(audit_log.log_event, "WITH lock (fixed code)")