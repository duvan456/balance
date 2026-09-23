SOURCE_REGISTRY = {
    1: {
        "source_key": "ASSET",
        "table": "dbo.Activo",
        "informational": False,
        "prefix_range": (100000, 199999),
    },
    2: {
        "source_key": "LIABILITY",
        "table": "dbo.Pasivo",
        "informational": False,
        "prefix_range": (200000, 299999),
    },
    3: {
        "source_key": "EQUITY",
        "table": "dbo.Patrimonio",
        "informational": False,
        "prefix_range": (300000, 399999),
    },
    4: {
        "source_key": "INCOME",
        "table": "dbo.Ingreso",
        "informational": False,
        "prefix_range": (400000, 499999),
    },
    5: {
        "source_key": "EXPENSE",
        "table": "dbo.Gasto",
        "informational": False,
        "prefix_range": (500000, 599999),
    },
    6: {
        "source_key": "INFORMATIONAL_ACCOUNT",
        "table": "dbo.CTARevInfo",
        "informational": True,
        "prefix_range": (600000, 699999),
    },
    8: {
        "source_key": "CONTROL_ACCOUNT",
        "table": "dbo.CTARevControl",
        "informational": True,
        "prefix_range": (800000, 899999),
    },
}

SUPPORTED_DATE_TYPES = {
    "ACCOUNTING_DATE": "FechaContable",
    "ACCOUNTING_VALUE_DATE": "FechaVContable",
}

UNSUPPORTED_PREFIXES = (0, 7, 9)


def resolve_rubro_interval_coverage(initial_rubro, final_rubro):
    """Returns the configured and unsupported segments for a rubric interval."""
    if initial_rubro > final_rubro:
        raise ValueError("initial_rubro cannot be greater than final_rubro")

    covered = []
    uncovered = []

    for prefix, config in sorted(SOURCE_REGISTRY.items()):
        start, end = config["prefix_range"]
        if initial_rubro <= end and final_rubro >= start:
            covered.append(
                {
                    "prefix": prefix,
                    "source_key": config["source_key"],
                    "table": config["table"],
                    "start": max(initial_rubro, start),
                    "end": min(final_rubro, end),
                }
            )

    for prefix in UNSUPPORTED_PREFIXES:
        start = prefix * 100000
        end = start + 99999
        if initial_rubro <= end and final_rubro >= start:
            uncovered.append(
                {
                    "prefix": prefix,
                    "start": max(initial_rubro, start),
                    "end": min(final_rubro, end),
                }
            )

    return {
        "covered": covered,
        "uncovered": uncovered,
        "source_tables": [segment["table"] for segment in covered],
    }
