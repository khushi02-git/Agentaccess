from fastapi import APIRouter
from database import get_db_connection


router = APIRouter(
    prefix="/audit",
    tags=["Audit"]
)


@router.get("/logs")
def get_audit_logs():

    connection = get_db_connection()

    if connection is None:
        return {
            "error": "Database connection failed"
        }

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute("""
            SELECT
                log_id,
                agent_id,
                request_id,
                action,
                result,
                details,
                logged_at
            FROM Audit_Logs
            ORDER BY logged_at DESC
        """)

        logs = cursor.fetchall()

        return {
            "logs": logs
        }

    finally:
        cursor.close()
        connection.close()