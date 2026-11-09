from django.urls import path
from rest_framework.routers import DefaultRouter

from .movement_views import MovementExportView, MovementQueryView
from .views import GastoListView, IngresoListView, TaskViewSet


router = DefaultRouter()
router.register("tasks", TaskViewSet, basename="task")

urlpatterns = [
    *router.urls,
    path("ingresos/", IngresoListView.as_view(), name="ingreso-list"),
    path("gastos/", GastoListView.as_view(), name="gasto-list"),
    path("movements/query/", MovementQueryView.as_view(), name="movement-query"),
    path("movements/export/", MovementExportView.as_view(), name="movement-export"),
]
