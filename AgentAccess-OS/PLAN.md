# AgentAccess: OS Monitoring Module

**Owner:** Member 3 (OS monitoring, logging, dashboard)
**Status as of:** 2026-10-10 (Phase 1 complete)
**Location:** `AgentAccess-OS/` (Python, separate from the React frontend)

---

## 1. Purpose and scope

AI agents are untrusted: they can be wrong or be manipulated (for example by prompt injection). Gemini itself runs on Google's servers, so we cannot control it. What we can control is the **agent runner**, the program on our machine that holds the API key, calls Gemini, and executes approved database operations.

This module covers the **OS layer** of AgentAccess:

1. **Monitor** CPU, RAM, disk and running processes, system-wide and per agent.
2. **Limit** each agent's resource use according to its role.
3. **Record** what happened (starts, violations, stops) in an append-only audit log.

**Out of scope for this module:** query validation and permissions (Member 1), authentication (Member 2), the API itself (FastAPI member). We provide data and functions to them.

## 2. Where it fits

```
React Dashboard  -->  FastAPI Backend  -->  MySQL (DBMS)
                            |
                            +-->  Gemini (validation / AI)
                            +-->  OS module (this repo): psutil monitoring,
                                   agent runner, limits, audit log
```

React cannot read CPU, RAM or processes itself. This module runs on the machine, collects the data, and the backend serves it to the dashboard.

## 3. Phases and status

| Phase | What | Status |
|---|---|---|
| A | System-wide stats with `psutil` | Done, verified against Task Manager |
| B | Stats returned as dictionaries (the JSON shape in 5.1) | Done |
| C | Dummy agent as a separate process, tracked by PID (including child processes) | Done |
| D | Per-role limits, sustained-threshold check, enforcement (terminate), violation records | Done |
| E | Per-request tracking around Gemini calls (query, decision, tokens, latency) | Planned |
| F | Docker/cgroups hard limits (`--cpus`, `--memory`), network and file restrictions | Planned (Docker not installed yet) |
| G | FastAPI endpoints and live dashboard pages | Planned (Phase 2 integration) |

**Phase 1 decision:** the OS module runs standalone and the frontend uses dummy data in the same shape. Integration comes in Phase 2.

## 4. Requirements

| ID | Requirement | Status |
|---|---|---|
| R1 | Report CPU %, RAM, disk % and top processes | Done |
| R2 | Report CPU and RAM for one agent, identified by PID, including its child processes | Done |
| R3 | Each role has a resource budget stored as configuration | Done |
| R4 | CPU is judged on a moving average (ignores single spikes); memory on a hard ceiling | Done |
| R5 | A violation terminates the agent and is recorded | Done |
| R6 | Every start, violation and stop is written to an append-only log by the running code (not entered by hand) | Done |
| R7 | Agent actions (query, decision, tokens, latency) are logged per request | Phase E |
| R8 | Hard limits and isolation through containers | Phase F |
| R9 | Data available over HTTP for the dashboard | Phase G |

## 5. Data contracts

These shapes are what the backend and frontend should rely on.

### 5.1 System stats (system-wide)

Produced by `get_system_stats()` in `monitor/system_stats.py`.

```json
{
  "cpu_percent": 43.2,
  "ram": { "total_gb": 15.7, "used_gb": 9.2, "percent": 59.0 },
  "disk": { "percent": 70.1 },
  "timestamp": "2026-10-10T14:31:43",
  "processes": [
    { "pid": 3148, "name": "Code.exe", "cpu_percent": 1.6, "memory_mb": 426.7 }
  ]
}
```

- `cpu_percent` (top level and in `processes`) is **% of the whole CPU**.
- `processes` holds the top 10 by memory.
- Timestamps are ISO 8601, local time, to the second.

### 5.2 Agent sample (one agent, one moment)

Produced by `AgentTracker.sample()` in `monitor/agent_tracker.py`.

```json
{ "pid": 11824, "process_count": 2, "cpu_percent": 80.4, "memory_mb": 20.1 }
```

- `cpu_percent` here is **% of ONE core** (100 = one full core). This differs from 5.1 on purpose, because Docker's `--cpus` uses the same unit.
- `process_count` is 2 on Windows because the virtual environment's `python.exe` launches the real interpreter. Values are summed across both.

### 5.3 Role limits

Defined in `monitor/limits.py`.

```python
ROLE_LIMITS = {
    "read_only": {"cpu_percent": 40, "memory_mb": 300,  "window_seconds": 5},
    "writer":    {"cpu_percent": 80, "memory_mb": 600,  "window_seconds": 5},
    "admin":     {"cpu_percent": 90, "memory_mb": 1500, "window_seconds": 5},
}
```

