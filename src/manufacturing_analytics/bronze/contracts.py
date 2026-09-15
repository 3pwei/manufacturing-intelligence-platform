"""Source-shaped Bronze schemas and validation contracts.

The module deliberately contains no Spark imports so contracts can be reviewed and tested outside
Databricks. Expressions use Spark SQL syntax and are compiled by ``ingestion.py`` at runtime.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ColumnContract:
    name: str
    data_type: str
    nullable: bool = False


@dataclass(frozen=True)
class RuleContract:
    code: str
    message: str
    valid_when: str


@dataclass(frozen=True)
class ForeignKeyContract:
    columns: tuple[str, ...]
    parent_table: str
    parent_columns: tuple[str, ...]
    nullable: bool = False


@dataclass(frozen=True)
class TableContract:
    name: str
    columns: tuple[ColumnContract, ...]
    key_columns: tuple[str, ...]
    rules: tuple[RuleContract, ...] = ()
    foreign_keys: tuple[ForeignKeyContract, ...] = ()


def c(name: str, data_type: str, nullable: bool = False) -> ColumnContract:
    return ColumnContract(name, data_type, nullable)


def r(code: str, message: str, valid_when: str) -> RuleContract:
    return RuleContract(code, message, valid_when)


DATE_RANGE = (
    r(
        "DATE_OUT_OF_RANGE",
        "date is outside the 2026 synthetic horizon",
        "{date} BETWEEN DATE '2026-01-01' AND DATE '2026-06-30'",
    ),
)

TABLE_CONTRACTS: dict[str, TableContract] = {
    "dim_date": TableContract(
        "dim_date",
        (
            c("date_id", "INT"),
            c("date", "DATE"),
            c("year", "INT"),
            c("quarter", "INT"),
            c("month", "INT"),
            c("week_of_year", "INT"),
            c("day_of_week", "INT"),
            c("is_weekend", "BOOLEAN"),
        ),
        ("date_id",),
        tuple(
            r_.__class__(r_.code, r_.message, r_.valid_when.format(date="date"))
            for r_ in DATE_RANGE
        ),
    ),
    "dim_factory": TableContract(
        "dim_factory",
        (
            c("factory_id", "STRING"),
            c("factory_code", "STRING"),
            c("factory_name", "STRING"),
            c("country", "STRING"),
            c("baseline_fpy", "DOUBLE"),
        ),
        ("factory_id",),
        (
            r(
                "INVALID_BASELINE_FPY",
                "baseline_fpy must be between zero and one",
                "baseline_fpy BETWEEN 0.0 AND 1.0",
            ),
        ),
    ),
    "dim_line": TableContract(
        "dim_line",
        (
            c("line_id", "STRING"),
            c("line_code", "STRING"),
            c("line_name", "STRING"),
            c("factory_id", "STRING"),
            c("is_ramp_line", "BOOLEAN"),
        ),
        ("line_id",),
        foreign_keys=(ForeignKeyContract(("factory_id",), "dim_factory", ("factory_id",)),),
    ),
    "dim_product": TableContract(
        "dim_product",
        (
            c("product_id", "STRING"),
            c("product_code", "STRING"),
            c("product_name", "STRING"),
            c("product_family", "STRING"),
            c("complexity_risk", "DOUBLE"),
        ),
        ("product_id",),
        (
            r(
                "NEGATIVE_COMPLEXITY_RISK",
                "complexity_risk must be non-negative",
                "complexity_risk >= 0.0",
            ),
        ),
    ),
    "dim_component": TableContract(
        "dim_component",
        (
            c("component_id", "STRING"),
            c("component_code", "STRING"),
            c("component_name", "STRING"),
            c("component_family", "STRING"),
        ),
        ("component_id",),
    ),
    "dim_supplier": TableContract(
        "dim_supplier",
        (
            c("supplier_id", "STRING"),
            c("supplier_code", "STRING"),
            c("supplier_name", "STRING"),
            c("supplier_region", "STRING"),
        ),
        ("supplier_id",),
    ),
    "dim_defect": TableContract(
        "dim_defect",
        (
            c("defect_id", "STRING"),
            c("defect_code", "STRING"),
            c("defect_name", "STRING"),
            c("defect_category", "STRING"),
            c("severity", "STRING"),
        ),
        ("defect_id",),
    ),
    "fact_production": TableContract(
        "fact_production",
        (
            c("production_lot_id", "STRING"),
            c("production_date", "DATE"),
            c("factory_id", "STRING"),
            c("line_id", "STRING"),
            c("product_id", "STRING"),
            c("production_qty", "BIGINT"),
            c("pass_qty", "BIGINT"),
            c("started_qty", "BIGINT"),
            c("completed_qty", "BIGINT"),
            c("first_pass_pass_qty", "BIGINT"),
            c("fail_qty", "BIGINT"),
            c("rework_qty", "BIGINT"),
            c("scrap_qty", "BIGINT"),
        ),
        ("production_date", "factory_id", "line_id", "product_id", "production_lot_id"),
        (
            r(
                "DATE_OUT_OF_RANGE",
                "production_date is outside the synthetic horizon",
                "production_date BETWEEN DATE '2026-01-01' AND DATE '2026-06-30'",
            ),
            r(
                "NEGATIVE_QUANTITY",
                "production quantities must be non-negative",
                "production_qty >= 0 AND pass_qty >= 0 AND started_qty >= 0 AND completed_qty >= 0 AND first_pass_pass_qty >= 0 AND fail_qty >= 0 AND rework_qty >= 0 AND scrap_qty >= 0",
            ),
            r(
                "INVALID_PRODUCTION_TOTAL",
                "pass_qty plus fail_qty must equal production_qty",
                "pass_qty + fail_qty = production_qty",
            ),
            r(
                "COMPLETED_EXCEEDS_STARTED",
                "completed_qty must not exceed started_qty",
                "completed_qty <= started_qty",
            ),
            r(
                "FIRST_PASS_EXCEEDS_STARTED",
                "first-pass quantities must not exceed started_qty",
                "first_pass_pass_qty + fail_qty <= started_qty",
            ),
            r(
                "REWORK_EXCEEDS_FAILURES",
                "rework_qty must not exceed fail_qty",
                "rework_qty <= fail_qty",
            ),
            r(
                "SCRAP_EXCEEDS_FAILURES",
                "scrap_qty must not exceed fail_qty",
                "scrap_qty <= fail_qty",
            ),
        ),
        (
            ForeignKeyContract(("factory_id",), "dim_factory", ("factory_id",)),
            ForeignKeyContract(("line_id",), "dim_line", ("line_id",)),
            ForeignKeyContract(("product_id",), "dim_product", ("product_id",)),
        ),
    ),
    "fact_quality_event": TableContract(
        "fact_quality_event",
        (
            c("quality_event_id", "STRING"),
            c("event_date", "DATE"),
            c("event_timestamp", "TIMESTAMP"),
            c("production_lot_id", "STRING"),
            c("factory_id", "STRING"),
            c("line_id", "STRING"),
            c("product_id", "STRING"),
            c("component_id", "STRING"),
            c("supplier_id", "STRING", True),
            c("component_lot_id", "STRING"),
            c("defect_id", "STRING"),
            c("inspection_stage", "STRING"),
            c("event_quantity", "BIGINT"),
            c("is_first_pass_failure", "BOOLEAN"),
            c("is_rework", "BOOLEAN"),
            c("is_scrap", "BOOLEAN"),
            c("disposition", "STRING"),
        ),
        ("quality_event_id",),
        (
            r(
                "DATE_OUT_OF_RANGE",
                "event_date is outside the synthetic horizon",
                "event_date BETWEEN DATE '2026-01-01' AND DATE '2026-06-30'",
            ),
            r(
                "TIMESTAMP_DATE_MISMATCH",
                "event timestamp must fall on event_date",
                "TO_DATE(event_timestamp) = event_date",
            ),
            r("INVALID_EVENT_QUANTITY", "event_quantity must be positive", "event_quantity > 0"),
            r(
                "INVALID_INSPECTION_STAGE",
                "inspection_stage is not governed",
                "inspection_stage IN ('incoming', 'in_process', 'final', 'test')",
            ),
            r(
                "INVALID_DISPOSITION",
                "disposition is not governed",
                "disposition IN ('fail', 'rework', 'scrap')",
            ),
        ),
        (
            ForeignKeyContract(("production_lot_id",), "fact_production", ("production_lot_id",)),
            ForeignKeyContract(("factory_id",), "dim_factory", ("factory_id",)),
            ForeignKeyContract(("line_id",), "dim_line", ("line_id",)),
            ForeignKeyContract(("product_id",), "dim_product", ("product_id",)),
            ForeignKeyContract(("component_id",), "dim_component", ("component_id",)),
            ForeignKeyContract(("supplier_id",), "dim_supplier", ("supplier_id",), True),
            ForeignKeyContract(("defect_id",), "dim_defect", ("defect_id",)),
        ),
    ),
}

INGESTION_ORDER = (
    "dim_date",
    "dim_factory",
    "dim_line",
    "dim_product",
    "dim_component",
    "dim_supplier",
    "dim_defect",
    "fact_production",
    "fact_quality_event",
)
