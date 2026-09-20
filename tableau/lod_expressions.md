# Tableau LOD Expressions — Advanced Analytics

These expressions solve explicit business-grain problems. They are evaluated against the
sanitized Gold extracts and must not be used to redefine Gold metrics.

## FIXED — Metric-aware benchmark

**Question:** While viewing product or line marks, how does each mark compare with its factory's
weighted FPY?

```tableau
{ FIXED [factory_id] : SUM([pass_quantity]) }
/
(
  { FIXED [factory_id] : SUM([pass_quantity]) }
  + { FIXED [factory_id] : SUM([fail_quantity]) }
)
```

Overall and Product variants use the same additive formula at `{ FIXED : ... }` and
`{ FIXED [product_id] : ... }`. Defect Rate, DPPM, Rework Rate, and Scrap Rate use the same
Overall/Factory/Product levels with their governed additive numerator and production denominator.
Date, Factory, and Product filters used to define the comparison cohort must be context filters;
ordinary dimension filters are applied after FIXED.

## INCLUDE — Component defect contribution

**Question:** In a supplier or product summary, how much of the selected failure cohort is
explained after adding component detail without permanently displaying Component?

```tableau
{ INCLUDE [component_id] : SUM([defect_quantity]) }
/
{ FIXED : SUM([defect_quantity]) }
```

Use only with the Defect Pareto Gold extract. Apply analysis cohort filters as context filters and
aggregate back to the displayed supplier/product grain.

## EXCLUDE — Product reference while drilling to Line

**Question:** When Line is added to a product view, what is the parent product FPY without the
line split?

```tableau
{ EXCLUDE [line_id] : SUM([pass_quantity]) }
/
(
  { EXCLUDE [line_id] : SUM([pass_quantity]) }
  + { EXCLUDE [line_id] : SUM([fail_quantity]) }
)
```

This keeps Product and Factory dimensions already present in the view and removes only Line.

## Validation rules

- Recompute every rate from additive quantities; never average row-level percentages.
- Test filter order explicitly: cohort filters are context filters for FIXED use cases.
- Compare Factory/Product LOD results with grouped Gold additive totals.
- Confirm INCLUDE totals aggregate back to the requested parent grain.
- Confirm EXCLUDE Line repeats the same product reference across all displayed lines.