- `cpu_percent`: limit on the **average** of the last `window_seconds` samples.
- `memory_mb`: ceiling checked on **every** sample.
- Role names and values are placeholders until they are aligned with the roles in the DBMS schema.

### 5.4 Audit log record

Written by `log_event()` in `monitor/audit_log.py` to `logs/audit.jsonl` (JSON Lines: one record per line, append-only).

```json
{
  "id": 2,
  "timestamp": "2026-10-10T15:05:48",
  "event": "violation",
  "agent_id": "agent_demo",
  "role": "read_only",
  "details": {
    "pid": 11824,
    "action": "terminate",
    "rule": "cpu_sustained",
    "observed": 53.9,
    "limit": 40,
    "unit": "% of 1 core, averaged"
  }
}
```

**Event types in use now:**

| `event` | `details` fields |
|---|---|
| `agent_started` | `pid`, `limits` |
| `violation` | `pid`, `action`, `rule`, `observed`, `limit`, `unit` |
| `agent_stopped` | `outcome` (`completed`, `terminated_by_monitor`, `exited_on_its_own`) |

**Violation rules:** `cpu_sustained`, `memory_ceiling`.

**Proposed for Phase E (needs agreement with the team):** `agent_request` with `details`: `query`, `decision` (allowed/blocked), `status`, `tokens`, `duration_ms`, and the validation result from the DBMS member.

## 6. Interface for teammates

**Functions the backend can import:**

| Function | Returns |
|---|---|
| `get_system_stats()` | the dictionary in 5.1 |
| `read_events(limit=None)` | list of log records (5.4), newest last |
| `monitor_agent(agent_id, role, ...)` | runs and monitors one agent until it finishes or breaks a limit |

**Proposed endpoints (not yet agreed with the FastAPI member):**

| Endpoint | Returns |
|---|---|
| `GET /api/system/stats` | 5.1 |
| `GET /api/events` | list of 5.4 records, with optional `?event=violation` filter |
| `GET /api/health` | already exists on the backend |

**Notes for integration:**

- `get_system_stats()` takes about 2 seconds because it samples CPU over time. For the API it should run in a background task that refreshes a cached value, so the endpoint answers instantly.
- The frontend runs on port 5173 and the API on 8000, so the backend needs CORS enabled for the dashboard.
- The Gemini API key must live only in the backend, as an environment variable, never in React code.
- The log file is read whole on each call. That is fine for a demo, and a database table would replace it later.

## 7. How the dashboard uses it

| Dashboard page | Data source |
|---|---|
| System Monitor | 5.1 system stats (CPU, RAM, disk, processes), polled every few seconds |
| Agents | `agent_started` and `agent_stopped` events, plus 5.2 samples |
| Logs | all events |
| Audit Trail | all events as a timeline |
| Violations | events where `event == "violation"` |
| Dashboard | summary counts from the above, plus the latest events |

## 8. Known limitations

- **Soft limits are reactive.** The monitor checks once per second, so an agent can overshoot briefly (observed: terminated at 320 MB against a 300 MB limit). Hard limits in Phase F prevent this.
- **The agent is simulated in Phase 1.** `dummy_agent.py` fakes Gemini calls and has a stress mode so limits can be demonstrated. The stress is deliberate, not Gemini's own load.
- **Per-agent CPU attribution is approximate** if processes are shared.
- **One writer assumed.** Log IDs come from counting lines, which is fine for one process and not for many.
- **Windows:** `terminate()` is an immediate stop. Docker runs through WSL2.

## 9. Open questions to confirm with the team

1. Who writes the real agent runner (the program that calls Gemini), and how does the backend start it?
2. Do the role names and budgets in 5.3 match the DBMS roles?
3. Is the log record in 5.4 acceptable, and where should violations from query validation (Member 1) be recorded: in the same log or in MySQL?
4. Does the FastAPI member import this module or call it another way?
5. Should audit records move to MySQL in Phase 2?

## 10. How to run (Phase 1)

From `AgentAccess-OS`, with the virtual environment active (`venv\Scripts\activate`):

```
python monitor\system_stats.py                  # system-wide stats (JSON)
python monitor\agent_tracker.py cpu             # track one agent (cpu or memory stress)
python monitor\agent_monitor.py read_only cpu   # full demo: limits, violation, log
python monitor\agent_monitor.py writer cpu      # same stress, allowed for this role
```

Log output goes to `logs\audit.jsonl`.