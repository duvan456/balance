from datetime import date
from typing import Any, Dict, List, Optional

from .query_plan import QueryPlan, SourcePlan
from .source_registry import SOURCE_REGISTRY, SUPPORTED_DATE_TYPES, resolve_rubro_interval_coverage


def build_query_plan(payload: Dict[str, Any]) -> QueryPlan:
    date_type = payload["date_type"]
    date_col = SUPPORTED_DATE_TYPES[date_type]

    initial_rubro = int(payload["initial_rubro"])
    final_rubro = int(payload["final_rubro"])
    coverage = resolve_rubro_interval_coverage(initial_rubro, final_rubro)
    if coverage["uncovered"]:
        uncovered = coverage["uncovered"]
        range_text = ", ".join(f"{segment['start']}-{segment['end']}" for segment in uncovered)
        warning = f"El rango solicitado incluye intervalos no configurados: {range_text}."
    else:
        warning = None

    sources: List[SourcePlan] = []
    for segment in coverage["covered"]:
        table = segment["table"]
        prefix = int(segment["prefix"])
        source_cfg = SOURCE_REGISTRY[prefix]
        sources.append(
            SourcePlan(
                source_key=source_cfg["source_key"],
                table=table,
                prefix=prefix,
                start_rubro=int(segment["start"]),
                end_rubro=int(segment["end"]),
                informational=bool(source_cfg.get("informational", False)),
                date_column=date_col,
                semantic_date_type=date_type,
            )
        )

    sort_list = payload.get("sorting") or [{"field": "accounting_date", "direction": "asc"}]
    query_plan = QueryPlan(
        date_type=date_type,
        date_from=payload["date_from"],
        date_to=payload["date_to"],
        initial_rubro=initial_rubro,
        final_rubro=final_rubro,
        customer_account=payload.get("customer_account"),
        nit=payload.get("nit"),
        branch=payload.get("branch"),
        page=int(payload.get("page", 1)),
        page_size=int(payload.get("page_size", 100)),
        sorting=sort_list,
        sources=sources,
        warnings=[warning] if warning else [],
        uncovered_ranges=coverage["uncovered"],
    )
    return query_plan
