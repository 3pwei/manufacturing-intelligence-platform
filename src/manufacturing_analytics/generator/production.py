"""Baseline lot production and product-mix generation."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from .config import GeneratorConfig
from .dimensions import FACTORIES, LINES, PRODUCTS
from .incidents import active
from .rng import DeterministicRng

BASE_MIX = {
    "FAC-TW": [0.35, 0.20, 0.20, 0.15, 0.10],
    "FAC-MX": [0.50, 0.18, 0.10, 0.12, 0.10],
    "FAC-MY": [0.25, 0.15, 0.18, 0.20, 0.22],
}


def _product(factory_id: str, day: Any, config: GeneratorConfig, rng: DeterministicRng) -> dict[str, Any]:
    weights = BASE_MIX[factory_id]
    if factory_id == "FAC-MX" and active("product_mix_shift", day, config.enabled_incidents):
        weights = [0.05, 0.80, 0.05, 0.05, 0.05]
    return rng.weighted(PRODUCTS, weights)


def generate_lot_plans(config: GeneratorConfig, rng: DeterministicRng) -> list[dict[str, Any]]:
    factories = {item["factory_id"]: item for item in FACTORIES}
    rows: list[dict[str, Any]] = []
    day = config.start_date
    lot_sequence = 1
    while day <= config.end_date:
        for line in LINES:
            if line["is_ramp_line"] and day < __import__("datetime").date(2026, 2, 1):
                continue
            factory = factories[line["factory_id"]]
            for _ in range(config.scale.lots_per_line_day):
                product = _product(line["factory_id"], day, config, rng)
                rows.append({
                    "production_lot_id": f"PLOT-{lot_sequence:08d}", "production_date": day,
                    "factory_id": line["factory_id"], "line_id": line["line_id"],
                    "product_id": product["product_id"],
                    "planned_qty": rng.randint(config.scale.lot_quantity_min, config.scale.lot_quantity_max),
                    "baseline_failure_probability": 1.0 - factory["baseline_fpy"] + product["complexity_risk"],
                })
                lot_sequence += 1
        day += timedelta(days=1)
    return rows
