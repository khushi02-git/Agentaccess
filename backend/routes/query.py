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
from backend.services.audit_service import create_audit_log
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

    result = validate_query(request.query)

    return QueryValidationResponse(**result)


@router.post(
    "/execute",
    response_model=QueryExecutionResponse
)
def execute(request: QueryRequest):

    # --------------------------------
    # 1. Validate query
    # --------------------------------

    validation = validate_query(request.query)

    action = validation["action"]

    # --------------------------------
    # 2. Check authorization
    # --------------------------------

    authorization = authorize_request(
        request.agent_id,
        action,
        "database"
    )

    # --------------------------------
    # 3. Stop if validation fails
    # --------------------------------

    if not validation["valid"]:

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
            connection.commit()
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

        return QueryExecutionResponse(
            success=True,
            request_id=request_id,
            result=result,
            message="Query executed successfully"
        )

    except Exception as e:

        connection.rollback()

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