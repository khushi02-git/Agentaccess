import re
from typing import Any

from backend.database import get_db_connection
from backend.services.audit_service import append_audit_event
from backend.services.auth_service import authorize_request


SEARCHABLE_TABLES = {
    "employees": {
        "id_column": "employee_id",
        "name_column": "employee_name",
        "display_columns": ("department", "salary"),
    },
    "contractors": {
        "id_column": "contractor_id",
        "name_column": "contractor_name",
        "display_columns": ("department", "salary"),
    },
    "managers": {
        "id_column": "manager_id",
        "name_column": "manager_name",
        "display_columns": ("salary",),
    },
}


class EntityResolutionDataError(ValueError):
    """Raised when an internal entity match does not meet the response contract."""


def _validate_match(match: dict[str, Any]) -> dict[str, Any]:
    required = ("table_name", "id_column", "record_id", "display_name", "data")
    if not isinstance(match, dict):
        raise EntityResolutionDataError("Entity resolution produced a malformed match.")
    missing = [field for field in required if field not in match]
    if missing:
        raise EntityResolutionDataError(
            f"Entity resolution produced a malformed match: missing {', '.join(missing)}."
        )
    if (
        not isinstance(match["table_name"], str)
        or not match["table_name"]
        or not isinstance(match["id_column"], str)
        or not match["id_column"]
        or isinstance(match["record_id"], bool)
        or not isinstance(match["record_id"], int)
        or not isinstance(match["display_name"], str)
        or not match["display_name"]
        or not isinstance(match["data"], dict)
    ):
        raise EntityResolutionDataError("Entity resolution produced a malformed match.")
    return match


def _make_match(
    table_name: str,
    metadata: dict[str, Any],
    row: dict[str, Any],
    display_columns: list[str],
) -> dict[str, Any]:
    id_column = metadata["id_column"]
    name_column = metadata["name_column"]
    try:
        match = {
            "table_name": table_name,
            "id_column": id_column,
            "record_id": row[id_column],
            "display_name": row[name_column],
            "data": {
                column: row[column]
                for column in [name_column, *display_columns]
            },
        }
    except (KeyError, TypeError) as error:
        raise EntityResolutionDataError(
            "Database returned an incomplete entity match."
        ) from error
    return _validate_match(match)


def extract_entity_name(request_text: str) -> str:
    cleaned = (request_text or "").strip()
    if not cleaned:
        return ""

    if re.search(
        r"\b(?:employee|contractor|manager)\s+(?:id\s*)?#?\d+\b",
        cleaned,
        flags=re.IGNORECASE,
    ):
        return ""

    generic_terms = {
        "all",
        "above",
        "are",
        "count",
        "details",
        "every",
        "employee",
        "employees",
        "emp",
        "how",
        "many",
        "there",
        "with",
        "from",
        "the",
        "salary",
        "record",
        "records",
        "contractor",
        "contractors",
        "manager",
        "managers",
    }
    generic_term_pattern = "|".join(
        re.escape(term) for term in sorted(generic_terms, key=len, reverse=True)
    )
    name_token = rf"(?!(?:{generic_term_pattern})\b)[A-Z][a-z]+"
    patterns = (
        rf"\b(?:named|for|about)\s+({name_token}(?:\s+{name_token})*)\b",
        r"\b(?:show|find|update|delete|remove|change)\s+(?:me\s+)?(?:the\s+)?"
        r"(?:(?:employee|contractor|manager)\s+)?"
        rf"({name_token}(?:\s+{name_token})*)\b",
    )
    for pattern in patterns:
        match = re.search(pattern, cleaned, flags=re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            candidate_terms = set(candidate.casefold().split())
            if not candidate_terms.intersection(generic_terms):
                return candidate
    return ""


def _can_search_table(agent_id: int, table_name: str) -> bool:
    auth = authorize_request(agent_id, "SELECT", table_name)
    return bool(auth.get("authorized"))


def _configured_tables_for_db(
    connection,
) -> list[tuple[str, dict[str, Any], set[str]]]:
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT TABLE_NAME, COLUMN_NAME FROM information_schema.columns "
            f"WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME IN "
            f"({', '.join(['%s'] * len(SEARCHABLE_TABLES))})",
            tuple(SEARCHABLE_TABLES),
        )
        columns_by_table: dict[str, set[str]] = {}
        for table_name, column_name in cursor.fetchall():
            columns_by_table.setdefault(str(table_name).casefold(), set()).add(
                str(column_name).casefold()
            )
    finally:
        if cursor is not None:
            cursor.close()

    available = []
    for table_name, metadata in SEARCHABLE_TABLES.items():
        existing_columns = columns_by_table.get(table_name.casefold(), set())
        if not {
            metadata["id_column"].casefold(),
            metadata["name_column"].casefold(),
        }.issubset(existing_columns):
            continue
        available.append((table_name, metadata, existing_columns))
    return available


