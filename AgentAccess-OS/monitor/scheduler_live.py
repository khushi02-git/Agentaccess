import sys
import threading
import time
from dataclasses import dataclass
from access_matrix import authorize

from agent_monitor import monitor_agent
from audit_log import log_event
from limits import ROLE_PRIORITY
from scheduler_sim import (
    gantt, make_pick_aging, make_request, pick_fcfs, pick_priority, pick_sjf, simulate,
)


@dataclass
class LiveJob:
    name: str
    role: str
    arrival: float      # seconds since the scheduler started
    burst: int          # how many seconds the agent is allowed to run
    priority: int
    stress: str = "none"
    stress_after: int = 10


class LiveScheduler:
    """Queue + policy + semaphore + real agent processes, all in one object."""

    def __init__(self, max_agents, pick, verbose=True):
        self.max_agents = max_agents
        self.verbose = verbose
        self.pick = pick
        self.slots = threading.Semaphore(max_agents)   # counting semaphore: free slots
        self.cond = threading.Condition()              # lock + wait/notify for the queue
        self.waiting = []                              # jobs, in arrival order
        self.closed = False
        self.t0 = time.monotonic()
        self._results = []
        self._results_lock = threading.Lock()
        self._print_lock = threading.Lock()
        self._workers = []
        self._count = 0
        self._dispatcher = threading.Thread(target=self._dispatch_loop, daemon=True)
        self._dispatcher.start()

    def now(self):
        return time.monotonic() - self.t0

    def _say(self, text):
        if not self.verbose:
            return
        with self._print_lock:                         # keep lines from mixing
            print(f"[t={self.now():5.1f}s] {text}")

    # ----- producer side -------------------------------------------------
    def submit(self, role, burst, stress="none", stress_after=10, name=None):
        if not authorize(name or role, role, "scheduler", "submit"):
            raise PermissionError(f"role {role!r} may not submit jobs")
        with self.cond:
            self._count += 1
            job = LiveJob(name or f"J{self._count}", role, self.now(), burst,
                          ROLE_PRIORITY[role], stress, stress_after)
            self.waiting.append(job)
            # Log and print INSIDE the critical section, before waking the dispatcher,
            # so the audit trail's order matches what really happened.
            log_event("job_submitted", job.name, role, burst=burst,
                      priority=job.priority, stress=stress)
            self._say(f"submitted {job.name} ({role}, burst {burst}s)  "
                      f"queue: {[j.name for j in self.waiting]}")
            self.cond.notify()                         # wake the dispatcher
        return job

    def close(self):
        with self.cond:
            self.closed = True
            self.cond.notify_all()

    def wait_until_done(self):
        self._dispatcher.join()
        for w in self._workers:
            w.join()

    # ----- consumer side -------------------------------------------------
    def _dispatch_loop(self):
        while True:
            self.slots.acquire()                       # 1. wait for a free slot
            with self.cond:                            # 2. wait for a job to exist
                while not self.waiting and not self.closed:
                    self.cond.wait()
                if not self.waiting:                   # closed and nothing left
                    self.slots.release()
                    return
                queue_names = [j.name for j in self.waiting]
                job = self.pick(self.waiting, self.now())   # 3. choose at the last moment
                self.waiting.remove(job)
            self._say(f"dispatch {job.name} ({job.role})  chose from {queue_names}")
            worker = threading.Thread(target=self._run_job, args=(job,))
            self._workers.append(worker)
            worker.start()

    def _run_job(self, job):
        start = self.now()
        log_event("job_started", job.name, job.role,
                  waited_seconds=round(start - job.arrival, 1))
        outcome = "error"
        try:
            summary = monitor_agent(job.name, job.role, stress=job.stress,
                                    stress_after=job.stress_after,
                                    duration=job.burst, verbose=False)
            outcome = summary["outcome"]
        finally:
            end = self.now()
            with self._results_lock:
                self._results.append({
                    "name": job.name, "role": job.role, "arrival": job.arrival,
                    "start": start, "end": end, "planned_burst": job.burst,
                    "outcome": outcome,
                })
            log_event("job_finished", job.name, job.role, outcome=outcome,
                      ran_seconds=round(end - start, 1))
            self._say(f"finished {job.name} ({job.role}): {outcome}")
            self.slots.release()                       # LAST: only now may the next job start

    def results(self):
        with self._results_lock:
            return sorted(self._results, key=lambda r: r["start"])


def peak_concurrency(results):
    """Largest number of jobs that were running at the same moment."""
    peak = 0
    for r in results:
        running = sum(1 for o in results if o["start"] <= r["start"] < o["end"])
        peak = max(peak, running)
    return peak


# ---------------------------------------------------------------------------
# DEMO
# ---------------------------------------------------------------------------
POLICIES = {
    "fcfs": pick_fcfs,
    "sjf": pick_sjf,
    "priority": pick_priority,
    "aging": make_pick_aging(3),
}

# (name, role, planned arrival in seconds, burst in seconds)
WORKED_EXAMPLE = [
    ("J1", "read_only", 0, 6),
    ("J2", "writer", 1, 3),
    ("J3", "admin", 2, 2),
    ("J4", "read_only", 3, 4),
]


def run_demo(slots=1, policy_name="aging", with_stress=False):
    plan = list(WORKED_EXAMPLE)
    stress_by_name = {}
    if with_stress:
        plan.append(("J5", "read_only", 4, 16))
        stress_by_name["J5"] = ("memory", 1)

    pick = POLICIES[policy_name]
    print(f"Live run: {slots} slot(s), policy = {policy_name}"
          f"{', with a memory-stress job (J5)' if with_stress else ''}\n")

    sched = LiveScheduler(slots, pick)
    for name, role, arrival, burst in plan:           # the producer: this main thread
        time.sleep(max(0.0, arrival - sched.now()))
        stress, stress_after = stress_by_name.get(name, ("none", 10))
        sched.submit(role, burst, stress, stress_after, name=name)
    sched.close()
    sched.wait_until_done()

    results = sched.results()
    print(f"\n{'job':<5}{'role':<11}{'arrive':>7}{'start':>7}{'end':>7}"
          f"{'waited':>8}{'planned':>8}  outcome")
    for r in results:
        print(f"{r['name']:<5}{r['role']:<11}{r['arrival']:>7.1f}{r['start']:>7.1f}"
              f"{r['end']:>7.1f}{r['start'] - r['arrival']:>8.1f}"
              f"{r['planned_burst']:>8}  {r['outcome']}")
    avg_wait = sum(r["start"] - r["arrival"] for r in results) / len(results)
    print(f"\naverage waiting {avg_wait:.2f}s")
    print(f"peak concurrency {peak_concurrency(results)} (semaphore cap was {slots})")

    if slots == 1:
        predicted = simulate([make_request(n, ro, a, b) for n, ro, a, b in plan], pick)
        actual = [(r["name"], round(r["start"]), round(r["end"])) for r in results]
        print("\nPREDICTED by the simulator (Step 3a):")
        print(gantt(predicted["schedule"]))
        print("\nACTUAL from the live run:")
        print(gantt(actual))
        same = [n for n, _, _ in predicted["schedule"]] == [n for n, _, _ in actual]
        print(f"\nsame order as predicted: {same}")


if __name__ == "__main__":
    args = sys.argv[1:]
    slots = next((int(a) for a in args if a.isdigit()), 1)
    policy = next((a for a in args if a in POLICIES), "aging")
    run_demo(slots, policy, with_stress="stress" in args)