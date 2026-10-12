def authenticate_user(username: str, password: str):
    """
    Temporary authentication logic.

    This will later be replaced/integrated
    with Member 2's authentication module.
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
    Temporary authorization logic.

    Later this will use Member 2's RBAC
    and permission system.
    """

    if agent_id == 1:
        return {
            "authorized": True,
            "role": "Admin",
            "permission": action,
            "reason": "Role has permission to perform this action"
        }

    return {
        "authorized": False,
        "role": "ReadOnly",
        "permission": action,
        "reason": "Agent does not have permission for this action"
    }