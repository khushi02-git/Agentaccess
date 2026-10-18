import json
import re
import threading
from datetime import datetime
from pathlib import Path

from backend.database import get_db_connection

AUDIT_LOG_FILE = Path(__file__).resolve().parents[1] / "audit_logs.jsonl"
MAX_QUERY_LENGTH = 4000
MAX_MESSAGE_LENGTH = 2000
_jsonl_lock = threading.Lock()
_next_event_id = None

_SENSITIVE_VALUE = re.compile(
    r"""(?i)\b(password|passwd|api[_-]?key|token|secret)\b\s*[:=]\s*
    (?:'[^']*'|"[^"]*"|[^\s,;]+)""",
    re.VERBOSE,
)
_BEARER_TOKEN = re.compile(r"(?i)\bBearer\s+\S+")


def _safe_text(value: str | None, max_length: int) -> str | None:
    if value is None:
        return None
    sanitized = _SENSITIVE_VALUE.sub(r"\1=[REDACTED]", value)
    sanitized = _BEARER_TOKEN.sub("Bearer [REDACTED]", sanitized)
    if len(sanitized) > max_length:
        return sanitized[:max_length] + "...[truncated]"
    return sanitized


def append_audit_event(
    event_type: str,
    status: str,
    *,
    agent_id: int | None = None,
    role: str | None = None,
    action: str | None = None,
    query: str | None = None,
    risk_level: str | None = None,
    message: str | None = None,
    request_id: int | None = None,
) -> dict:
    """Append a sanitized AgentAccess event to the JSONL audit stream."""
    global _next_event_id

    with _jsonl_lock:
        AUDIT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        if _next_event_id is None:
            if AUDIT_LOG_FILE.exists():
                with AUDIT_LOG_FILE.open(encoding="utf-8") as log_file:
                    _next_event_id = sum(1 for line in log_file if line.strip()) + 1
            else:
                _next_event_id = 1

        event = {
            "id": _next_event_id,
            "timestamp": datetime.now().astimezone().isoformat(timespec="microseconds"),
            "source": "AgentAccess",
            "event_type": event_type,
            "event": event_type,
            "agent_id": agent_id,
            "role": role,
            "action": action,
            "query": _safe_text(query, MAX_QUERY_LENGTH),
            "status": status,
            "risk_level": risk_level,
            "message": _safe_text(message, MAX_MESSAGE_LENGTH),
            "request_id": request_id,
            "details": {},
        }
        with AUDIT_LOG_FILE.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(event, ensure_ascii=True) + "\n")
        _next_event_id += 1
        return event


def read_agentaccess_events() -> list[dict]:
    """Read AgentAccess JSONL events; malformed records are surfaced to callers."""
    with _jsonl_lock:
        if not AUDIT_LOG_FILE.exists():
            return []
        events = []
        with AUDIT_LOG_FILE.open(encoding="utf-8") as log_file:
            for line_number, line in enumerate(log_file, start=1):
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError as error:
                    raise ValueError(
                        f"Malformed AgentAccess audit event at line {line_number}"
                    ) from error
                if (
                    not isinstance(event, dict)
                    or type(event.get("id")) is not int
                    or not isinstance(event.get("timestamp"), str)
                    or not isinstance(event.get("event"), str)
                    or not isinstance(event.get("event_type"), str)
                    or not isinstance(event.get("source"), str)
                ):
                    raise ValueError(
                        f"Malformed AgentAccess audit event at line {line_number}"
                    )
                events.append(event)
        return events


def create_audit_log(
    agent_id: int,
    request_id: int | None,
    action: str,
    result: str,
    details: str
):
    connection = get_db_connection()

    if connection is None:
        return False

    cursor = connection.cursor()

    try:
        query = """
            INSERT INTO Audit_Logs
            (agent_id, request_id, action, result, details)
            VALUES (%s, %s, %s, %s, %s)
        """

        cursor.execute(
            query,
            (
                agent_id,
                request_id,
                action,
                result,
                details
            )
        )

        connection.commit()

        return True

    except Exception as e:
        print(f"Audit log error: {e}")
        connection.rollback()
        return False

    finally:
        cursor.close()
        connection.close()