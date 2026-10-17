import sys
import time
from collections import deque
from statistics import mean
from access_matrix import authorize

from agent_tracker import AgentTracker, start_agent
from audit_log import log_event, read_events
from limits import ROLE_LIMITS


def check_limits(sample, cpu_history, limits):
    """Compare one sample with the role's limits. Returns a list of violations."""
    violations = []

    # CPU is a rate: judge the average over the window, not one spike
    cpu_history.append(sample["cpu_percent"])
    if len(cpu_history) == cpu_history.maxlen:
        avg = round(mean(cpu_history), 1)
        if avg > limits["cpu_percent"]:
            violations.append({
                "rule": "cpu_sustained",
                "observed": avg,
                "limit": limits["cpu_percent"],
                "unit": "% of 1 core, averaged",
            })

    # Memory is a level: any single sample over the ceiling counts
    if sample["memory_mb"] > limits["memory_mb"]:
        violations.append({
            "rule": "memory_ceiling",
            "observed": sample["memory_mb"],
            "limit": limits["memory_mb"],
            "unit": "MB",
        })

    return violations


def monitor_agent(agent_id, role, stress="none", stress_after=10, duration=50,
                  verbose=True):
    """Run one agent process under its role's limits. Returns a summary dict."""

    def say(text):
        if verbose:
            print(text)

    limits = ROLE_LIMITS[role]
    popen = start_agent(agent_id, role, stress, stress_after)
    tracker = AgentTracker(popen)
    cpu_history = deque(maxlen=limits["window_seconds"])

    log_event("agent_started", agent_id, role, pid=popen.pid, limits=limits)
    say(f"Started {agent_id} (role={role}, PID {popen.pid}, stress={stress})")
    say(f"Limits: CPU avg > {limits['cpu_percent']}% over {limits['window_seconds']}s, "
        f"memory > {limits['memory_mb']} MB")
    say(f"Policy: strike 1 = suspend {limits['suspend_seconds']}s, "
        f"strike {limits['max_strikes']} = terminate")
    say(f"{'sec':>4} {'CPU %':>7} {'RAM MB':>8}  state")

    outcome = "completed"
    strikes = 0
    resume_at = None  # when set, the agent is currently suspended
    baseline_procs = None  # how many processes the agent normally consists of

    try:
        for second in range(1, duration + 1):
            time.sleep(1)
            if popen.poll() is not None:
                outcome = "exited_on_its_own"
                break

            sample = tracker.sample()
            say(f"{second:>4} {sample['cpu_percent']:>7} {sample['memory_mb']:>8}  "
                f"{tracker.status()}")

            # While suspended we only wait; no checks, no violations
            if resume_at is not None:
                if time.time() >= resume_at:
                    tracker.resume()
                    cpu_history.clear()  # old readings belong to before the freeze
                    resume_at = None
                    log_event("agent_resumed", agent_id, role, pid=popen.pid)
                    say("          -> agent resumed")
                continue


                        # Access check: did the agent create a process it is not allowed to create?
            if baseline_procs is None:
                baseline_procs = sample["process_count"]
            elif sample["process_count"] > baseline_procs:
                if authorize(agent_id, role, "process", "spawn", pid=popen.pid,
                             processes_before=baseline_procs,
                             processes_now=sample["process_count"]):
                    baseline_procs = sample["process_count"]  # allowed: new normal
                else:
                    log_event("violation", agent_id, role, pid=popen.pid,
                              action="terminate", rule="unauthorized_spawn",
                              observed=sample["process_count"], limit=baseline_procs,
                              unit="processes")
                    say(f"VIOLATION: unauthorized_spawn ({baseline_procs} -> "
                        f"{sample['process_count']} processes). Action: terminate.")
                    outcome = "terminated_by_monitor"
                    break

            violations = check_limits(sample, cpu_history, limits)
            if not violations:
                continue

            strikes += 1
            final = strikes >= limits["max_strikes"]
            action = "terminate" if final else "suspend"
            for v in violations:
                log_event("violation", agent_id, role, pid=popen.pid,
                          action=action, strike=strikes, **v)
                say(f"VIOLATION (strike {strikes}): {v['rule']} = {v['observed']} "
                    f"{v['unit']} (limit {v['limit']}). Action: {action}.")

            if final:
                outcome = "terminated_by_monitor"
                break

            tracker.suspend()
            resume_at = time.time() + limits["suspend_seconds"]
            log_event("agent_suspended", agent_id, role, pid=popen.pid,
                      seconds=limits["suspend_seconds"], strike=strikes)
    finally:
        tracker.stop()
        log_event("agent_stopped", agent_id, role, outcome=outcome)
        say(f"Agent stopped. Outcome: {outcome}")

    return {"outcome": outcome, "strikes": strikes}


def show_recent_events(count=8):
    print("\nLast events in the audit log:")
    for e in read_events(limit=count):
        print(f"  #{e['id']} {e['timestamp']} {e['event']:<15} "
              f"{e['agent_id']} ({e['role']}) {e['details']}")


if __name__ == "__main__":
    role = sys.argv[1] if len(sys.argv) > 1 else "read_only"
    stress = sys.argv[2] if len(sys.argv) > 2 else "cpu"
    monitor_agent("agent_demo", role, stress=stress)
    show_recent_events()