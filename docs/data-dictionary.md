# Initial Data Dictionary

This is a contract-level dictionary. Physical column types may be refined during implementation but field meaning and grain must remain consistent.

## `fact_production`

| Field | Meaning |
|---|---|
| production_date | Manufacturing reporting date |
| factory_id | FK to factory |
| line_id | FK to production line |
| product_id | FK to product |
| production_lot_id | Synthetic production lot identifier |
| production_qty | Alias for completed production quantity in the generator output |
| pass_qty | Alias for first-pass pass quantity in the generator output |
| started_qty | Units entering the defined production scope |
| completed_qty | Units completing the scope |
| first_pass_pass_qty | Units passing on first attempt |
| fail_qty | Units failing the first attempt |
| rework_qty | Units routed to rework |
| scrap_qty | Units scrapped |

## `fact_quality_event`

| Field | Meaning |
|---|---|
| quality_event_id | Unique synthetic event ID |
| event_date | Manufacturing reporting date of the event |
| event_timestamp | Event time |
| production_lot_id | Related production lot |
| component_lot_id | Synthetic supplier component-lot identifier; does not change fact grain |
| unit_id | Optional synthetic unit identifier |
| factory_id | Factory FK |
| line_id | Line FK |
| product_id | Product FK |
| component_id | Component FK when applicable |
| supplier_id | Supplier FK when attributable |
| defect_id | Defect/failure-mode FK |
| inspection_stage | Incoming / in-process / final / test |
| disposition | Pass / fail / rework / scrap |
| event_quantity | Number of units represented by the event record |
| is_first_pass_failure | Whether the event contributed to first-pass failure |
| is_rework | Whether affected units were routed to rework |
| is_scrap | Whether affected units were scrapped |

The generator emits aggregated inspection/failure events: records sharing a lot, component,
supplier, component lot, defect, stage, and disposition flags are represented by one row with an
additive `event_quantity`. `supplier_id` is nullable for process-attributed failures such as test
station calibration, preventing false supplier attribution.

## Dimension keys

All dimensions use stable surrogate IDs in analytical models and retain a readable synthetic business code for demos and debugging.

Implemented dimension attributes are documented by the generated CSV/Parquet schema and include
readable codes/names plus hierarchy attributes needed for drill-down. Scenario-only baseline risk
attributes are generator inputs and are not canonical metrics.
