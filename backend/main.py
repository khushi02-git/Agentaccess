from fastapi import FastAPI

from routes.auth import router as auth_router
from routes.query import router as query_router
from routes.audit import router as audit_router
from routes.dashboard import router as dashboard_router


app = FastAPI(
    title="AgentAccess API",
    description="FastAPI Backend for AgentAccess",
    version="1.0.0"
)


# -------------------------
# Include API routes
# -------------------------

app.include_router(auth_router)
app.include_router(query_router)
app.include_router(audit_router)
app.include_router(dashboard_router)


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