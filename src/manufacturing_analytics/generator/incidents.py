"""Incident windows and low-level risk modifiers."""

from __future__ import annotations

from datetime import date
from typing import Any

INCIDENTS: list[dict[str, Any]] = [
    {"incident_id": "INC-A", "incident_type": "supplier_quality_degradation", "start_date": "2026-03-15", "end_date": "2026-04-12", "affected_factory": None, "affected_line": None, "affected_product": None, "affected_component": "COMP-PWR", "affected_supplier": "SUP-B", "affected_defect": "DEF-VOLT", "expected_primary_driver": "Supplier B Power Module failure probability", "expected_direction": "increase", "description": "Supplier B Power Module quality degrades across consuming sites."},
    {"incident_id": "INC-B", "incident_type": "test_station_calibration", "start_date": "2026-04-15", "end_date": "2026-05-05", "affected_factory": "FAC-MX", "affected_line": "LINE-MX-02", "affected_product": None, "affected_component": None, "affected_supplier": None, "affected_defect": "DEF-VOLT", "expected_primary_driver": "Mexico Line 2 test-station process risk", "expected_direction": "increase", "description": "A line-local calibration drift raises voltage-test failures without supplier attribution."},
    {"incident_id": "INC-C", "incident_type": "line_ramp_up", "start_date": "2026-02-01", "end_date": "2026-05-31", "affected_factory": "FAC-MY", "affected_line": "LINE-MY-03", "affected_product": None, "affected_component": None, "affected_supplier": None, "affected_defect": "DEF-ASSY", "expected_primary_driver": "Ramp-line learning curve", "expected_direction": "decrease_over_time", "description": "A new Malaysia line begins with elevated failure and rework risk that decays smoothly."},
    {"incident_id": "INC-D", "incident_type": "bad_component_lot", "start_date": "2026-05-10", "end_date": "2026-05-16", "affected_factory": "FAC-TW", "affected_line": None, "affected_product": "PROD-X200", "affected_component": "COMP-MEM", "affected_supplier": "SUP-C", "affected_defect": "DEF-MEM", "affected_component_lot": "CLOT-BAD-001", "expected_primary_driver": "Concentrated bad memory component lot", "expected_direction": "increase", "description": "A short-lived Supplier C memory lot creates a localized failure spike."},
    {"incident_id": "INC-E", "incident_type": "product_mix_shift", "start_date": "2026-06-01", "end_date": "2026-06-30", "affected_factory": "FAC-MX", "affected_line": None, "affected_product": "PROD-X200", "affected_component": None, "affected_supplier": None, "affected_defect": None, "expected_primary_driver": "Shift from high-yield X100 to lower-yield X200", "expected_direction": "aggregate_fpy_decrease", "description": "Mexico product mix shifts while within-product failure probabilities remain unchanged."},
]


def active(incident_type: str, day: date, enabled: tuple[str, ...]) -> bool:
    if incident_type not in enabled:
        return False
    item = next(x for x in INCIDENTS if x["incident_type"] == incident_type)
    return date.fromisoformat(item["start_date"]) <= day <= date.fromisoformat(item["end_date"])


def manifest(enabled: tuple[str, ...]) -> list[dict[str, Any]]:
    return [item.copy() for item in INCIDENTS if item["incident_type"] in enabled]
