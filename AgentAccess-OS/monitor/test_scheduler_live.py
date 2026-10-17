import json
import tempfile
import time
from pathlib import Path

import audit_log
from scheduler_live import LiveScheduler, peak_concurrency
from scheduler_sim import pick_priority


def use_temp_log():
    """Send audit records to a throwaway file so tests don't touch the real log."""
    audit_log.LOG_FILE = Path(tempfile.mkdtemp()) / "audit.jsonl"
    audit_log._next_id = None


def read_log():
    with open(audit_log.LOG_FILE, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def test_semaphore_never_exceeds_cap():
    use_temp_log()
    sched = LiveScheduler(max_agents=2, pick=pick_priority, verbose=False)
    for i in range(6):
        sched.submit("admin", burst=1, name=f"T{i}")
    sched.close()
    sched.wait_until_done()

    results = sched.results()
    assert len(results) == 6 
    assert all(r["outcome"] == "completed" for r in results)   # ...and succeeded                     # every job ran
    assert peak_concurrency(results) == 2         # the cap was reached, never exceeded


def test_priority_order_among_waiting_jobs():
    use_temp_log()
    sched = LiveScheduler(max_agents=1, pick=pick_priority, verbose=False)
    sched.submit("read_only", burst=3, name="A")  # starts immediately, holds the slot
    time.sleep(0.5)
    sched.submit("read_only", burst=1, name="B")  # these three queue up
    sched.submit("writer", burst=1, name="C")
    sched.submit("admin", burst=1, name="D")
    sched.close()
    sched.wait_until_done()

    order = [r["name"] for r in sched.results()]
    assert order == ["A", "D", "C", "B"]          # admin, then writer, then read_only


def test_audit_log_is_complete_and_sequential():
    use_temp_log()
    sched = LiveScheduler(max_agents=2, pick=pick_priority, verbose=False)
    for i in range(4):
        sched.submit("writer", burst=1, name=f"L{i}")
    sched.close()
    sched.wait_until_done()

    events = read_log()
    ids = [e["id"] for e in events]
    assert ids == list(range(1, len(ids) + 1))    # no duplicates, no gaps
    for kind in ("job_submitted", "job_started", "job_finished"):
        assert sum(1 for e in events if e["event"] == kind) == 4
    for i in range(4):                            # per job: submitted, then started, then finished
        mine = [e["event"] for e in events
                if e["agent_id"] == f"L{i}" and e["event"].startswith("job_")]
        assert mine == ["job_submitted", "job_started", "job_finished"]


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for t in tests:
        t()
        print(f"passed: {t.__name__}")
    print(f"\nall {len(tests)} tests passed")