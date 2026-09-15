# Data Quality Rules

## Core production rules

- quantities are integers and non-negative;
- `first_pass_pass_qty + fail_qty <= started_qty`;
- `completed_qty <= started_qty` unless an explicitly documented carry-over rule is introduced;
- `rework_qty <= fail_qty` for the MVP process model;
- `scrap_qty <= fail_qty`;
- FPY derived from valid numerator/denominator is in `[0, 1]`;
- production natural key is unique at the documented fact grain.

## Referential integrity

All fact foreign keys must resolve to known dimensions unless the field is explicitly nullable by design.

## Quality-event rules

- `quality_event_id` is unique;
- event timestamp is within the generated scenario horizon;
- disposition and inspection stage use governed enumerations;
- attributable supplier/component fields are populated only where the scenario permits attribution;
- duplicate events must not inflate unit-based defect metrics.

## Pipeline behavior

Bronze preserves malformed or rejected source records for traceability. Silver must classify validation failures. Gold contains only records meeting documented analytical-quality rules or explicitly modeled exceptions.
