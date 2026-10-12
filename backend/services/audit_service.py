from database import get_db_connection


def create_audit_log(
    agent_id: int,
    request_id: int | None,
    action: str,
    result: str,
    details: str
):
    connection = get_db_connection()

    if connection is None:
        return False

    cursor = connection.cursor()

    try:
        query = """
            INSERT INTO Audit_Logs
            (agent_id, request_id, action, result, details)
            VALUES (%s, %s, %s, %s, %s)
        """

        cursor.execute(
            query,
            (
                agent_id,
                request_id,
                action,
                result,
                details
            )
        )

        connection.commit()

        return True

    except Exception as e:
        print(f"Audit log error: {e}")
        connection.rollback()
        return False

    finally:
        cursor.close()
        connection.close()