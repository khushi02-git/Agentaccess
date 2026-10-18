from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from backend.schemas import OSEventsResponse, SystemStatsResponse
from backend.services.audit_service import read_agentaccess_events
from backend.services.os_monitor_service import (
    MalformedAuditLogError,
    os_monitor_service,
)

router = APIRouter(tags=["OS Monitoring"])


def _event_timestamp(event: dict) -> datetime:
    timestamp = datetime.fromisoformat(event["timestamp"])
    return timestamp.astimezone() if timestamp.tzinfo is None else timestamp


@router.get("/api/system/stats", response_model=SystemStatsResponse)
def get_system_stats():
    stats = os_monitor_service.get_cached_system_stats()
    if stats is None:
        raise HTTPException(
            status_code=503,
            detail="System metrics are not available until the first refresh succeeds",
        )
    return stats


@router.get("/api/events", response_model=OSEventsResponse)
def get_os_events(
    limit: int = Query(default=100, ge=1, le=1000),
    event: str | None = Query(default=None, min_length=1, max_length=100),
    event_type: str | None = Query(default=None, min_length=1, max_length=100),
):
    try:
        os_events = os_monitor_service.read_events(event_type=None, limit=None)
        audit_events = read_agentaccess_events()
    except MalformedAuditLogError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    except (ImportError, OSError) as error:
        raise HTTPException(
            status_code=503,
            detail="The OS audit log is unavailable",
        ) from error

    events = []
    for item in os_events:
        event_data = item.model_dump()
        event_data["source"] = "OS"
        event_data["event_type"] = "OS"
        event_data["action"] = item.details.get("action")
        event_data["query"] = item.details.get("query")
        event_data["status"] = None
        event_data["risk_level"] = None
        event_data["message"] = None
        event_data["request_id"] = None
        events.append(event_data)
    events.extend(audit_events)

    if event is not None:
        events = [item for item in events if item.get("event") == event]
    if event_type is not None:
        if event_type.upper() == "OS":
            events = [item for item in events if item.get("source") == "OS"]
        else:
            events = [
                item
                for item in events
                if item.get("event_type", "").upper() == event_type.upper()
            ]

    try:
        events.sort(
            key=_event_timestamp,
            reverse=True,
        )
    except (KeyError, TypeError, ValueError, OverflowError) as error:
        raise HTTPException(
            status_code=500,
            detail="An audit event contains an invalid timestamp",
        ) from error

    return OSEventsResponse(events=events[:limit])
