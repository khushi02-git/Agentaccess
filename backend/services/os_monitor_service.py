import asyncio
import importlib.util
import json
import logging
import threading
from functools import lru_cache
from pathlib import Path
from types import ModuleType

from backend.schemas import OSEvent, SystemStatsResponse

logger = logging.getLogger(__name__)
REFRESH_INTERVAL_SECONDS = 5
OS_MONITOR_DIR = (
    Path(__file__).resolve().parents[2] / "AgentAccess-OS" / "monitor"
)


class MalformedAuditLogError(Exception):
    """Raised when the OS audit log contains invalid JSONL."""


@lru_cache(maxsize=None)
def _load_os_module(module_name: str, file_path: str) -> ModuleType:
    """Load one standalone OS helper without adding its directory to sys.path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load OS monitor module from {file_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class OSMonitorService:
    def __init__(self):
        self._cache_lock = threading.Lock()
        self._cached_system_stats: SystemStatsResponse | None = None

    def refresh_system_stats(self) -> SystemStatsResponse:
        module = _load_os_module(
            "agentaccess_os_system_stats",
            str(OS_MONITOR_DIR / "system_stats.py"),
        )
        stats = SystemStatsResponse(**module.get_system_stats())
        with self._cache_lock:
            self._cached_system_stats = stats
        return stats

    def get_cached_system_stats(self) -> SystemStatsResponse | None:
        with self._cache_lock:
            return self._cached_system_stats

    def read_events(
        self,
        event_type: str | None,
        limit: int | None,
    ) -> list[OSEvent]:
        module = _load_os_module(
            "agentaccess_os_audit_log",
            str(OS_MONITOR_DIR / "audit_log.py"),
        )
        try:
            events = module.read_events()
        except json.JSONDecodeError as error:
            raise MalformedAuditLogError(
                "The OS audit log contains a malformed JSONL entry"
            ) from error

        if event_type is not None:
            events = [event for event in events if event.get("event") == event_type]

        newest_events = events[-limit:] if limit is not None else events
        return [OSEvent(**event) for event in newest_events]


os_monitor_service = OSMonitorService()


async def refresh_system_stats_periodically() -> None:
    while True:
        try:
            await asyncio.to_thread(os_monitor_service.refresh_system_stats)
        except Exception:
            logger.exception("OS system-stat refresh failed")
        await asyncio.sleep(REFRESH_INTERVAL_SECONDS)
