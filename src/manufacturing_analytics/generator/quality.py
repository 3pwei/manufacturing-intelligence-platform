"""Generate unit outcomes and aggregate quality events from underlying risks."""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Any

from .config import GeneratorConfig
from .dimensions import COMPONENTS, SUPPLIERS
from .incidents import active
from .rng import DeterministicRng

COMPONENT_WEIGHTS = [0.18, 0.22, 0.18, 0.13, 0.14, 0.15]
SUPPLIER_WEIGHTS = [0.16, 0.17, 0.16, 0.12, 0.11, 0.10, 0.09, 0.09]
DEFECT_BY_COMPONENT = {
    "COMP-PWR": (["DEF-VOLT", "DEF-FUNC", "DEF-CONN"], [0.65, 0.20, 0.15]),
    "COMP-MAIN": (["DEF-FUNC", "DEF-VOLT", "DEF-ASSY"], [0.55, 0.25, 0.20]),
    "COMP-MEM": (["DEF-MEM", "DEF-FUNC", "DEF-CONN"], [0.72, 0.18, 0.10]),
    "COMP-NET": (["DEF-FUNC", "DEF-CONN", "DEF-ASSY"], [0.55, 0.30, 0.15]),
    "COMP-COOL": (["DEF-THERM", "DEF-FUNC", "DEF-ASSY"], [0.72, 0.18, 0.10]),
    "COMP-STOR": (["DEF-FUNC", "DEF-CONN", "DEF-ASSY"], [0.58, 0.25, 0.17]),
}


def _unit_driver(lot: dict[str, Any], config: GeneratorConfig, rng: DeterministicRng) -> tuple[str, str, str, str, float, bool]:
    day: date = lot["production_date"]
    component = rng.weighted(COMPONENTS, COMPONENT_WEIGHTS)["component_id"]
    supplier = rng.weighted(SUPPLIERS, SUPPLIER_WEIGHTS)["supplier_id"]
    component_lot = f"CLOT-{supplier[-1]}-{component[-3:]}-{day.strftime('%Y%m%d')}"
    risk = float(lot["baseline_failure_probability"])
    process_attributed = False

    if active("supplier_quality_degradation", day, config.enabled_incidents) and component == "COMP-PWR" and supplier == "SUP-B":
        risk += 0.18
    if (active("test_station_calibration", day, config.enabled_incidents)
            and lot["line_id"] == "LINE-MX-02"):
        risk += 0.10
        process_attributed = True
        component = "COMP-PWR"
    if active("line_ramp_up", day, config.enabled_incidents) and lot["line_id"] == "LINE-MY-03":
        elapsed = (day - date(2026, 2, 1)).days
        risk += 0.075 * max(0.0, 1.0 - elapsed / 120.0)
    if (active("bad_component_lot", day, config.enabled_incidents)
            and lot["factory_id"] == "FAC-TW" and lot["product_id"] == "PROD-X200"
            and rng.random() < 0.70):
        component, supplier, component_lot = "COMP-MEM", "SUP-C", "CLOT-BAD-001"
        risk += 0.32

    defects, weights = DEFECT_BY_COMPONENT[component]
    defect = rng.weighted(defects, weights)
    if process_attributed:
        defect = "DEF-VOLT"
        supplier = ""
    if component_lot == "CLOT-BAD-001":
        defect = "DEF-MEM"
    return component, supplier, component_lot, defect, min(risk, 0.85), process_attributed


def generate_outcomes(lots: list[dict[str, Any]], config: GeneratorConfig,
                      rng: DeterministicRng) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    production: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    event_sequence = 1
    for lot in lots:
        failures: dict[tuple[str, str, str, str, str], int] = defaultdict(int)
        rework = scrap = 0
        for _ in range(lot["planned_qty"]):
            component, supplier, component_lot, defect, risk, _ = _unit_driver(lot, config, rng)
            if rng.random() >= risk:
                continue
            ramp_early = lot["line_id"] == "LINE-MY-03" and lot["production_date"] < date(2026, 3, 15)
            scrap_flag = rng.random() < 0.12
            rework_flag = not scrap_flag and rng.random() < (0.82 if ramp_early else 0.62)
            rework += int(rework_flag)
            scrap += int(scrap_flag)
            stage = "test" if defect in {"DEF-VOLT", "DEF-FUNC", "DEF-MEM", "DEF-THERM"} else "in_process"
            failures[(component, supplier, component_lot, defect, stage + f"|{int(rework_flag)}|{int(scrap_flag)}")] += 1

        fail_qty = sum(failures.values())
        qty = lot["planned_qty"]
        production.append({
            "production_lot_id": lot["production_lot_id"], "production_date": lot["production_date"],
            "factory_id": lot["factory_id"], "line_id": lot["line_id"], "product_id": lot["product_id"],
            "production_qty": qty, "pass_qty": qty - fail_qty, "started_qty": qty,
            "completed_qty": qty, "first_pass_pass_qty": qty - fail_qty, "fail_qty": fail_qty,
            "rework_qty": rework, "scrap_qty": scrap,
        })
        for (component, supplier, component_lot, defect, flags), quantity in sorted(failures.items()):
            stage, is_rework, is_scrap = flags.split("|")
            events.append({
                "quality_event_id": f"QEV-{event_sequence:09d}", "event_date": lot["production_date"],
                "event_timestamp": f"{lot['production_date'].isoformat()}T12:00:00",
                "production_lot_id": lot["production_lot_id"], "factory_id": lot["factory_id"],
                "line_id": lot["line_id"], "product_id": lot["product_id"], "component_id": component,
                "supplier_id": supplier or None, "component_lot_id": component_lot,
                "defect_id": defect, "inspection_stage": stage, "event_quantity": quantity,
                "is_first_pass_failure": True, "is_rework": bool(int(is_rework)),
                "is_scrap": bool(int(is_scrap)),
                "disposition": "scrap" if int(is_scrap) else "rework" if int(is_rework) else "fail",
            })
            event_sequence += 1
    return production, events
