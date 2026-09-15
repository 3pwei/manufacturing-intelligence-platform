from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest

from manufacturing_analytics.generator import ManufacturingDataGenerator
from manufacturing_analytics.generator.config import load_config
from manufacturing_analytics.generator.incidents import manifest
from manufacturing_analytics.generator.validation import validate_dataset


@pytest.fixture(scope="module")
def config():
    return load_config(Path("config/data_generation.yaml"), seed=42, scale="test")


@pytest.fixture(scope="module")
def tables(config):
    return ManufacturingDataGenerator(config).generate()


def _fpy(rows):
    passed = sum(row["pass_qty"] for row in rows)
    failed = sum(row["fail_qty"] for row in rows)
    return passed / (passed + failed)


def _canonical_hash(tables):
    payload = json.dumps(tables, default=str, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def test_config_parsing_and_overrides(tmp_path):
    parsed = load_config(Path("config/data_generation.yaml"), seed=7, output=tmp_path, scale="test")
    assert parsed.seed == 7
    assert parsed.output_path == tmp_path
    assert parsed.start_date == date(2026, 1, 1)
    assert parsed.end_date == date(2026, 6, 30)
    assert parsed.scale.lots_per_line_day == 1


def test_seed_is_deterministic(config):
    first = ManufacturingDataGenerator(config).generate()
    second = ManufacturingDataGenerator(config).generate()
    different = ManufacturingDataGenerator(replace(config, seed=43)).generate()
    assert _canonical_hash(first) == _canonical_hash(second)
    assert _canonical_hash(first) != _canonical_hash(different)


def test_dimension_keys_are_unique(tables):
    for table, key in {"dim_date": "date_id", "dim_factory": "factory_id", "dim_line": "line_id",
                       "dim_product": "product_id", "dim_component": "component_id",
                       "dim_supplier": "supplier_id", "dim_defect": "defect_id"}.items():
        values = [row[key] for row in tables[table]]
        assert len(values) == len(set(values))


def test_integrity_and_quantity_contract(tables, config):
    validate_dataset(tables, config.start_date, config.end_date)
    assert all(r["pass_qty"] + r["fail_qty"] == r["production_qty"] for r in tables["fact_production"])
    assert all(r["rework_qty"] <= r["fail_qty"] and r["scrap_qty"] <= r["fail_qty"] for r in tables["fact_production"])


def test_incident_a_supplier_power_defects_increase(tables):
    events = tables["fact_quality_event"]
    incident = sum(r["event_quantity"] for r in events if date(2026, 3, 15) <= r["event_date"] <= date(2026, 4, 12) and r["supplier_id"] == "SUP-B" and r["component_id"] == "COMP-PWR")
    baseline = sum(r["event_quantity"] for r in events if date(2026, 2, 14) <= r["event_date"] <= date(2026, 3, 14) and r["supplier_id"] == "SUP-B" and r["component_id"] == "COMP-PWR")
    assert incident > baseline * 2


def test_incident_b_line_voltage_failure_increase_without_supplier_blame(tables):
    events = tables["fact_quality_event"]
    incident = [r for r in events if date(2026, 4, 15) <= r["event_date"] <= date(2026, 5, 5) and r["line_id"] == "LINE-MX-02" and r["defect_id"] == "DEF-VOLT"]
    baseline = [r for r in events if date(2026, 3, 25) <= r["event_date"] <= date(2026, 4, 14) and r["line_id"] == "LINE-MX-02" and r["defect_id"] == "DEF-VOLT"]
    assert sum(r["event_quantity"] for r in incident) > sum(r["event_quantity"] for r in baseline) * 2
    assert sum(r["event_quantity"] for r in incident if r["supplier_id"] is None) > 0


def test_incident_c_ramp_learning_curve(tables):
    rows = [r for r in tables["fact_production"] if r["line_id"] == "LINE-MY-03"]
    early = [r for r in rows if date(2026, 2, 1) <= r["production_date"] <= date(2026, 2, 28)]
    late = [r for r in rows if date(2026, 5, 1) <= r["production_date"] <= date(2026, 5, 31)]
    early_rate = sum(r["rework_qty"] for r in early) / sum(r["completed_qty"] for r in early)
    late_rate = sum(r["rework_qty"] for r in late) / sum(r["completed_qty"] for r in late)
    assert early_rate > late_rate * 1.5


def test_incident_d_bad_component_lot_is_concentrated(tables):
    totals = defaultdict(int)
    for row in tables["fact_quality_event"]:
        if row["component_id"] == "COMP-MEM" and row["supplier_id"] == "SUP-C":
            totals[row["component_lot_id"]] += row["event_quantity"]
    bad = totals.pop("CLOT-BAD-001")
    assert bad > max(totals.values()) * 3


def test_incident_e_is_mix_not_within_product_deterioration(tables):
    rows = [r for r in tables["fact_production"] if r["factory_id"] == "FAC-MX"]
    before = [r for r in rows if date(2026, 5, 6) <= r["production_date"] <= date(2026, 5, 31)]
    after = [r for r in rows if date(2026, 6, 1) <= r["production_date"] <= date(2026, 6, 30)]
    assert _fpy(after) < _fpy(before) - 0.004
    common = {r["product_id"] for r in before} & {r["product_id"] for r in after}
    changes = []
    for product in common:
        product_before = [r for r in before if r["product_id"] == product]
        product_after = [r for r in after if r["product_id"] == product]
        changes.append(abs(_fpy(product_after) - _fpy(product_before)))
    assert sum(changes) / len(changes) < 0.035


def test_ground_truth_matches_enabled_incidents(config):
    truth = manifest(config.enabled_incidents)
    assert {item["incident_id"] for item in truth} == {"INC-A", "INC-B", "INC-C", "INC-D", "INC-E"}
    assert all(item["start_date"] <= item["end_date"] for item in truth)


def test_output_writes_csv_parquet_and_manifest(config, tmp_path):
    counts = ManufacturingDataGenerator(config).generate_to(tmp_path)
    assert counts["fact_production"] > 0
    assert (tmp_path / "fact_production.csv").exists()
    assert (tmp_path / "fact_production.parquet").exists()
    assert len(json.loads((tmp_path / "ground_truth/incidents.json").read_text())) == 5
