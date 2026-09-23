from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch

from .models import Task


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
