"""Pure functions mirroring the governed additive metric contract."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


def sums(rows: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    columns = (
        "completed_qty",
        "first_pass_pass_qty",
        "fail_qty",
        "rework_qty",
        "scrap_qty",
    )
    return {column: sum(int(row[column]) for row in rows) for column in columns}


def governed_production_metrics(rows: Iterable[Mapping[str, Any]]) -> dict[str, float | int]:
    totals = sums(rows)
    fpy_denominator = totals["first_pass_pass_qty"] + totals["fail_qty"]
    production = totals["completed_qty"]
    fpy = totals["first_pass_pass_qty"] / fpy_denominator if fpy_denominator else 0.0
    return {
        "production_quantity": production,
        "pass_quantity": totals["first_pass_pass_qty"],
        "fail_quantity": totals["fail_qty"],
        "fpy": fpy,
        "defect_rate": totals["fail_qty"] / production if production else 0.0,
        "dppm": totals["fail_qty"] * 1_000_000 / production if production else 0.0,
        "rework_rate": totals["rework_qty"] / production if production else 0.0,
        "scrap_rate": totals["scrap_qty"] / production if production else 0.0,
        "yield_loss": 1.0 - fpy,
    }

