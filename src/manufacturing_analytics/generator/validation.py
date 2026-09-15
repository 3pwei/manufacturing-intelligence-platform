"""Dataset contract validation independent of output I/O."""

from __future__ import annotations

from datetime import date
from typing import Any

REQUIRED = {
    "fact_production": {"production_lot_id", "production_date", "factory_id", "line_id", "product_id", "production_qty", "pass_qty", "fail_qty", "rework_qty", "scrap_qty"},
    "fact_quality_event": {"quality_event_id", "event_date", "production_lot_id", "factory_id", "line_id", "product_id", "component_id", "supplier_id", "defect_id", "inspection_stage", "event_quantity", "is_first_pass_failure", "is_rework", "is_scrap"},
}


def validate_dataset(tables: dict[str, list[dict[str, Any]]], start: date, end: date) -> None:
    """Raise ValueError with all detected contract violations."""
    errors: list[str] = []
    for table, columns in REQUIRED.items():
        if not tables.get(table):
            errors.append(f"{table} is empty")
        elif missing := columns - set(tables[table][0]):
            errors.append(f"{table} missing columns: {sorted(missing)}")

    pk_specs = {"dim_date": "date_id", "dim_factory": "factory_id", "dim_line": "line_id",
                "dim_product": "product_id", "dim_component": "component_id",
                "dim_supplier": "supplier_id", "dim_defect": "defect_id",
                "fact_quality_event": "quality_event_id"}
    for table, key in pk_specs.items():
        values = [row[key] for row in tables[table]]
        if len(values) != len(set(values)):
            errors.append(f"{table}.{key} is not unique")

    productions = tables["fact_production"]
    natural_keys = [
        (r["production_date"], r["factory_id"], r["line_id"], r["product_id"], r["production_lot_id"])
        for r in productions
    ]
    if len(natural_keys) != len(set(natural_keys)):
        errors.append("fact_production natural key is not unique")

    references = [
        ("factory", tables["dim_factory"], "factory_id"),
        ("line", tables["dim_line"], "line_id"),
        ("product", tables["dim_product"], "product_id"),
        ("component", tables["dim_component"], "component_id"),
        ("supplier", tables["dim_supplier"], "supplier_id"),
        ("defect", tables["dim_defect"], "defect_id"),
    ]
    ids = {name: {row[key] for row in rows} for name, rows, key in references}
    lot_ids = {row["production_lot_id"] for row in productions}
    for row in productions:
        if not start <= row["production_date"] <= end:
            errors.append("production date outside configured range")
        if (
            row["factory_id"] not in ids["factory"]
            or row["line_id"] not in ids["line"]
            or row["product_id"] not in ids["product"]
        ):
            errors.append("production foreign key is invalid")
        quantities = [
            row[k]
            for k in ("production_qty", "pass_qty", "fail_qty", "rework_qty", "scrap_qty")
        ]
        if any(not isinstance(value, int) or value < 0 for value in quantities):
            errors.append("production quantities must be non-negative integers")
        if row["pass_qty"] + row["fail_qty"] != row["production_qty"]:
            errors.append("pass_qty + fail_qty must equal production_qty")
        if row["first_pass_pass_qty"] + row["fail_qty"] > row["started_qty"]:
            errors.append("first-pass quantities exceed started_qty")
        if row["rework_qty"] > row["fail_qty"] or row["scrap_qty"] > row["fail_qty"]:
            errors.append("rework/scrap exceeds fail_qty")
    for row in tables["fact_quality_event"]:
        if row["production_lot_id"] not in lot_ids:
            errors.append("quality event has orphan production lot")
        for field, group in (
            ("factory_id", "factory"),
            ("line_id", "line"),
            ("product_id", "product"),
            ("component_id", "component"),
            ("defect_id", "defect"),
        ):
            if row[field] not in ids[group]:
                errors.append(f"quality event has invalid {field}")
        if row["supplier_id"] is not None and row["supplier_id"] not in ids["supplier"]:
            errors.append("quality event has invalid supplier_id")
        if row["event_quantity"] <= 0 or row["inspection_stage"] not in {
            "incoming", "in_process", "final", "test"
        }:
            errors.append("quality event quantity/stage is invalid")
        if not start <= row["event_date"] <= end:
            errors.append("quality event date outside configured range")
    if errors:
        unique = list(dict.fromkeys(errors))
        raise ValueError("Dataset validation failed: " + "; ".join(unique))
