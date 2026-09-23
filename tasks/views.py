from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Task
from .serializers import TaskSerializer
from .warehouse import fetch_rows


class WarehouseReadOnlyView(APIView):
    query = ""

    def get(self, request):
        try:
            return Response(fetch_rows(self.query))
        except Exception:
            return Response(
                {"detail": "No fue posible consultar el data warehouse."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )


class IngresoListView(WarehouseReadOnlyView):
    query = """
        SELECT TOP (10000)
            [FechaContable], [Rubro], [DescripcionRubro], [CuentaCliente],
            [NumeroDocumento], [Nombre], [Importe], [Sucursal], [Deb-Cred],
            [hccos], [hsubop], [FechaVcontable], [Concatenated_Fields]
        FROM [dbo].[Ingreso]
    """


class GastoListView(WarehouseReadOnlyView):
    query = """
        SELECT TOP (10000)
            [FechaContable], [Rubro], [DescripcionRubro], [CuentaCliente],
            [NumeroDocumento], [Nombre], [Importe], [Sucursal], [Deb-Cred],
            [FechaVcontable], [hccos], [hsubop]
        FROM [dbo].[Gasto]
    """


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
