from pydantic import BaseModel
from typing import Any, Optional


# -------------------------
# Authentication
# -------------------------

class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    authenticated: bool
    agent_id: Optional[int] = None
    role: Optional[str] = None
    token: Optional[str] = None
    message: Optional[str] = None


# -------------------------
# Authorization
# -------------------------

class AuthorizationRequest(BaseModel):
    agent_id: int
    action: str
    resource: str


class AuthorizationResponse(BaseModel):
    authorized: bool
    role: Optional[str] = None
    permission: Optional[str] = None
    reason: str


# -------------------------
# Query
# -------------------------

class QueryRequest(BaseModel):
    agent_id: int
    query: str


class QueryValidationResponse(BaseModel):
    valid: bool
    risk_level: str
    action: str
    reason: str


class QueryExecutionResponse(BaseModel):
    success: bool
    request_id: Optional[int] = None
    result: Optional[object] = None
    message: str


# -------------------------
# Dashboard
# -------------------------

class DashboardStats(BaseModel):
    total_requests: int
    approved_requests: int
    denied_requests: int
    high_risk_requests: int


# -------------------------
# OS Monitoring
# -------------------------

class SystemMonitor(BaseModel):
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    process_count: int
    timestamp: str


class SystemRam(BaseModel):
    total_gb: float
    used_gb: float
    percent: float


class SystemDisk(BaseModel):
    percent: float


class SystemProcess(BaseModel):
    pid: int
    name: str
    cpu_percent: float
    memory_mb: float


class SystemStatsResponse(BaseModel):
    cpu_percent: float
    ram: SystemRam
    disk: SystemDisk
    timestamp: str
    processes: list[SystemProcess]


class OSEvent(BaseModel):
    id: int
    timestamp: str
    event: str
    agent_id: int | str
    role: str
    details: dict[str, Any]


class OSEventsResponse(BaseModel):
    events: list[dict[str, Any]]