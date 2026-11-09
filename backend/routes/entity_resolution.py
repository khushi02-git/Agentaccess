import logging

from fastapi import APIRouter, HTTPException

from backend.schemas import (
    EntityResolutionRequest,
    EntityResolutionResponse,
    EntitySelectionRequest,
)
from backend.services.entity_resolution_service import (
    EntityResolutionDataError,
    record_entity_selection,
    resolve_entity_matches,
)

router = APIRouter(prefix="/query", tags=["Entity Resolution"])
logger = logging.getLogger(__name__)


@router.post("/resolve-entity", response_model=EntityResolutionResponse)
def resolve_entity(request: EntityResolutionRequest):
    try:
        result = resolve_entity_matches(request.agent_id, request.request)
        return EntityResolutionResponse(**result)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except EntityResolutionDataError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Entity resolution failed")
        raise HTTPException(
            status_code=500,
            detail="Entity resolution failed. Check the backend logs.",
        ) from exc


@router.post("/resolve-entity/selection")
def select_entity(request: EntitySelectionRequest):
    try:
        selected_match = record_entity_selection(
            request.agent_id,
            request.table_name,
            request.id_column,
            request.record_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except EntityResolutionDataError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Entity selection could not be recorded")
        raise HTTPException(
            status_code=500,
            detail="Entity selection failed. Check the backend logs.",
        ) from exc

    return {
        "success": True,
        "message": "Selected record recorded.",
        "match": selected_match,
    }
