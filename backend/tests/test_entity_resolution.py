import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend.services import entity_resolution_service as entity_service
from backend.services import gemini_service
from backend.services.query_service import validate_query
from backend.schemas import EntityResolutionResponse
from backend.schemas import EntitySelectionRequest


def make_match(table_name="employees", record_id=101):
    id_column, name_column = {
        "employees": ("employee_id", "employee_name"),
        "contractors": ("contractor_id", "contractor_name"),
    }.get(table_name, ("employee_id", "employee_name"))
    return {
        "table_name": table_name,
        "id_column": id_column,
        "record_id": record_id,
        "display_name": "Rahul Verma",
        "data": {name_column: "Rahul Verma", "salary": 60000},
    }


class EntityResolutionTests(unittest.TestCase):
    def test_detects_specific_names_and_skips_generic_or_id_requests(self):
        for request in (
            "Update Rahul Verma's salary to 70000",
            "update rahul verma salary 20000",
            "change Rahul Verma salary to 70000",
            "update Priya Singh salary 80000",
            "Show me Rahul Verma",
            "Show Rahul Verma details",
            "Delete Rahul Verma's record",
            "Delete Rahul Verma",
        ):
            expected = "Priya Singh" if "Priya" in request else "Rahul Verma"
            with self.subTest(request=request):
                self.assertEqual(
                    entity_service.extract_entity_name(request).casefold(),
                    expected.casefold(),
                )

        for request in (
            "show all",
            "show all employees",
            "list all employees",
            "count employees",
            "how many employees are there",
            "Show employees with salary above 50000",
            "Update employee 101 salary to 70000",
        ):
            with self.subTest(request=request):
                self.assertEqual(entity_service.extract_entity_name(request), "")

    @patch.object(entity_service, "append_audit_event")
    @patch.object(entity_service, "_collect_matching_rows")
    def test_generic_request_does_not_require_entity_resolution(
        self, collect, audit
    ):
        result = entity_service.resolve_entity_matches(1, "show all employee")

        self.assertEqual(result, {"status": "not_required", "matches": []})
        collect.assert_not_called()
        audit.assert_called_once()
        self.assertEqual(audit.call_args.args[1], "NOT_REQUIRED")

        response = EntityResolutionResponse(**result).model_dump()
        self.assertEqual(
            response,
            {
                "status": "not_required",
                "message": None,
                "match": None,
                "matches": [],
            },
        )

    @patch.object(entity_service, "append_audit_event")
    @patch.object(entity_service, "_collect_matching_rows")
    def test_single_multiple_and_no_match_states(self, collect, _audit):
        employee_match = {
            "table_name": "employees",
            "id_column": "employee_id",
            "record_id": 3,
            "display_name": "Rahul Verma",
            "data": {
                "employee_name": "Rahul Verma",
                "department": "Finance",
                "salary": 40000,
            },
        }
        contractor_match = {
            "table_name": "contractors",
            "id_column": "contractor_id",
            "record_id": 1,
            "display_name": "Rahul Verma",
            "data": {
                "contractor_name": "Rahul Verma",
                "department": "IT",
                "salary": 50000,
            },
        }
        collect.return_value = [employee_match]
        single = entity_service.resolve_entity_matches(
            1, "Update Rahul Verma's salary to 70000"
        )
        self.assertEqual(single["status"], "single_match")
        self.assertEqual(single["match"], employee_match)

        collect.return_value = [employee_match, contractor_match]
        multiple = entity_service.resolve_entity_matches(
            1, "Update Rahul Verma's salary to 70000"
        )
        self.assertEqual(multiple["status"], "multiple_matches")
        self.assertNotIn("match", multiple)
        self.assertEqual(multiple["matches"], [employee_match, contractor_match])

        collect.return_value = []
        no_match = entity_service.resolve_entity_matches(1, "Show Rahul Verma")
        self.assertEqual(no_match["status"], "no_match")

    @patch.object(entity_service, "append_audit_event")
    @patch.object(entity_service, "_collect_matching_rows")
    def test_malformed_internal_match_raises_controlled_error(self, collect, _audit):
        collect.return_value = [{"table": "employees", "id": 101}]
        with self.assertRaisesRegex(
            entity_service.EntityResolutionDataError,
            "missing table_name",
        ):
            entity_service.resolve_entity_matches(1, "Show Rahul Verma")

    @patch.object(entity_service, "append_audit_event")
    @patch.object(entity_service, "_configured_tables_for_db")
    @patch.object(entity_service, "_can_search_table")
    @patch.object(entity_service, "get_db_connection")
    def test_unauthorized_table_is_not_searched(
        self, get_connection, can_search, configured, _audit
    ):
        class Cursor:
            query = ""

            def execute(self, query, params=None):
                self.query = query

            def fetchall(self):
                if "FROM `employees`" in self.query:
                    return [
                        {
                            "employee_id": 101,
                            "employee_name": "Rahul Verma",
                            "salary": 60000,
                        }
                    ]
                return []

            def close(self):
                pass

        class Connection:
            def __init__(self):
                self.queries = []

            def cursor(self, **_kwargs):
                cursor = Cursor()
                original_execute = cursor.execute

                def track(query, params=None):
                    self.queries.append(query)
                    original_execute(query, params)

                cursor.execute = track
                return cursor

            def close(self):
                pass

        connection = Connection()
        get_connection.return_value = connection
        configured.return_value = [
            (
                "employees",
                entity_service.SEARCHABLE_TABLES["employees"],
                {"employee_id", "employee_name", "salary"},
            ),
            (
                "contractors",
                entity_service.SEARCHABLE_TABLES["contractors"],
                {"contractor_id", "contractor_name", "salary"},
            ),
        ]
        can_search.side_effect = lambda _agent_id, table: table == "employees"

        results = entity_service._collect_matching_rows(1, "Rahul Verma")
        self.assertEqual([item["table_name"] for item in results], ["employees"])
        self.assertFalse(any("FROM `contractors`" in query for query in connection.queries))

    def test_database_metadata_lookup_is_limited_to_explicit_allowlist(self):
        class Cursor:
            query = ""
            params = None

            def execute(self, query, params=None):
                self.query = query
                self.params = params

            def fetchall(self):
                return [
                    ("employees", "employee_id"),
                    ("employees", "employee_name"),
                    ("contractors", "contractor_id"),
                    ("contractors", "contractor_name"),
                    ("audit_logs", "id"),
                    ("agents", "agent_id"),
                ]

            def close(self):
                pass

        class Connection:
            def __init__(self):
                self.cursor_instance = Cursor()

            def cursor(self):
                return self.cursor_instance

        connection = Connection()
        available = entity_service._configured_tables_for_db(connection)

        self.assertEqual(
            [table_name for table_name, _, _ in available],
            ["employees", "contractors"],
        )
        self.assertIn("TABLE_NAME IN", connection.cursor_instance.query)
        self.assertEqual(
            connection.cursor_instance.params,
            tuple(entity_service.SEARCHABLE_TABLES),
        )

    @patch.object(entity_service, "append_audit_event")
    @patch.object(entity_service, "_configured_tables_for_db")
    @patch.object(entity_service, "_can_search_table", return_value=True)
    @patch.object(entity_service, "get_db_connection")
    def test_search_finds_employee_and_contractor_matches_only(
        self, get_connection, _can_search, configured, _audit
    ):
        class Cursor:
            def __init__(self):
                self.query = ""

            def execute(self, query, params=None):
                self.query = query
                self.params = params

            def fetchall(self):
                if "FROM `employees`" in self.query:
                    return [{
                        "employee_id": 3,
                        "employee_name": "Rahul Verma",
                        "department": "Finance",
                        "salary": 40000,
                    }]
                if "FROM `contractors`" in self.query:
                    return [{
                        "contractor_id": 1,
                        "contractor_name": "Rahul Verma",
                        "department": "IT",
                        "salary": 50000,
                    }]
                return []

            def close(self):
                pass

        class Connection:
            def __init__(self):
                self.queries = []

            def cursor(self, **_kwargs):
                cursor = Cursor()
                original_execute = cursor.execute

                def track(query, params=None):
                    self.queries.append(query)
                    original_execute(query, params)

                cursor.execute = track
                return cursor

            def close(self):
                pass

        connection = Connection()
        get_connection.return_value = connection
        configured.return_value = [
            (
                "employees",
                entity_service.SEARCHABLE_TABLES["employees"],
                {"employee_id", "employee_name", "department", "salary"},
            ),
            (
                "contractors",
                entity_service.SEARCHABLE_TABLES["contractors"],
                {"contractor_id", "contractor_name", "department", "salary"},
            ),
        ]

        matches = entity_service._collect_matching_rows(1, "Rahul Verma")

        self.assertEqual(
            matches,
            [
                {
                    "table_name": "employees",
                    "id_column": "employee_id",
                    "record_id": 3,
                    "display_name": "Rahul Verma",
                    "data": {
                        "employee_name": "Rahul Verma",
                        "department": "Finance",
                        "salary": 40000,
                    },
                },
                {
                    "table_name": "contractors",
                    "id_column": "contractor_id",
                    "record_id": 1,
                    "display_name": "Rahul Verma",
                    "data": {
                        "contractor_name": "Rahul Verma",
                        "department": "IT",
                        "salary": 50000,
                    },
                },
            ],
        )
        self.assertEqual(len(connection.queries), 2)
        self.assertTrue(all("audit_logs" not in query for query in connection.queries))

    @patch.object(entity_service, "append_audit_event")
    @patch.object(entity_service, "_configured_tables_for_db")
    @patch.object(entity_service, "_can_search_table", return_value=True)
    @patch.object(entity_service, "get_db_connection")
    def test_selected_record_id_is_revalidated_and_preserved(
        self, get_connection, _can_search, configured, audit
    ):
        class Cursor:
            def execute(self, query, params=None):
                self.query = query
                self.params = params

            def fetchone(self):
                return {
                    "employee_id": 101,
                    "employee_name": "Rahul Verma",
                    "salary": 60000,
                }

            def close(self):
                pass

        class Connection:
            def cursor(self, **_kwargs):
                return Cursor()

            def close(self):
                pass

        get_connection.return_value = Connection()
        configured.return_value = [
            (
                "employees",
                entity_service.SEARCHABLE_TABLES["employees"],
                {"employee_id", "employee_name", "salary"},
            )
        ]

        selected = entity_service.record_entity_selection(
            1, "employees", "employee_id", 101
        )
        self.assertEqual(selected, make_match())
        audit.assert_called_once()
        self.assertEqual(audit.call_args.args[0], "ENTITY_SELECTED")

    @patch.object(entity_service, "append_audit_event")
    @patch.object(entity_service, "_configured_tables_for_db")
    @patch.object(entity_service, "_can_search_table", return_value=True)
    @patch.object(entity_service, "get_db_connection")
    def test_selected_contractor_is_reloaded_with_department(
        self, get_connection, _can_search, configured, _audit
    ):
        class Cursor:
            def execute(self, query, params=None):
                self.query = query
                self.params = params

            def fetchone(self):
                return {
                    "contractor_id": 1,
                    "contractor_name": "Rahul Verma",
                    "department": "IT",
                    "salary": 50000,
                }

            def close(self):
                pass

        class Connection:
            def cursor(self, **_kwargs):
                return Cursor()

            def close(self):
                pass

        get_connection.return_value = Connection()
        configured.return_value = [
            (
                "contractors",
                entity_service.SEARCHABLE_TABLES["contractors"],
                {"contractor_id", "contractor_name", "department", "salary"},
            )
        ]

        selected = entity_service.record_entity_selection(
            1, "contractors", "contractor_id", 1
        )

        self.assertEqual(
            selected,
            {
                "table_name": "contractors",
                "id_column": "contractor_id",
                "record_id": 1,
                "display_name": "Rahul Verma",
                "data": {
                    "contractor_name": "Rahul Verma",
                    "department": "IT",
                    "salary": 50000,
                },
            },
        )

    @patch.object(entity_service, "append_audit_event")
    @patch.object(entity_service, "_configured_tables_for_db")
    @patch.object(entity_service, "_can_search_table", return_value=True)
    @patch.object(entity_service, "get_db_connection")
    def test_nonexistent_selected_record_is_rejected(
        self, get_connection, _can_search, configured, _audit
    ):
        class Cursor:
            def execute(self, query, params=None):
                pass

            def fetchone(self):
                return None

            def close(self):
                pass

        class Connection:
            def cursor(self, **_kwargs):
                return Cursor()

            def close(self):
                pass

        get_connection.return_value = Connection()
        configured.return_value = [
            (
                "employees",
                entity_service.SEARCHABLE_TABLES["employees"],
                {"employee_id", "employee_name", "department", "salary"},
            )
        ]

        with self.assertRaisesRegex(
            entity_service.EntityResolutionDataError,
            "selected record no longer exists",
        ):
            entity_service.record_entity_selection(
                1, "employees", "employee_id", 999
            )

    @patch("backend.routes.entity_resolution.record_entity_selection")
    def test_selection_endpoint_accepts_match_context_and_returns_revalidated_match(
        self, select_record
    ):
        from backend.routes.entity_resolution import select_entity

        authoritative_match = {
            "table_name": "contractors",
            "id_column": "contractor_id",
            "record_id": 1,
            "display_name": "Rahul Verma",
            "data": {
                "contractor_name": "Rahul Verma",
                "department": "IT",
                "salary": 50000,
            },
        }
        select_record.return_value = authoritative_match
        request = EntitySelectionRequest(
            agent_id=1,
            table_name="contractors",
            id_column="contractor_id",
            record_id=1,
            display_name="Rahul Verma",
            data={"contractor_name": "Rahul Verma", "department": "IT"},
        )

        response = select_entity(request)

        select_record.assert_called_once_with(
            1, "contractors", "contractor_id", 1
        )
        self.assertEqual(response["match"], authoritative_match)

    def test_selected_record_context_is_in_existing_gemini_prompt(self):
        captured = {}

        class FakeModels:
            def generate_content(self, *, model, contents):
                captured["prompt"] = contents
                return SimpleNamespace(
                    text="UPDATE employees SET salary = 70000 WHERE employee_id = 101;"
                )

        class FakeClient:
            def __init__(self, **_kwargs):
                self.models = FakeModels()

        request = (
            "Update Rahul Verma's salary to 70000\n\n"
            "The user selected this record:\n"
            "table_name = employees\n"
            "id_column = employee_id\n"
            "record_id = 101\n"
            "display_name = Rahul Verma\n"
            'data = {"employee_name": "Rahul Verma", "department": "Finance"}'
        )
        with (
            patch.object(gemini_service, "API_KEY", "test-only"),
            patch.object(gemini_service.genai, "Client", FakeClient),
        ):
            sql = gemini_service.generate_sql(request)

        prompt = captured["prompt"].lower()
        self.assertIn("table_name = employees", prompt)
        self.assertIn("id_column = employee_id", prompt)
        self.assertIn("record_id = 101", prompt)
        self.assertIn('"department": "finance"', prompt)
        self.assertIn("where employee_id = 101", sql.lower())

    def test_query_still_requires_a_target_and_validation_remains_active(self):
        validation = validate_query(
            "UPDATE employees SET salary = 70000 WHERE employee_id = 101"
        )
        self.assertTrue(validation["valid"])
        self.assertEqual(validation["action"], "UPDATE")

        unrestricted = validate_query("DELETE FROM employees")
        self.assertFalse(unrestricted["valid"])
        self.assertEqual(unrestricted["risk_level"], "HIGH")

    @patch("backend.routes.query.get_db_connection")
    @patch("backend.routes.query.create_audit_log")
    @patch("backend.routes.query.append_audit_event")
    @patch(
        "backend.routes.query.authorize_request",
        return_value={"authorized": False, "reason": "Denied", "role": "ReadOnly"},
    )
    @patch(
        "backend.routes.query.validate_query",
        return_value={
            "valid": True,
            "risk_level": "LOW",
            "action": "UPDATE",
            "reason": "Query is valid",
        },
    )
    def test_execution_still_validates_checks_rbac_and_stops_when_denied(
        self, validate, authorize, _audit, _create_audit, get_connection
    ):
        from backend.routes.query import execute
        from backend.schemas import QueryRequest

        response = execute(
            QueryRequest(
                agent_id=1,
                query="UPDATE employees SET salary = 70000 WHERE employee_id = 3",
            )
        )

        validate.assert_called_once()
        authorize.assert_called_once_with(1, "UPDATE", "database")
        get_connection.assert_not_called()
        self.assertFalse(response.success)


if __name__ == "__main__":
    unittest.main()
