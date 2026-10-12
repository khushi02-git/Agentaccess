import re


BLOCKED_OPERATIONS = {
    "DROP",
    "TRUNCATE",
    "ALTER",
    "CREATE",
    "GRANT",
    "REVOKE"
}


def get_action(query: str) -> str:
    """
    Extract the SQL operation from the query.
    """

    query = query.strip().upper()

    if not query:
        return "UNKNOWN"

    return query.split()[0]


def validate_query(query: str):
    """
    Temporary query validation.

    Final validation logic will be connected
    with Member 1's query-validation module.
    """

    action = get_action(query)

    if action in BLOCKED_OPERATIONS:
        return {
            "valid": False,
            "risk_level": "HIGH",
            "action": action,
            "reason": f"{action} operation is blocked by AgentAccess policy"
        }

    allowed_operations = {
        "SELECT",
        "INSERT",
        "UPDATE",
        "DELETE"
    }

    if action not in allowed_operations:
        return {
            "valid": False,
            "risk_level": "HIGH",
            "action": action,
            "reason": "Unsupported SQL operation"
        }

    return {
        "valid": True,
        "risk_level": "LOW",
        "action": action,
        "reason": "Query follows allowed database operation rules"
    }