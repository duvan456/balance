from django.test import SimpleTestCase
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch

from .models import Task
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
            "initial_rubro": 100000,
            "final_rubro": 199999,
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
            "initial_rubro": 100000,
            "final_rubro": 199999,
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
            "initial_rubro": 300000,
            "final_rubro": 100000,
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
            "initial_rubro": 650000,
            "final_rubro": 820000,
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
            "initial_rubro": 100000,
            "final_rubro": 199999,
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
            "initial_rubro": 150000,
            "final_rubro": 199999,
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
            "initial_rubro": 100000,
            "final_rubro": 199999,
            "page": 1,
            "page_size": 999,
        }

        serializer = MovementQuerySerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("page_size", serializer.errors)


class SourceRegistryTests(SimpleTestCase):
    def test_range_coverage_for_multiple_sources(self):
        coverage = resolve_rubro_interval_coverage(150000, 250000)

        self.assertEqual(len(coverage["covered"]), 2)
        self.assertEqual(coverage["source_tables"], ["dbo.Activo", "dbo.Pasivo"])

    def test_range_coverage_detects_unsupported_prefix(self):
        coverage = resolve_rubro_interval_coverage(650000, 820000)

        self.assertTrue(coverage["uncovered"])
        self.assertEqual(coverage["uncovered"][0]["prefix"], 7)
