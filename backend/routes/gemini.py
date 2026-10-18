
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.services.audit_service import append_audit_event
from backend.services.gemini_service import generate_sql
from backend.services.query_service import validate_query

router = APIRouter(prefix="/gemini", tags=["Gemini AI"])


class GeminiRequest(BaseModel):
    request: str = Field(min_length=1, max_length=2000)

import logging
@router.post("/generate")
def generate(request: GeminiRequest):
    try:
        sql = generate_sql(request.request)
    except RuntimeError as exc:
        append_audit_event(
            "GEMINI",
            "ERROR",
            message=str(exc),
        )
        append_audit_event("ERROR", "FAILED", message=str(exc))
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        append_audit_event("GEMINI", "ERROR", message="SQL generation failed")
        append_audit_event("ERROR", "FAILED", message="Gemini SQL generation failed")
        logging.exception("Gemini API request failed")
        raise HTTPException(
            status_code=502,
            detail="Gemini request failed. Check the backend terminal.",
        )

    append_audit_event(
        "GEMINI",
        "SUCCESS",
        action="GENERATE",
        query=sql,
        message="SQL generated; no execution performed",
    )

    try:
        result = validate_query(sql)
    except Exception:
        append_audit_event(
            "ERROR",
            "FAILED",
            action="VALIDATE",
            query=sql,
            message="Generated SQL validation failed",
        )
        raise HTTPException(
            status_code=500,
            detail="Query validation failed.",
        )

    append_audit_event(
        "VALIDATION",
        "PASSED" if result["valid"] else "BLOCKED",
        action=result["action"],
        query=sql,
        risk_level=result["risk_level"],
        message=result["reason"],
    )

    return {
        "generated_sql": sql,
        "validation": result,
        "executed": False,
    }
