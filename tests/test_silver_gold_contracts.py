from datetime import date
from pathlib import Path

import yaml

from manufacturing_analytics.analytics.metrics import governed_production_metrics
from manufacturing_analytics.generator import ManufacturingDataGenerator
from manufacturing_analytics.generator.config import load_config

ROOT = Path(__file__).parents[1]
SILVER_SQL = (ROOT / "sql/transformations/010_silver_conformed.sql").read_text()
GOLD_SQL = (ROOT / "sql/metrics/020_gold_analytics.sql").read_text()


def test_all_silver_and_gold_models_are_declared() -> None:
    silver = {
        "silver_dim_date", "silver_dim_factory", "silver_dim_line", "silver_dim_product",
        "silver_dim_component", "silver_dim_supplier", "silver_dim_defect",
        "silver_fact_production", "silver_fact_quality_event",
    }
    gold = {
        "gold_manufacturing_daily", "gold_factory_quality", "gold_product_quality",
        "gold_supplier_quality", "gold_defect_pareto",
    }
    assert all(f"silver.{table}" in SILVER_SQL for table in silver)
    assert all(f"gold.{table}" in GOLD_SQL for table in gold)
    assert SILVER_SQL.count("CREATE OR REPLACE TABLE") == 9
    assert GOLD_SQL.count("CREATE OR REPLACE TABLE") == 5


def test_yaml_and_gold_implement_required_metric_contract() -> None:
    configured = set(yaml.safe_load((ROOT / "config/metrics.yaml").read_text())["metrics"])
    required = {
        "production_quantity", "pass_quantity", "fail_quantity", "fpy", "defect_rate",
        "dppm", "rework_rate", "scrap_rate", "yield_loss", "wow_fpy_change",
        "supplier_attributed_defect_rate",
    }
    assert required <= configured
    assert all(metric in GOLD_SQL.lower() for metric in required)


def test_metrics_and_incident_e_survive_analytical_aggregation() -> None:
    config = load_config(ROOT / "config/data_generation.yaml", seed=42, scale="test")
    production = ManufacturingDataGenerator(config).generate()["fact_production"]
    metrics = governed_production_metrics(production)
    assert metrics["production_quantity"] > 0
    assert 0 < metrics["fpy"] < 1
    assert abs(metrics["yield_loss"] - (1 - metrics["fpy"])) < 1e-12

    mexico = [row for row in production if row["factory_id"] == "FAC-MX"]
    before = [row for row in mexico if date(2026, 5, 6) <= row["production_date"] <= date(2026, 5, 31)]
    after = [row for row in mexico if date(2026, 6, 1) <= row["production_date"] <= date(2026, 6, 30)]
    assert governed_production_metrics(after)["fpy"] < governed_production_metrics(before)["fpy"]
    common = {row["product_id"] for row in before} & {row["product_id"] for row in after}
    changes = []
    for product_id in common:
        left = [row for row in before if row["product_id"] == product_id]
        right = [row for row in after if row["product_id"] == product_id]
        changes.append(abs(governed_production_metrics(right)["fpy"] - governed_production_metrics(left)["fpy"]))
    assert sum(changes) / len(changes) < 0.035

