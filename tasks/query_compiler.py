from datetime import timedelta
from decimal import Decimal
from typing import Any, Dict, List, Tuple

from .query_plan import QueryPlan

SEMANTIC_COLUMN_ORDER = [
    "accounting_date",
    "accounting_value_date",
    "rubro",
    "rubro_description",
    "customer_account",
    "nit",
    "amount",
    "operation_type",
    "branch",
    "cost_center",
    "source_currency",
]

MOVEMENT_COLUMNS = [
    {"key": "accounting_date", "label": "Fecha contable", "type": "datetime"},
    {"key": "accounting_value_date", "label": "Fecha valor contable", "type": "datetime"},
    {"key": "rubro", "label": "Rubro", "type": "integer"},
    {"key": "rubro_description", "label": "Descripción rubro", "type": "string"},
    {"key": "customer_account", "label": "Cuenta cliente", "type": "integer"},
    {"key": "nit", "label": "NIT", "type": "string"},
    {"key": "amount", "label": "Importe", "type": "decimal"},
    {"key": "operation_type", "label": "Débito o crédito", "type": "string"},
    {"key": "branch", "label": "Sucursal", "type": "integer"},
    {"key": "cost_center", "label": "Centro de costo", "type": "integer"},
    {"key": "source_currency", "label": "Moneda", "type": "string"},
]


def qs(source_table: str) -> str:
    if source_table.endswith("Activo"):
        return "Modenaorigen"
    return "Modenaorigen"


def build_source_select(plan: QueryPlan, source) -> Tuple[str, List[Any]]:
    table = source.table
    date_column = source.date_column
    date_param_sql = "FechaContable >= ? AND FechaContable < ?" if plan.date_type == "ACCOUNTING_DATE" else "FechaVContable >= ? AND FechaVContable <= ?"
    extra_filters: List[str] = []
    params: List[Any] = []

    if plan.date_type == "ACCOUNTING_DATE":
        params.extend([plan.date_from, plan.date_to + timedelta(days=1)])
    else:
        params.extend([plan.date_from, plan.date_to])

    if source.start_rubro is not None:
        extra_filters.append("Rubro >= ?")
        params.append(source.start_rubro)
    if source.end_rubro is not None:
        extra_filters.append("Rubro <= ?")
        params.append(source.end_rubro)
    if plan.customer_account is not None:
        extra_filters.append("CuentaCliente = ?")
        params.append(plan.customer_account)
    if plan.nit is not None:
        extra_filters.append("NumeroDocumento = ?")
        params.append(plan.nit)
    if plan.branch is not None:
        extra_filters.append("Sucursal = ?")
        params.append(plan.branch)

    source_currency_field = qs(table)
    if table in {"dbo.Patrimonio", "dbo.CTARevInfo", "dbo.CTARevControl"}:
        source_currency_sql = "CAST(NULL AS DECIMAL(38, 6)) AS source_currency"
    else:
        source_currency_sql = f"{source_currency_field} AS source_currency"

    sql = f"""
        SELECT
            {date_column} AS accounting_date,
            FechaVcontable AS accounting_value_date,
            Rubro AS rubro,
            DescripcionRubro AS rubro_description,
            CuentaCliente AS customer_account,
            NumeroDocumento AS nit,
            Importe AS amount,
            CASE
                WHEN [Deb-Cred] = 1 THEN 'DEBIT'
                WHEN [Deb-Cred] = 2 THEN 'CREDIT'
                ELSE 'UNKNOWN'
            END AS operation_type,
            Sucursal AS branch,
            hccos AS cost_center,
            {source_currency_sql},
            CAST(NULL AS nvarchar(4000)) AS reference
        FROM {table}
        WHERE {date_param_sql}
          AND {' AND '.join(extra_filters) if extra_filters else '1 = 1'}
    """
    return sql, params


def compile_query(plan: QueryPlan) -> Tuple[str, List[Any]]:
    if not plan.sources:
        raise ValueError("No source tables were selected for the requested rubro range.")

    source_sql = []
    params = []
    for source in plan.sources:
        sql, source_params = build_source_select(plan, source)
        source_sql.append(sql)
        params.extend(source_params)

    union_sql = " UNION ALL ".join(source_sql)
    order_field = "accounting_date"
    order_direction = "ASC"
    if plan.sorting:
        first_sort = plan.sorting[0]
        order_field = first_sort.get("field", "accounting_date")
        order_direction = first_sort.get("direction", "asc").upper()

    offset = (plan.page - 1) * plan.page_size
    limit_sql = f"""
        SELECT * FROM (
            SELECT q.*, ROW_NUMBER() OVER (ORDER BY {order_field} {order_direction}) AS row_num
            FROM ({union_sql}) AS q
        ) AS ranked
        WHERE row_num > ? AND row_num <= ?
        ORDER BY row_num
    """
    compiled_params = list(params) + [offset, offset + plan.page_size]
    return limit_sql, compiled_params


def compile_count_query(plan: QueryPlan) -> Tuple[str, List[Any]]:
    if not plan.sources:
        raise ValueError("No source tables were selected for the requested rubro range.")

    source_sql = []
    params = []
    for source in plan.sources:
        sql, source_params = build_source_select(plan, source)
        source_sql.append(sql)
        params.extend(source_params)

    union_sql = " UNION ALL ".join(source_sql)
    return f"SELECT COUNT(*) AS row_count FROM ({union_sql}) AS union_rows", params


def normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(row)
    if "amount" in normalized and normalized["amount"] is not None:
        if not isinstance(normalized["amount"], Decimal):
            normalized["amount"] = Decimal(str(normalized["amount"]))
        normalized["amount"] = str(normalized["amount"])
    if "accounting_date" in normalized and normalized["accounting_date"] is not None:
        normalized["accounting_date"] = normalized["accounting_date"].isoformat() if hasattr(normalized["accounting_date"], "isoformat") else str(normalized["accounting_date"])
    if "accounting_value_date" in normalized and normalized["accounting_value_date"] is not None:
        normalized["accounting_value_date"] = normalized["accounting_value_date"].isoformat() if hasattr(normalized["accounting_value_date"], "isoformat") else str(normalized["accounting_value_date"])
    return normalized


def convert_to_string_decimal(value: Any) -> str:
    if value is None:
        return None
    return str(Decimal(str(value)))


def validate_order_field(field_name: str) -> bool:
    return field_name in {col["key"] for col in MOVEMENT_COLUMNS}


def build_column_metadata() -> List[Dict[str, str]]:
    return MOVEMENT_COLUMNS


def ensure_safe_text(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        begins = value.lstrip()
        if begins.startswith(("=", "+", "-", "@")):
            return "'" + value
        return value
    return value


def secret_name(value: str) -> str:
    return value


def get_sql_date_range(plan: QueryPlan) -> Tuple[str, List[Any]]:
    if plan.date_type == "ACCOUNTING_DATE":
        return "DateContable >= ? AND DateContable < ?", [plan.date_from, plan.date_to]
    return "FechaVContable >= ? AND FechaVContable <= ?", [plan.date_from, plan.date_to]


def get_rows_for_export(plan: QueryPlan, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [normalize_row(row) for row in rows]
