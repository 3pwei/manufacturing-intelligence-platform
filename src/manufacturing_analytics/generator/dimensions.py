"""Stable synthetic master data."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

FACTORIES = [
    {"factory_id": "FAC-TW", "factory_code": "TW01", "factory_name": "Taiwan Factory", "country": "Taiwan", "baseline_fpy": 0.980},
    {"factory_id": "FAC-MX", "factory_code": "MX01", "factory_name": "Mexico Factory", "country": "Mexico", "baseline_fpy": 0.965},
    {"factory_id": "FAC-MY", "factory_code": "MY01", "factory_name": "Malaysia Factory", "country": "Malaysia", "baseline_fpy": 0.970},
]
LINES = [
    {"line_id": "LINE-TW-01", "line_code": "TW-L1", "line_name": "Taiwan Line 1", "factory_id": "FAC-TW", "is_ramp_line": False},
    {"line_id": "LINE-TW-02", "line_code": "TW-L2", "line_name": "Taiwan Line 2", "factory_id": "FAC-TW", "is_ramp_line": False},
    {"line_id": "LINE-MX-01", "line_code": "MX-L1", "line_name": "Mexico Line 1", "factory_id": "FAC-MX", "is_ramp_line": False},
    {"line_id": "LINE-MX-02", "line_code": "MX-L2", "line_name": "Mexico Line 2", "factory_id": "FAC-MX", "is_ramp_line": False},
    {"line_id": "LINE-MY-01", "line_code": "MY-L1", "line_name": "Malaysia Line 1", "factory_id": "FAC-MY", "is_ramp_line": False},
    {"line_id": "LINE-MY-03", "line_code": "MY-L3", "line_name": "Malaysia Ramp Line", "factory_id": "FAC-MY", "is_ramp_line": True},
]
PRODUCTS = [
    {"product_id": "PROD-X100", "product_code": "X100", "product_name": "AI Server X100", "product_family": "AI Server", "complexity_risk": 0.000},
    {"product_id": "PROD-X200", "product_code": "X200", "product_name": "AI Server X200", "product_family": "AI Server", "complexity_risk": 0.014},
    {"product_id": "PROD-C100", "product_code": "C100", "product_name": "Compute Board C100", "product_family": "Board", "complexity_risk": 0.004},
    {"product_id": "PROD-N100", "product_code": "N100", "product_name": "Network Board N100", "product_family": "Board", "complexity_risk": 0.007},
    {"product_id": "PROD-S100", "product_code": "S100", "product_name": "Storage Node S100", "product_family": "Storage", "complexity_risk": 0.009},
]
COMPONENTS = [
    {"component_id": "COMP-PWR", "component_code": "PWR", "component_name": "Power Module", "component_family": "Power"},
    {"component_id": "COMP-MAIN", "component_code": "MAIN", "component_name": "Main Board", "component_family": "Compute"},
    {"component_id": "COMP-MEM", "component_code": "MEM", "component_name": "Memory Module", "component_family": "Memory"},
    {"component_id": "COMP-NET", "component_code": "NET", "component_name": "Network Module", "component_family": "Network"},
    {"component_id": "COMP-COOL", "component_code": "COOL", "component_name": "Cooling Module", "component_family": "Thermal"},
    {"component_id": "COMP-STOR", "component_code": "STOR", "component_name": "Storage Module", "component_family": "Storage"},
]
SUPPLIERS = [
    {"supplier_id": f"SUP-{letter}", "supplier_code": letter, "supplier_name": f"Supplier {letter}", "supplier_region": region}
    for letter, region in zip("ABCDEFGH", ["APAC", "APAC", "Americas", "EMEA", "APAC", "Americas", "EMEA", "APAC"], strict=True)
]
DEFECTS = [
    {"defect_id": "DEF-VOLT", "defect_code": "VOLT", "defect_name": "Voltage Failure", "defect_category": "Electrical", "severity": "High"},
    {"defect_id": "DEF-FUNC", "defect_code": "FUNC", "defect_name": "Functional Test Failure", "defect_category": "Functional", "severity": "High"},
    {"defect_id": "DEF-THERM", "defect_code": "THERM", "defect_name": "Thermal Failure", "defect_category": "Thermal", "severity": "High"},
    {"defect_id": "DEF-MEM", "defect_code": "MEM", "defect_name": "Memory Test Failure", "defect_category": "Electrical", "severity": "Medium"},
    {"defect_id": "DEF-ASSY", "defect_code": "ASSY", "defect_name": "Assembly Defect", "defect_category": "Assembly", "severity": "Medium"},
    {"defect_id": "DEF-CONN", "defect_code": "CONN", "defect_name": "Connector Defect", "defect_category": "Assembly", "severity": "Medium"},
]


def build_dimensions(start: date, end: date) -> dict[str, list[dict[str, Any]]]:
    dates: list[dict[str, Any]] = []
    current = start
    while current <= end:
        iso = current.isocalendar()
        dates.append({"date_id": int(current.strftime("%Y%m%d")), "date": current, "year": current.year,
                      "quarter": (current.month - 1) // 3 + 1, "month": current.month,
                      "week_of_year": iso.week, "day_of_week": current.isoweekday(),
                      "is_weekend": current.isoweekday() >= 6})
        current += timedelta(days=1)
    return {"dim_date": dates, "dim_factory": FACTORIES, "dim_line": LINES,
            "dim_product": PRODUCTS, "dim_component": COMPONENTS,
            "dim_supplier": SUPPLIERS, "dim_defect": DEFECTS}
