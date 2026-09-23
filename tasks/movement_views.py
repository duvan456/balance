import csv
import io
import uuid

from django.conf import settings
from django.http import HttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .query_compiler import build_column_metadata, compile_count_query, compile_query, normalize_row
from .query_planner import build_query_plan
from .serializers import MovementQuerySerializer
from .warehouse import execute_query


class MovementQueryView(APIView):
    def post(self, request):
        serializer = MovementQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            plan = build_query_plan(serializer.validated_data)
            sql, params = compile_query(plan)
            rows = execute_query(sql, params)
            count_sql, count_params = compile_count_query(plan)
            total_rows = execute_query(count_sql, count_params)
            total_count = int(total_rows[0]["row_count"]) if total_rows else 0

            normalized = [normalize_row(row) for row in rows]
            correlation_id = str(uuid.uuid4())
            payload = {
                "correlation_id": correlation_id,
                "columns": build_column_metadata(),
                "rows": normalized,
                "pagination": {
                    "page": plan.page,
                    "page_size": plan.page_size,
                    "has_next": (plan.page * plan.page_size) < total_count,
                },
                "summary": {
                    "movement_count_on_page": len(normalized),
                    "date_from": plan.date_from.isoformat(),
                    "date_to": plan.date_to.isoformat(),
                    "initial_rubro": plan.initial_rubro,
                    "final_rubro": plan.final_rubro,
                },
                "warnings": plan.warnings,
            }
            return Response(payload, status=status.HTTP_200_OK)
        except Exception:
            return Response({"detail": "No fue posible consultar movimientos."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class MovementExportView(APIView):
    def post(self, request):
        serializer = MovementQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            plan = build_query_plan(serializer.validated_data)
            max_rows = getattr(settings, "MOVEMENT_EXPORT_MAX_ROWS", 500000)
            if plan.page_size > max_rows:
                return Response({"detail": f"Export limit exceeded: {max_rows}."}, status=status.HTTP_400_BAD_REQUEST)

            sql, params = compile_query(plan)
            rows = execute_query(sql, params)
            normalized = [normalize_row(row) for row in rows]
            if len(normalized) > max_rows:
                return Response({"detail": f"Export limit exceeded: {max_rows}."}, status=status.HTTP_400_BAD_REQUEST)

            buffer = io.StringIO(newline="")
            writer = csv.writer(buffer, delimiter=",", quoting=csv.QUOTE_MINIMAL)
            headers = [column["label"] for column in build_column_metadata()]
            writer.writerow(headers)

            for row in normalized:
                safe_row = []
                for key in [column["key"] for column in build_column_metadata()]:
                    value = row.get(key)
                    if isinstance(value, str) and value and value[0] in "=+-@":
                        value = "'" + value
                    safe_row.append(value if value is not None else "")
                writer.writerow(safe_row)

            content = buffer.getvalue().encode("utf-8-sig")
            response = HttpResponse(content, content_type="text/csv; charset=utf-8")
            file_name = "movimientos.csv"
            response["Content-Disposition"] = f'attachment; filename="{file_name}"'
            response["X-Correlation-ID"] = str(uuid.uuid4())
            return response
        except Exception:
            return Response({"detail": "No fue posible exportar movimientos."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
