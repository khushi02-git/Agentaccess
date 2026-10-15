from fastapi import APIRouter
from backend.database import get_db_connection

from backend.schemas import DashboardStats


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get(
    "/stats",
    response_model=DashboardStats
)
def dashboard_stats():

    connection = get_db_connection()

    if connection is None:
        return DashboardStats(
            total_requests=0,
            approved_requests=0,
            denied_requests=0,
            high_risk_requests=0
        )

    cursor = connection.cursor()

    try:

        # Total requests
        cursor.execute(
            "SELECT COUNT(*) FROM Query_Requests"
        )

        total_requests = cursor.fetchone()[0]

        # Approved
        cursor.execute("""
            SELECT COUNT(*)
            FROM Query_Requests
            WHERE status = 'APPROVED'
        """)

        approved_requests = cursor.fetchone()[0]

        # Denied
        cursor.execute("""
            SELECT COUNT(*)
            FROM Query_Requests
            WHERE status = 'DENIED'
        """)

        denied_requests = cursor.fetchone()[0]

        # High-risk count from audit logs
        cursor.execute("""
            SELECT COUNT(*)
            FROM Audit_Logs
            WHERE result = 'DENIED'
        """)

        high_risk_requests = cursor.fetchone()[0]

        return DashboardStats(
            total_requests=total_requests,
            approved_requests=approved_requests,
            denied_requests=denied_requests,
            high_risk_requests=high_risk_requests
        )

    finally:
        cursor.close()
        connection.close()