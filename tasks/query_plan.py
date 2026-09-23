from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List, Optional


@dataclass
class SourcePlan:
    source_key: str
    table: str
    prefix: int
    start_rubro: int
    end_rubro: int
    informational: bool
    date_column: str
    semantic_date_type: str


@dataclass
class QueryPlan:
    date_type: str
    date_from: date
    date_to: date
    initial_rubro: int
    final_rubro: int
    customer_account: Optional[int] = None
    nit: Optional[str] = None
    branch: Optional[int] = None
    page: int = 1
    page_size: int = 100
    sorting: List[Dict[str, str]] = field(default_factory=list)
    sources: List[SourcePlan] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    uncovered_ranges: List[Dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "date_type": self.date_type,
            "date_from": self.date_from.isoformat(),
            "date_to": self.date_to.isoformat(),
            "initial_rubro": self.initial_rubro,
            "final_rubro": self.final_rubro,
            "customer_account": self.customer_account,
            "nit": self.nit,
            "branch": self.branch,
            "page": self.page,
            "page_size": self.page_size,
            "sorting": self.sorting,
            "sources": [
                {
                    "source_key": source.source_key,
                    "table": source.table,
                    "prefix": source.prefix,
                    "start_rubro": source.start_rubro,
                    "end_rubro": source.end_rubro,
                    "informational": source.informational,
                    "date_column": source.date_column,
                    "semantic_date_type": source.semantic_date_type,
                }
                for source in self.sources
            ],
            "warnings": self.warnings,
            "uncovered_ranges": self.uncovered_ranges,
        }
