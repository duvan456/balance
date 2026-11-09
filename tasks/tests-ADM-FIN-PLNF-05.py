from django.test import SimpleTestCase
from datetime import date
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch

from .models import Task
from .query_compiler import compile_query
from .query_planner import build_query_plan
from .serializers import MovementQuerySerializer
from .source_registry import resolve_rubro_interval_coverage


class TaskApiTests(APITestCase):
    def test_create_and_list_tasks(self):
        create_response = self.client.post(
            "/api/tasks/",
            {"title": "Ship API", "description": "Publish the first version"},
            format="json",
        )

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(create_response.data["status"], Task.Status.TODO)

        list_response = self.client.get("/api/tasks/")

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 1)
        self.assertEqual(list_response.data[0]["title"], "Ship API")

    def test_update_task_status(self):
        task = Task.objects.create(title="Write tests")

        response = self.client.patch(
            f"/api/tasks/{task.pk}/",
            {"status": Task.Status.DONE},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Task.Status.DONE)


class WarehouseApiTests(APITestCase):
    @patch("tasks.views.fetch_rows")
    def test_list_ingresos_is_read_only_endpoint(self, fetch_rows):
        fetch_rows.return_value = [{"Rubro": "101", "Importe": 1250}]

        response = self.client.get("/api/ingresos/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, fetch_rows.return_value)
        fetch_rows.assert_called_once()

    @patch("tasks.views.fetch_rows")
    def test_list_gastos_is_read_only_endpoint(self, fetch_rows):
        fetch_rows.return_value = [{"Rubro": "202", "Importe": 500}]

        response = self.client.get("/api/gastos/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, fetch_rows.return_value)
        fetch_rows.assert_called_once()


class MovementQuerySerializerTests(SimpleTestCase):
    def test_valid_accounting_date_query(self):
        payload = {
            "date_type": "ACCOUNTING_DATE",
            "date_from": "2026-08-01",
            "date_to": "2026-08-31",
            "initial_rubro": 1000000000,
            "final_rubro": 1999999999,
            "page": 1,
            "page_size": 100,
            "sorting": [{"field": "accounting_date", "direction": "asc"}],
        }

        serializer = MovementQuerySerializer(data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_invalid_date_range_is_rejected(self):
        payload = {
            "date_type": "ACCOUNTING_DATE",
            "date_from": "2026-08-31",
            "date_to": "2026-08-01",
            "initial_rubro": 1000000000,
            "final_rubro": 1999999999,
            "page": 1,
            "page_size": 25,
        }

        serializer = MovementQuerySerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("date_from", serializer.errors)

    def test_invalid_rubro_range_is_rejected(self):
        payload = {
            "date_type": "ACCOUNTING_DATE",
            "date_from": "2026-08-01",
            "date_to": "2026-08-31",
            "initial_rubro": 3000000000,
            "final_rubro": 1000000000,
            "page": 1,
            "page_size": 25,
        }

        serializer = MovementQuerySerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("initial_rubro", serializer.errors)

    def test_unsupported_interval_is_rejected(self):
        payload = {
            "date_type": "ACCOUNTING_DATE",
            "date_from": "2026-08-01",
            "date_to": "2026-08-31",
            "initial_rubro": 6500000000,
            "final_rubro": 8200000000,
            "page": 1,
            "page_size": 25,
        }

        serializer = MovementQuerySerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("initial_rubro", serializer.errors)

    def test_sorts_only_authorized_fields(self):
        payload = {
            "date_type": "ACCOUNTING_DATE",
            "date_from": "2026-08-01",
            "date_to": "2026-08-31",
            "initial_rubro": 1000000000,
            "final_rubro": 1999999999,
            "page": 1,
            "page_size": 25,
            "sorting": [{"field": "customer_name", "direction": "asc"}],
        }

        serializer = MovementQuerySerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("sorting", serializer.errors)

    def test_nit_is_treated_as_text(self):
        payload = {
            "date_type": "ACCOUNTING_VALUE_DATE",
            "date_from": "2026-08-01",
            "date_to": "2026-08-31",
            "initial_rubro": 1500000000,
            "final_rubro": 1999999999,
            "nit": "001234567-9",
            "page": 1,
            "page_size": 25,
        }

        serializer = MovementQuerySerializer(data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["nit"], "001234567-9")

    def test_page_size_respects_global_limit(self):
        payload = {
            "date_type": "ACCOUNTING_DATE",
            "date_from": "2026-08-01",
            "date_to": "2026-08-31",
            "initial_rubro": 1000000000,
            "final_rubro": 1999999999,
            "page": 1,
            "page_size": 999,
        }

        serializer = MovementQuerySerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("page_size", serializer.errors)

    def test_rubro_requires_ten_positive_digits(self):
        payload = {
            "date_type": "ACCOUNTING_DATE",
            "date_from": "2026-08-01",
            "date_to": "2026-08-31",
            "initial_rubro": 999999999,
            "final_rubro": 1999999999,
            "page": 1,
            "page_size": 25,
        }

        serializer = MovementQuerySerializer(data=payload)

        self.assertFalse(serializer.is_valid())
        self.assertIn("initial_rubro", serializer.errors)

    def test_rubro_rejects_more_than_ten_digits(self):
        payload = {
            "date_type": "ACCOUNTING_DATE",
            "date_from": "2026-08-01",
            "date_to": "2026-08-31",
            "initial_rubro": 1000000000,
            "final_rubro": 10000000000,
            "page": 1,
            "page_size": 25,
        }

        serializer = MovementQuerySerializer(data=payload)

        self.assertFalse(serializer.is_valid())
        self.assertIn("final_rubro", serializer.errors)


class MovementQueryCompilerTests(SimpleTestCase):
    def test_source_currency_is_nullable_when_column_is_unavailable(self):
        plan = build_query_plan(
            {
                "date_type": "ACCOUNTING_DATE",
                "date_from": date(2026, 8, 1),
                "date_to": date(2026, 8, 31),
                "initial_rubro": 1100000000,
                "final_rubro": 1999999999,
                "page": 1,
                "page_size": 50,
                "sorting": [{"field": "accounting_date", "direction": "asc"}],
            }
        )

        sql, _ = compile_query(plan)

        self.assertIn("CAST(NULL AS nvarchar(32)) AS source_currency", sql)
        self.assertNotIn("MonedaOrigen", sql)


class SourceRegistryTests(SimpleTestCase):
    def test_range_coverage_for_multiple_sources(self):
        coverage = resolve_rubro_interval_coverage(1500000000, 2500000000)

        self.assertEqual(len(coverage["covered"]), 2)
        self.assertEqual(coverage["source_tables"], ["dbo.Activo", "dbo.Pasivo"])

    def test_range_coverage_detects_unsupported_prefix(self):
        coverage = resolve_rubro_interval_coverage(6500000000, 8200000000)

        self.assertTrue(coverage["uncovered"])
        self.assertEqual(coverage["uncovered"][0]["prefix"], 7)
