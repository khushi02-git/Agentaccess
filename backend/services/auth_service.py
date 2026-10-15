try:
    from backend.database import get_db_connection
except ModuleNotFoundError:
    from backend.database import get_db_connection


def authenticate_user(username: str, password: str):
    """
    Temporary authentication for development.
    Replace with the team's final authentication module.
    """
    if username == "admin" and password == "admin123":
        return {
            "authenticated": True,
            "agent_id": 1,
            "role": "Admin",
            "token": "TEMP_TOKEN"
        }

    return {
        "authenticated": False,
        "agent_id": None,
        "role": None,
        "token": None
    }


def authorize_request(agent_id: int, action: str, resource: str):
    """
    Authorize an agent using Agents, Roles, Permissions,
    Role_Permissions, and Blocked_Operations.
    Fails closed if the database check cannot be completed.
    """
    action = action.strip().upper()

    if action not in {"SELECT", "INSERT", "UPDATE", "DELETE"}:
        return {
            "authorized": False,
            "role": None,
            "permission": action,
            "reason": "Unsupported or restricted operation"
        }

    connection = get_db_connection()
    if connection is None:
        return {
            "authorized": False,
            "role": None,
            "permission": action,
            "reason": "Authorization unavailable: database connection failed"
        }

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)

        # Confirm agent identity and obtain the assigned role.
        cursor.execute(
            """
            SELECT a.agent_id, r.role_name
            FROM Agents a
            JOIN Roles r ON r.role_id = a.role_id
            WHERE a.agent_id = %s
            """,
            (agent_id,)
        )
        agent = cursor.fetchone()

        if not agent:
            return {
                "authorized": False,
                "role": None,
                "permission": action,
                "reason": "Unknown agent"
            }

        # Check whether the requested operation is blocked by policy.
        cursor.execute(
            """
            SELECT operation_name
            FROM Blocked_Operations
            WHERE UPPER(operation_name) = %s
            LIMIT 1
            """,
            (action,)
        )
        blocked = cursor.fetchone()

        if blocked:
            return {
                "authorized": False,
                "role": agent["role_name"],
                "permission": action,
                "reason": f"{action} is blocked by AgentAccess policy"
            }

        # Check role-based permission.
        cursor.execute(
            """
            SELECT 1
            FROM Agents a
            JOIN Role_Permissions rp ON rp.role_id = a.role_id
            JOIN Permissions p ON p.permission_id = rp.permission_id
            WHERE a.agent_id = %s
              AND UPPER(p.permission_name) = %s
            LIMIT 1
            """,
            (agent_id, action)
        )
        has_permission = cursor.fetchone() is not None

        if not has_permission:
            return {
                "authorized": False,
                "role": agent["role_name"],
                "permission": action,
                "reason": "Agent role does not have this permission"
            }

        return {
            "authorized": True,
            "role": agent["role_name"],
            "permission": action,
            "reason": "Role permission and operation policy checks passed"
        }

    except Exception:
        # Don't expose internal database errors to API clients.
        return {
            "authorized": False,
            "role": None,
            "permission": action,
            "reason": "Authorization check failed; request denied"
        }

    finally:
        if cursor is not None:
            cursor.close()
        connection.close()
