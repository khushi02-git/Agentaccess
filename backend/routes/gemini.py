
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

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
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        logging.exception("Gemini API request failed")
        raise HTTPException(
            status_code=502,
            detail="Gemini request failed. Check the backend terminal.",
        )

    try:
        result = validate_query(sql)
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Query validation failed.",
        )

    return {
        "generated_sql": sql,
        "validation": result,
        "executed": False,
    }
