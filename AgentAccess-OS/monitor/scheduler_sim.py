from dataclasses import dataclass

from limits import ROLE_PRIORITY


@dataclass
class Request:
    name: str
    role: str
    arrival: int
    burst: int
    priority: int


def make_request(name, role, arrival, burst):
    """Build a request; its priority comes from the role."""
    return Request(name, role, arrival, burst, ROLE_PRIORITY[role])


# ---------------------------------------------------------------------------
# POLICIES: each one answers only "which waiting request goes next?"
# `ready` arrives already ordered by arrival time (then name), so when two
# requests tie, the one found first in the scan is the one that arrived first.
# ---------------------------------------------------------------------------
def pick_fcfs(ready, now):
    """First come, first served: the head of the queue."""
    return ready[0]


def pick_sjf(ready, now):
    """Shortest job first: scan for the smallest burst time."""
    chosen = ready[0]
    for r in ready:
        if r.burst < chosen.burst:  # strictly smaller, so ties keep the earlier arrival
            chosen = r
    return chosen


def pick_priority(ready, now):
    """Priority: scan for the most important request (lowest number)."""
    chosen = ready[0]
    for r in ready:
        if r.priority < chosen.priority:
            chosen = r
    return chosen


def make_pick_aging(interval):
    """Priority with aging: every `interval` time units waited improves a request by one level."""

    def effective_priority(r, now):
        waited = now - r.arrival
        return r.priority - waited // interval

    def pick(ready, now):
        chosen = ready[0]
        for r in ready:
            if effective_priority(r, now) < effective_priority(chosen, now):
                chosen = r
        return chosen

    return pick


# ---------------------------------------------------------------------------
# MECHANISM: runs the requests one at a time (non-preemptive), using any policy
# ---------------------------------------------------------------------------
def simulate(requests, pick):
    pending = sorted(requests, key=lambda r: (r.arrival, r.name))
    now = 0
    schedule = []  # list of (name, start, end)
    timing = {}    # name -> (start, end)

    while pending:
        ready = [r for r in pending if r.arrival <= now]
        if not ready:
            now = min(r.arrival for r in pending)  # server idle until next arrival
            continue
        chosen = pick(ready, now)
        pending.remove(chosen)
        start, end = now, now + chosen.burst
        schedule.append((chosen.name, start, end))
        timing[chosen.name] = (start, end)
        now = end

    rows = []
    for r in requests:
        start, end = timing[r.name]
        turnaround = end - r.arrival
        rows.append({
            "name": r.name, "role": r.role, "arrival": r.arrival,
            "burst": r.burst, "priority": r.priority,
            "start": start, "end": end,
            "waiting": turnaround - r.burst,
            "turnaround": turnaround,
            "response": start - r.arrival,
        })

    n = len(rows)
    span = max(r["end"] for r in rows) - min(r["arrival"] for r in rows)
    busy = sum(r["burst"] for r in rows)
    return {
        "schedule": schedule,
        "rows": rows,
        "avg_waiting": round(sum(r["waiting"] for r in rows) / n, 2),
        "avg_turnaround": round(sum(r["turnaround"] for r in rows) / n, 2),
        "avg_response": round(sum(r["response"] for r in rows) / n, 2),
        "throughput": round(n / span, 3),
        "utilization": round(100 * busy / span, 1),
    }


# ---------------------------------------------------------------------------
# OUTPUT
# ---------------------------------------------------------------------------
def gantt(schedule, scale=3):
    """Draw the schedule as text: bars on the first line, time marks on the second."""
    end_time = schedule[-1][2]
    bar = [" "] * (end_time * scale + 1)
    ticks = [" "] * (end_time * scale + 6)

    for name, start, end in schedule:
        a, b = start * scale, end * scale
        bar[a] = "|"
        bar[b] = "|"
        label = name[: b - a - 1]
        mid = a + 1 + (b - a - 1 - len(label)) // 2
        for i, ch in enumerate(label):
            bar[mid + i] = ch
        for t, pos in ((start, a), (end, b)):
            text = str(t)
            if all(ticks[pos + i] == " " for i in range(len(text))):
                for i, ch in enumerate(text):
                    ticks[pos + i] = ch

    return "".join(bar).rstrip() + "\n" + "".join(ticks).rstrip()


def report(title, result):
    print(f"=== {title} ===")
    print(gantt(result["schedule"]))
    print(f"\n{'req':<5}{'role':<11}{'arr':>4}{'burst':>6}{'prio':>5}"
          f"{'start':>6}{'end':>5}{'wait':>6}{'turn':>6}{'resp':>6}")
    for r in result["rows"]:
        print(f"{r['name']:<5}{r['role']:<11}{r['arrival']:>4}{r['burst']:>6}{r['priority']:>5}"
              f"{r['start']:>6}{r['end']:>5}{r['waiting']:>6}{r['turnaround']:>6}{r['response']:>6}")
    print(f"\naverage waiting {result['avg_waiting']}, turnaround {result['avg_turnaround']}, "
          f"response {result['avg_response']}")
    print(f"throughput {result['throughput']} jobs/unit, utilization {result['utilization']}%\n")


# ---------------------------------------------------------------------------
# EXAMPLES
# ---------------------------------------------------------------------------
def worked_example():
    return [
        make_request("R1", "read_only", 0, 6),
        make_request("R2", "writer", 1, 3),
        make_request("R3", "admin", 2, 2),
        make_request("R4", "read_only", 3, 4),
    ]


def starvation_example():
    reqs = [
        make_request("X", "admin", 0, 4),
        make_request("L", "read_only", 1, 3),  # the low-priority victim
    ]
    for i, arrival in enumerate([2, 4, 6, 8, 10], start=1):
        reqs.append(make_request(f"A{i}", "admin", arrival, 3))
    return reqs


if __name__ == "__main__":
    reqs = worked_example()
    print("WORKED EXAMPLE\n")
    report("FCFS", simulate(reqs, pick_fcfs))
    report("SJF (non-preemptive)", simulate(reqs, pick_sjf))
    report("Priority (non-preemptive)", simulate(reqs, pick_priority))

    print("\nSTARVATION EXAMPLE (admin requests keep arriving)\n")
    reqs = starvation_example()
    report("Priority, no aging", simulate(reqs, pick_priority))
    report("Priority with aging (every 3 units)", simulate(reqs, make_pick_aging(3)))