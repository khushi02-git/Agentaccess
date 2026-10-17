import sys
import tempfile
import threading
import time
from collections import Counter
from pathlib import Path

import audit_log
import test_log_race
from access_matrix import acl, capabilities, format_matrix
from agent_monitor import monitor_agent
from audit_log import read_events
from scheduler_live import LiveScheduler, run_demo
from scheduler_sim import (
    gantt, make_pick_aging, pick_fcfs, pick_priority, simulate,
    starvation_example, worked_example,
)
from system_stats import get_system_stats

ROOT = Path(__file__).resolve().parent.parent
DEMO_LOG = ROOT / "logs" / "demo_audit.jsonl"


def use_demo_log(reset=True):
    """Record the whole demo in its own log file, so the summary at the end is clean."""
    DEMO_LOG.parent.mkdir(parents=True, exist_ok=True)
    if reset and DEMO_LOG.exists():
        DEMO_LOG.unlink()
    audit_log.LOG_FILE = DEMO_LOG
    audit_log._next_id = None


# ---------------------------------------------------------------------------
# 1. System monitoring
# ---------------------------------------------------------------------------
def section_system():
    stats = get_system_stats()
    ram = stats["ram"]
    print(f"CPU {stats['cpu_percent']}%    RAM {ram['used_gb']} / {ram['total_gb']} GB "
          f"({ram['percent']}%)    Disk {stats['disk']['percent']}%")
    print(f"\nTop processes by memory:\n  {'pid':>6}  {'name':<30}{'cpu %':>6}{'MB':>9}")
    for p in stats["processes"][:5]:
        print(f"  {p['pid']:>6}  {p['name']:<30}{p['cpu_percent']:>6}{p['memory_mb']:>9}")


# ---------------------------------------------------------------------------
# 2 and 3. Limits
# ---------------------------------------------------------------------------
def section_cpu():
    monitor_agent("agent_cpu", "read_only", stress="cpu", stress_after=3, duration=40)


def section_memory():
    monitor_agent("agent_mem", "read_only", stress="memory", stress_after=2, duration=30)


# ---------------------------------------------------------------------------
# 4. Protection
# ---------------------------------------------------------------------------
def section_access():
    print(format_matrix())
    print("\n* = enforced by the code today; the other cells are policy for the Docker phase\n")
    print("Column view (ACL) for 'process':       ", acl("process"))
    print("Row view (capabilities) of 'read_only':", capabilities("read_only"))

    print("\n-- An unknown role tries to submit a job --")
    sched = LiveScheduler(1, pick_priority, verbose=False)
    try:
        sched.submit("intruder", burst=2)
    except PermissionError as error:
        print("blocked:", error)
    sched.close()
    sched.wait_until_done()

    print("\n-- A read_only agent creates a child process --")
    monitor_agent("spawn_ro", "read_only", stress="spawn", stress_after=2, duration=8)

    print("\n-- An admin agent does the same --")
    monitor_agent("spawn_admin", "admin", stress="spawn", stress_after=2, duration=5)


# ---------------------------------------------------------------------------
# 5. Scheduling simulator
# ---------------------------------------------------------------------------
def brief(title, result):
    print(title)
    print(gantt(result["schedule"]))
    print(f"average waiting {result['avg_waiting']}, turnaround {result['avg_turnaround']}\n")


def section_simulator():
    reqs = worked_example()
    brief("FCFS:", simulate(reqs, pick_fcfs))
    brief("Priority (admin R3 jumps ahead of R2 and R4):", simulate(reqs, pick_priority))

    reqs = starvation_example()
    no_aging = simulate(reqs, pick_priority)
    aging = simulate(reqs, make_pick_aging(3))
    brief("Priority without aging (read_only request L starves):", no_aging)
    brief("Priority with aging:", aging)
    waited = lambda res: next(r["waiting"] for r in res["rows"] if r["name"] == "L")
    print(f"Request L waits {waited(no_aging)} time units without aging "
          f"and {waited(aging)} with aging.")


# ---------------------------------------------------------------------------
# 6. Live scheduler
# ---------------------------------------------------------------------------
def section_live():
    run_demo(slots=1, policy_name="aging")
    print("\n" + "-" * 60 + "\nSame requests, but the semaphore now allows 2 agents at once:\n")
    run_demo(slots=2, policy_name="aging")


# ---------------------------------------------------------------------------
# 7. Synchronization
# ---------------------------------------------------------------------------
def race_once(log_fn, threads=20, per_thread=25):
    audit_log.LOG_FILE = Path(tempfile.mkdtemp()) / "race.jsonl"
    audit_log._next_id = None

    def worker(n):
        for i in range(per_thread):
            log_fn("test", f"agent_{n}", "read_only", i=i)

    pool = [threading.Thread(target=worker, args=(n,)) for n in range(threads)]
    start = time.time()
    for t in pool:
        t.start()
    for t in pool:
        t.join()
    elapsed = time.time() - start
    return test_log_race.summarize(audit_log.LOG_FILE), elapsed, threads * per_thread


