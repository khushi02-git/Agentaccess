from pydantic import BaseModel
from typing import Optional


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