def _collect_matching_rows(agent_id: int, entity_name: str) -> list[dict[str, Any]]:
    connection = get_db_connection()
    if connection is None:
        raise RuntimeError("Database connection failed")

    results: list[dict[str, Any]] = []
    records_cursor = None
    try:
        available_tables = _configured_tables_for_db(connection)
        records_cursor = connection.cursor(dictionary=True)
        for table_name, metadata, existing_columns in available_tables:
            if not _can_search_table(agent_id, table_name):
                continue

            id_column = metadata["id_column"]
            name_column = metadata["name_column"]
            display_columns = [
                column
                for column in metadata["display_columns"]
                if column.casefold() in existing_columns
            ]
            selected_columns = [id_column, name_column, *display_columns]
            select_columns = ", ".join(
                f"`{column}` AS `{column}`" for column in selected_columns
            )

            records_cursor.execute(
                f"SELECT {select_columns} FROM `{table_name}` "
                f"WHERE `{name_column}` = %s LIMIT 50",
                (entity_name,),
            )
            rows = records_cursor.fetchall()
            for row in rows:
                results.append(
                    _make_match(table_name, metadata, row, display_columns)
                )
    finally:
        if records_cursor is not None:
            records_cursor.close()
        connection.close()
    return results


def resolve_entity_matches(agent_id: int, request_text: str) -> dict[str, Any]:
    entity_name = extract_entity_name(request_text)
    if not entity_name:
        append_audit_event(
            "ENTITY_RESOLUTION",
            "NOT_REQUIRED",
            agent_id=agent_id,
            message="No specific entity requires resolution",
        )
        return {
            "status": "not_required",
            "matches": [],
        }

    try:
        matches = [
            _validate_match(match)
            for match in _collect_matching_rows(agent_id, entity_name)
        ]
    except Exception:
        append_audit_event(
            "ENTITY_RESOLUTION_FAILED",
            "FAILED",
            agent_id=agent_id,
            message="Entity lookup failed",
        )
        raise

    if not matches:
        append_audit_event(
            "ENTITY_RESOLUTION",
            "NO_MATCH",
            agent_id=agent_id,
            message="No matching record found",
        )
        return {
            "status": "no_match",
            "message": "No matching record found.",
            "matches": [],
        }

    if len(matches) == 1:
        append_audit_event(
            "ENTITY_RESOLUTION",
            "SINGLE_MATCH",
            agent_id=agent_id,
            message="One permitted matching record found",
        )
        return {
            "status": "single_match",
            "message": "Exactly one matching record was found.",
            "match": matches[0],
            "matches": [],
        }

    append_audit_event(
        "MULTIPLE_MATCHES",
        "AMBIGUOUS",
        agent_id=agent_id,
        message=f"{len(matches)} permitted matching records found",
    )
    return {
        "status": "multiple_matches",
        "message": "Multiple matching records found. Please select one.",
        "matches": matches,
    }


def record_entity_selection(
    agent_id: int,
    table_name: str,
    id_column: str,
    record_id: int,
) -> dict[str, Any]:
    table_config = SEARCHABLE_TABLES.get(table_name)
    if table_config is None or table_config["id_column"] != id_column:
        append_audit_event(
            "ENTITY_RESOLUTION_FAILED",
            "BLOCKED",
            agent_id=agent_id,
            action="SELECT",
            message="Selected entity table or identifier is not configured",
        )
        raise EntityResolutionDataError("The selected record is not a configured entity.")

    if not _can_search_table(agent_id, table_name):
        append_audit_event(
            "ENTITY_RESOLUTION_FAILED",
            "DENIED",
            agent_id=agent_id,
            action="SELECT",
            message="Agent is not authorized to access the selected entity table",
        )
        raise PermissionError("Agent is not authorized to access the selected record.")

    connection = get_db_connection()
    if connection is None:
        append_audit_event(
            "ENTITY_RESOLUTION_FAILED",
            "FAILED",
            agent_id=agent_id,
            message="Database connection failed while confirming selected record",
        )
        raise RuntimeError("Database connection failed")

    cursor = None
    try:
        configured = {
            configured_table: (metadata, existing_columns)
            for configured_table, metadata, existing_columns
            in _configured_tables_for_db(connection)
        }
        table_metadata = configured.get(table_name)
        if table_metadata is None:
            raise EntityResolutionDataError("The selected record no longer exists.")
        metadata, existing_columns = table_metadata
        cursor = connection.cursor(dictionary=True)
        name_column = table_config["name_column"]
        display_columns = [
            column
            for column in metadata["display_columns"]
            if column.casefold() in existing_columns
        ]
        selected_columns = [id_column, name_column, *display_columns]
        select_columns = ", ".join(
            f"`{column}` AS `{column}`" for column in selected_columns
        )
        cursor.execute(
            f"SELECT {select_columns} FROM `{table_name}` "
            f"WHERE `{id_column}` = %s LIMIT 1",
            (record_id,),
        )
        row = cursor.fetchone()
    except Exception:
        append_audit_event(
            "ENTITY_RESOLUTION_FAILED",
            "FAILED",
            agent_id=agent_id,
            message="Selected-record lookup failed",
        )
        raise
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()

    if row is None:
        raise EntityResolutionDataError("The selected record no longer exists.")

    selected_match = _make_match(
        table_name,
        metadata,
        row,
        display_columns,
    )

    append_audit_event(
        "ENTITY_SELECTED",
        "SUCCESS",
        agent_id=agent_id,
        action="SELECT",
        message=f"Selected {table_name} record {id_column}={record_id}",
    )
    return selected_match