def show_race(label, summary, elapsed, expected):
    print(f"{label}")
    print(f"  expected {expected}, valid records {summary['valid']}, "
          f"corrupted lines {summary['corrupted']}")
    print(f"  duplicate IDs {summary['duplicates']}, IDs sequential {summary['sequential']}, "
          f"time {elapsed:.2f}s\n")


def section_race():
    demo_file = audit_log.LOG_FILE
    try:
        print("20 threads write 25 events each, at the same moment.\n")
        for attempt in range(1, 4):  # a race is random, so allow a few tries
            summary, elapsed, expected = race_once(test_log_race.unsafe_log_event)
            if summary["duplicates"] or summary["corrupted"] or attempt == 3:
                break
        show_race(f"WITHOUT a lock (original code), attempt {attempt}:", summary, elapsed, expected)
        summary, elapsed, expected = race_once(audit_log.log_event)
        show_race("WITH the mutex (fixed code):", summary, elapsed, expected)
    finally:
        audit_log.LOG_FILE = demo_file
        audit_log._next_id = None


# ---------------------------------------------------------------------------
# 8. Audit trail
# ---------------------------------------------------------------------------
def section_audit():
    events = read_events()
    if not events:
        print("No events yet. Run the other sections first.")
        return
    print(f"{len(events)} events, all written by the running code to {DEMO_LOG.name}\n")
    for name, count in sorted(Counter(e["event"] for e in events).items()):
        print(f"  {name:<17}{count}")

    print("\nViolations:")
    for e in events:
        if e["event"] == "violation":
            d = e["details"]
            print(f"  #{e['id']:<4}{e['agent_id']:<12}{e['role']:<10}{d['rule']:<20}"
                  f"{d['observed']} (limit {d['limit']})  -> {d['action']}")

    print("\nAccess decisions:")
    routine = 0
    for e in events:
        if not e["event"].startswith("access_"):
            continue
        d = e["details"]
        if e["event"] == "access_granted" and d["object"] == "scheduler":
            routine += 1  # every accepted job passes this check; not worth listing
            continue
        print(f"  #{e['id']:<4}{e['event']:<15}{e['agent_id']:<12}({e['role']}) "
              f"{d['object']}:{d['right']}")
    print(f"  (plus {routine} routine scheduler:submit grants, one per accepted job)")

    print("\nOne agent's life, read from the log (agent_cpu):")
    for e in events:
        if e["agent_id"] == "agent_cpu":
            d = {k: v for k, v in e["details"].items() if k not in ("limits", "unit")}
            print(f"  #{e['id']:<4}{e['timestamp'][11:]}  {e['event']:<16}{d}")

    ids = [e["id"] for e in events]
    print(f"\nIntegrity check, IDs unique and sequential: {ids == list(range(1, len(ids) + 1))}")


SECTIONS = [
    (1, "SYSTEM MONITORING",
     "Reads CPU, RAM, disk and the process table from the OS. (process concept, PID, process table)",
     section_system),
    (2, "LIMITS: CPU",
     "A read_only agent burns CPU. Its 5-second average breaks the budget: suspend, then terminate. "
     "(process states, operations on processes)",
     section_cpu),
    (3, "LIMITS: MEMORY",
     "Suspending frees the CPU but not the RAM, so the memory violation escalates right after resume.",
     section_memory),
    (4, "PROTECTION: ACCESS MATRIX",
     "Rights per role, default deny. Same behaviour, different verdict. "
     "(principles of protection, access matrix)",
     section_access),
    (5, "SCHEDULING SIMULATOR",
     "FCFS vs priority, and aging against starvation. (scheduling criteria, algorithms, Gantt charts)",
     section_simulator),
    (6, "LIVE SCHEDULER WITH REAL AGENT PROCESSES",
     "Producer-consumer queue, counting semaphore, same policies; live result vs the simulator's prediction.",
     section_live),
    (7, "SYNCHRONIZATION: WHY THE AUDIT LOG HAS A LOCK",
     "The same log writer without and with a mutex. (critical section, mutual exclusion)",
     section_race),
    (8, "AUDIT TRAIL",
     "Everything above was recorded by the code, not typed in.",
     section_audit),
]


def banner(number, title, caption):
    print("\n" + "=" * 72)
    print(f"  {number}. {title}")
    print(f"  {caption}")
    print("=" * 72 + "\n")


def main():
    args = sys.argv[1:]
    auto = "auto" in args
    only = {int(a) for a in args if a.isdigit()}
    chosen = [s for s in SECTIONS if not only or s[0] in only]

    # Section 8 only reads the log, so running it alone must not erase the last run
    use_demo_log(reset=[sec[0] for sec in chosen] != [8])
    print("Tip: add 'auto' to skip the pauses, or a section number (1-8) to run just that part.")
    total_start = time.time()
    try:
        for index, (number, title, caption, run) in enumerate(chosen):
            banner(number, title, caption)
            started = time.time()
            run()
            print(f"\n[section {number} took {time.time() - started:.0f}s]")
            if not auto and index < len(chosen) - 1:
                input("\nPress Enter for the next section... ")
    except KeyboardInterrupt:
        print("\nDemo interrupted. Any running agent was stopped.")
        return
    print(f"\nDemo finished in {time.time() - total_start:.0f}s. "
          f"Audit log: {DEMO_LOG}")


if __name__ == "__main__":
    main()