
import sqlglot
from sqlglot import exp, errors


ALLOWED_OPERATIONS = {"SELECT", "INSERT", "UPDATE", "DELETE"}


def get_action(query: str) -> str:
    """Return the operation of one supported SQL statement."""
    if not query or not query.strip():
        return "UNKNOWN"

    try:
        statements = sqlglot.parse(query, read="mysql")
    except (errors.ParseError, ValueError):
        return "UNKNOWN"

    # Reject empty, ambiguous, or multiple statements.
    if len(statements) != 1 or statements[0] is None:
        return "UNKNOWN"

    statement = statements[0]

    if isinstance(statement, exp.Select):
        return "SELECT"
    if isinstance(statement, exp.Insert):
        return "INSERT"
    if isinstance(statement, exp.Update):
        return "UPDATE"
    if isinstance(statement, exp.Delete):
        return "DELETE"

    # WITH queries and all other statement types fail closed
    # until explicitly supported and reviewed.
    return "UNKNOWN"


def validate_query(query: str):
    """Validate supported SQL operations and block unrestricted writes."""
    action = get_action(query)

    if action == "UNKNOWN":
        return {
            "valid": False,
            "risk_level": "HIGH",
            "action": action,
            "reason": "Invalid, ambiguous, or unsupported SQL statement"
        }

    statement = sqlglot.parse_one(query, read="mysql")
    if action == "DELETE" and statement.args.get("where") is None:
        return {
            "valid": False,
            "risk_level": "HIGH",
            "action": action,
            "reason": "Unrestricted DELETE without a WHERE clause is blocked"
        }

    if action == "UPDATE" and statement.args.get("where") is None:
        return {
            "valid": False,
            "risk_level": "HIGH",
            "action": action,
            "reason": "Unrestricted UPDATE without a WHERE clause is blocked"
        }

    if action not in ALLOWED_OPERATIONS:
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
        "reason": "SQL operation passed preliminary validation"
    }
