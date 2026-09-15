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
| event_timestamp | Event time |
| production_lot_id | Related production lot |
| unit_id | Optional synthetic unit identifier |
| factory_id | Factory FK |
| line_id | Line FK |
| product_id | Product FK |
| component_id | Component FK when applicable |
| supplier_id | Supplier FK when attributable |
| defect_id | Defect/failure-mode FK |
| inspection_stage | Incoming / in-process / final / test |
| disposition | Pass / fail / rework / scrap |

## Dimension keys

All dimensions use stable surrogate IDs in analytical models and retain a readable synthetic business code for demos and debugging.
