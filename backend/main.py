import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.routes.auth import router as auth_router
from backend.routes.query import router as query_router
from backend.routes.audit import router as audit_router
from backend.routes.dashboard import router as dashboard_router
from backend.routes.gemini import router as gemini_router
from backend.routes.os_monitor import router as os_monitor_router
from backend.services.os_monitor_service import refresh_system_stats_periodically


@asynccontextmanager
async def lifespan(app: FastAPI):
    refresh_task = asyncio.create_task(refresh_system_stats_periodically())
    try:
        yield
    finally:
        refresh_task.cancel()
        try:
            await refresh_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="AgentAccess API",
    description="FastAPI Backend for AgentAccess",
    version="1.0.0",
    lifespan=lifespan,
)


# -------------------------
# Include API routes
# -------------------------

app.include_router(auth_router)
app.include_router(query_router)
app.include_router(audit_router)
app.include_router(dashboard_router)
app.include_router(gemini_router)
app.include_router(os_monitor_router)


# -------------------------
# Root endpoint
# -------------------------

@app.get("/")
def root():

    return {
        "project": "AgentAccess",
        "message": "AgentAccess FastAPI Backend is running"
    }


# -------------------------
# Health check
# -------------------------

@app.get("/health")
def health():

    return {
        "status": "healthy"
    }
