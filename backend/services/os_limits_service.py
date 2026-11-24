import sys
import threading
import time

import psutil

from backend.database import get_db_connection
from backend.services.os_monitor_service import OS_MONITOR_DIR, _load_os_module

# Share ONE audit_log instance with the rest of the backend (one lock, one id counter)
_audit = _load_os_module("agentaccess_os_audit_log", str(OS_MONITOR_DIR / "audit_log.py"))
sys.modules["audit_log"] = _audit
sys.path.insert(0, str(OS_MONITOR_DIR))

from limits import ROLE_LIMITS        # noqa: E402
from access_matrix import authorize   # noqa: E402

# DB role names -> OS role keys (copy the exact strings from your Roles INSERT)
ROLE_MAP = {"Admin": "admin", "Analyst": "writer", "ReadOnly": "read_only"}
MAX_CONCURRENT = {"admin": 3, "writer": 2, "read_only": 1}

_slots = {r: threading.BoundedSemaphore(n) for r, n in MAX_CONCURRENT.items()}
_suspended_until = {}
_state_lock = threading.Lock()


class AgentBlocked(Exception):
    """Access matrix said no."""


class AgentBusy(Exception):
    """Suspended or no free slot."""


def get_os_role(agent_id):
    conn = get_db_connection()
    if conn is None:
        return None
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT r.role_name FROM Agents a JOIN Roles r ON r.role_id = a.role_id "
            "WHERE a.agent_id = %s", (agent_id,))
        row = cur.fetchone()
        return ROLE_MAP.get(row[0]) if row else None
    finally:
        cur.close()
        conn.close()


def run_with_limits(agent_id, work):
    role = get_os_role(agent_id)
    if role is None:
        raise AgentBlocked("Unknown agent or role")
    limits = ROLE_LIMITS[role]

    if not authorize(f"agent_{agent_id}", role, "network", "connect_llm"):
        raise AgentBlocked(f"Role {role} may not call the LLM")

    with _state_lock:
        until = _suspended_until.get(agent_id, 0)
    if time.time() < until:
        raise AgentBusy(f"Agent suspended for {round(until - time.time())}s more")

    if not _slots[role].acquire(timeout=5):
        raise AgentBusy("Too many concurrent requests for this role")

    proc = psutil.Process()
    cpu_before = sum(proc.cpu_times()[:2])      # user + system seconds
    start = time.perf_counter()
    try:
        return work()
    finally:
        elapsed = max(time.perf_counter() - start, 0.001)
        cpu_pct = round((sum(proc.cpu_times()[:2]) - cpu_before) / elapsed * 100, 1)
        mem_mb = round(proc.memory_info().rss / 1024**2, 1)

        _audit.log_event("agent_request", agent_id, role,
                         duration_ms=round(elapsed * 1000),
                         cpu_percent=cpu_pct, memory_mb=mem_mb)

        broken = []
        if cpu_pct > limits["cpu_percent"]:
            broken.append(("cpu_sustained", cpu_pct, limits["cpu_percent"]))
        if mem_mb > limits["memory_mb"]:
            broken.append(("memory_ceiling", mem_mb, limits["memory_mb"]))
        for rule, observed, limit in broken:
            _audit.log_event("violation", agent_id, role, action="suspend",
                             rule=rule, observed=observed, limit=limit)
        if broken:
            with _state_lock:
                _suspended_until[agent_id] = time.time() + limits["suspend_seconds"]
            _audit.log_event("agent_suspended", agent_id, role,
                             seconds=limits["suspend_seconds"])

        _slots[role].release()                  # last, so the slot frees even on error