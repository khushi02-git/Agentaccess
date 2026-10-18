from fastapi import APIRouter, HTTPException

from backend.schemas import (
    QueryRequest,
    QueryValidationResponse,
    QueryExecutionResponse
)

from backend.services.query_service import (
    validate_query,
    get_action
)

from backend.services.auth_service import authorize_request
from backend.services.audit_service import append_audit_event, create_audit_log
from backend.database import get_db_connection


router = APIRouter(
    prefix="/query",
    tags=["Query Management"]
)


@router.post(
    "/validate",
    response_model=QueryValidationResponse
)
def validate(request: QueryRequest):

    try:
        result = validate_query(request.query)
    except Exception:
        append_audit_event(
            "ERROR",
            "FAILED",
            agent_id=request.agent_id,
            action="VALIDATE",
            query=request.query,
            message="Query validation failed",
        )
        raise
    append_audit_event(
        "VALIDATION",
        "PASSED" if result["valid"] else "BLOCKED",
        agent_id=request.agent_id,
        action=result["action"],
        query=request.query,
        risk_level=result["risk_level"],
        message=result["reason"],
    )

    return QueryValidationResponse(**result)


@router.post(
    "/execute",
    response_model=QueryExecutionResponse
)
def execute(request: QueryRequest):

    # --------------------------------
    # 1. Validate query
    # --------------------------------

    try:
        validation = validate_query(request.query)
    except Exception:
        append_audit_event(
            "ERROR",
            "FAILED",
            agent_id=request.agent_id,
            action="VALIDATE",
            query=request.query,
            message="Query validation failed",
        )
        raise

    action = validation["action"]

    # --------------------------------
    # 2. Check authorization
    # --------------------------------

    authorization = authorize_request(
        request.agent_id,
        action,
        "database"
    )
    append_audit_event(
        "RBAC",
        "ALLOWED" if authorization["authorized"] else "DENIED",
        agent_id=request.agent_id,
        role=authorization.get("role"),
        action=action,
        query=request.query,
        message=authorization["reason"],
    )

    append_audit_event(
        "VALIDATION",
        "PASSED" if validation["valid"] else "BLOCKED",
        agent_id=request.agent_id,
        role=authorization.get("role"),
        action=action,
        query=request.query,
        risk_level=validation["risk_level"],
        message=validation["reason"],
    )

    # --------------------------------
    # 3. Stop if validation fails
    # --------------------------------

    if not validation["valid"]:

        append_audit_event(
            "QUERY",
            "BLOCKED",
            agent_id=request.agent_id,
            role=authorization.get("role"),
            action=action,
            query=request.query,
            risk_level=validation["risk_level"],
            message=validation["reason"],
        )
        append_audit_event(
            "SECURITY",
            "BLOCKED",
            agent_id=request.agent_id,
            role=authorization.get("role"),
            action=action,
            query=request.query,
            risk_level=validation["risk_level"],
            message=validation["reason"],
        )
        create_audit_log(
            request.agent_id,
            None,
            action,
            "DENIED",
            validation["reason"]
        )

        return QueryExecutionResponse(
            success=False,
            message=validation["reason"]
        )

    # --------------------------------
    # 4. Stop if authorization fails
    # --------------------------------

    if not authorization["authorized"]:

        append_audit_event(
            "QUERY",
            "BLOCKED",
            agent_id=request.agent_id,
            role=authorization.get("role"),
            action=action,
            query=request.query,
            risk_level=validation["risk_level"],
            message=authorization["reason"],
        )
        append_audit_event(
            "SECURITY",
            "BLOCKED",
            agent_id=request.agent_id,
            role=authorization.get("role"),
            action=action,
            query=request.query,
            risk_level=validation["risk_level"],
            message=authorization["reason"],
        )
        create_audit_log(
            request.agent_id,
            None,
            action,
            "DENIED",
            authorization["reason"]
        )

        return QueryExecutionResponse(
            success=False,
            message=authorization["reason"]
        )

    # --------------------------------
    # 5. Connect to database
    # --------------------------------

    connection = get_db_connection()

    if connection is None:

        append_audit_event(
            "QUERY",
            "FAILED",
            agent_id=request.agent_id,
            role=authorization.get("role"),
            action=action,
            query=request.query,
            risk_level=validation["risk_level"],
            message="Database connection failed",
        )
        append_audit_event(
            "ERROR",
            "FAILED",
            agent_id=request.agent_id,
            action=action,
            query=request.query,
            message="Database connection failed",
        )
        raise HTTPException(
            status_code=500,
            detail="Database connection failed"
        )

    cursor = connection.cursor()

    try:

        # Execute approved query
        cursor.execute(request.query)

        # Get results for SELECT
        if action == "SELECT":
            result = cursor.fetchall()
        else:
            result = f"{cursor.rowcount} row(s) affected"

        # --------------------------------
        # 6. Store request
        # --------------------------------

        insert_request = """
            INSERT INTO Query_Requests
            (agent_id, query_text, status)
            VALUES (%s, %s, %s)
        """

        cursor.execute(
            insert_request,
            (
                request.agent_id,
                request.query,
                "APPROVED"
            )
        )

        request_id = cursor.lastrowid

        connection.commit()

        # --------------------------------
        # 7. Audit
        # --------------------------------

        create_audit_log(
            request.agent_id,
            request_id,
            action,
            "ALLOWED",
            "Query executed successfully"
        )
        append_audit_event(
            "QUERY",
            "SUCCESS",
            agent_id=request.agent_id,
            role=authorization.get("role"),
            action=action,
            query=request.query,
            risk_level=validation["risk_level"],
            message="Query executed successfully",
            request_id=request_id,
        )

        return QueryExecutionResponse(
            success=True,
            request_id=request_id,
            result=result,
            message="Query executed successfully"
        )

    except Exception as e:

        connection.rollback()

        append_audit_event(
            "QUERY",
            "FAILED",
            agent_id=request.agent_id,
            role=authorization.get("role"),
            action=action,
            query=request.query,
            risk_level=validation["risk_level"],
            message=str(e),
        )
        append_audit_event(
            "ERROR",
            "FAILED",
            agent_id=request.agent_id,
            action=action,
            query=request.query,
            message=str(e),
        )
        create_audit_log(
            request.agent_id,
            None,
            action,
            "DENIED",
            str(e)
        )

        raise HTTPException(
            status_code=400,
            detail=f"Query execution failed: {str(e)}"
        )

    finally:
        cursor.close()
        connection.close()