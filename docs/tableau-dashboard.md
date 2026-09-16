# Tableau Connection and Manufacturing Dashboard MVP

## Scope

PR #12 defines the Tableau Desktop implementation for:

```text
Databricks Gold → SQL Warehouse → Tableau Desktop → three dashboard MVP
```

It uses only `manufacturing_intelligence.gold`. Metric definitions remain governed by
`docs/metrics-definition.md` and the Gold models.

## Dashboard 1 — Executive Overview

Audience: manufacturing leadership. Target canvas: 1366 × 768, fixed desktop size.

Top row contains seven KPI cards:

1. Production Quantity
2. FPY
3. Defect Rate
4. DPPM
5. Rework Rate
6. Scrap Rate
7. WoW FPY Change (pp)

Below the cards, use one full-width weekly FPY line chart. A compact product-mix bar may appear
beside the trend only if it remains readable. Global filters: Date, Factory, Product.

Tooltip context:

- FPY is weighted by units and is not an average of subgroup percentages.
- WoW is a percentage-point change.
- A declining aggregate FPY may reflect product mix; use Product Quality before concluding that
  process quality deteriorated.

## Dashboard 2 — Manufacturing Quality

Audience: quality and operations engineers.

Use five uncluttered sheets:

- weighted FPY trend from Manufacturing Daily;
- production volume bars;
- fail quantity bars;
- rework and scrap trend;
- factory comparison and product comparison in one aligned comparison area.

Filters: Date, Factory, Product, Line. Present Factory → Product → Line as a visual investigation
sequence, not as a physical multi-table join. Selecting a factory or product should filter the
relevant downstream sheets through dashboard filter actions.

Recommended tooltip: production quantity, pass quantity, fail quantity, weighted FPY, rework rate,
scrap rate, and selected scope.

## Dashboard 3 — Root Cause Analysis

Audience: quality engineer performing a structured investigation.

Use four primary views:

- Defect Pareto: descending bars plus cumulative contribution line;
- Component contribution;
- Supplier contribution;
- Daily/weekly defect trend.

Filters/actions support Factory → Product → Line → Component → Supplier → Defect. Use Defect
Pareto for line/defect detail and Supplier Quality for component/supplier attribution. Do not join
the two fact-like Gold sources.

Supplier tooltips must include the attribution limitation documented in
`docs/silver-gold-model.md`.

## Product-mix evidence panel

Add a dedicated worksheet or dashboard zone named **Product Mix vs Product FPY** using Product
Quality:

- columns: Month of `production_date`;
- color: `product_id`;
- bars: production quantity or Product Mix Share;
- line or adjacent panel: Product FPY;
- filter: factory = `FAC-MX`;
- compare May 2026 with June 2026.

Required interpretation:

> Mexico aggregate FPY declines after June 1 while product-level FPY remains approximately stable.
> The production share shifts from X100 toward the normally lower-yield X200, so the aggregate
> movement is a product-mix effect and must not be labeled broad quality deterioration.

Do not average daily `fpy` or `product_mix_share`. Recompute FPY from pass/fail quantities and
recompute mix share from production quantity over the displayed period.

## Incident demo paths

| Incident | Date/scope | Dashboard path | Expected visual evidence |
|---|---|---|---|
| A | 2026-03-15–04-12 | RCA → Supplier/Component | Supplier B + Power Module concentration |
| B | 2026-04-15–05-05 | Quality/RCA → Mexico → Line 2 | localized voltage/test failures |
| C | 2026-02-01–05-31 | Quality → Malaysia → ramp line | high early rework, improving trend |
| D | 2026-05-10–05-16 | RCA → component/supplier/defect | narrow bad-lot symptom; lot identifier is not in Gold and exact lot proof remains SQL validation |
| E | 2026-05-01–06-30 | Executive → Product Mix panel | aggregate FPY down, stable product FPY, X100→X200 mix shift |

Incident D's exact `CLOT-BAD-001` identification requires the governed validation query that
currently reads Silver. Tableau remains Gold-only and shows the localized component/supplier/defect
symptom. Adding lot-level Gold evidence is a future model change, not a Tableau workaround.

## Visual design

- white background with restrained light-gray section bands;
- title 22–26 pt, section headers 15–18 pt, body/axis text at least 11 pt;
- consistent KPI colors: neutral navy, positive green, watch amber, adverse red;
- color must not be the only signal; include labels/arrows;
- no more than seven KPI cards and five analytical views per dashboard;
- use containers and consistent spacing; avoid floating overlaps;
- default tooltips explain the business meaning, scope, denominator, and caveat.

## Manual Tableau Desktop procedure

1. Connect to the five Gold tables using `tableau/README.md`.
2. Create the calculated fields from `tableau/calculated_fields.md`.
3. Build and validate individual sheets before assembling dashboards.
4. Apply Date, Factory, and Product filters to all compatible data sources using related field
   names; add Line/Component/Supplier/Defect only where present.
5. Configure filter actions instead of cross-grain joins.
6. Run `sql/validation/040_tableau_mvp_validation.sql` and reconcile unfiltered KPIs, May/June
   Mexico product mix, and incident slices.
7. Save the sanitized workbook and capture the four required screenshots.
8. Inspect the workbook/package for credentials before committing.

## Validation checklist

- all five Tableau data sources point to schema `gold`;
- no Bronze or Silver object appears in Tableau data-source metadata;
- unfiltered production, pass, fail, FPY, defect rate, DPPM, rework, and scrap match Databricks SQL;
- Date, Factory, Product, and Line filters update expected sheets;
- rates use aggregated numerators and denominators;
- Incident A–E visual paths produce the expected directional evidence;
- Incident E is described as product mix, not broad quality deterioration;
- workbook and Git history contain no token, password, personal path, or embedded credential.

## Tableau Public

1. Create a sanitized extract; Tableau Public cannot rely on a private live Databricks session.
2. Remove unused fields and verify that only synthetic Gold data is included.
3. Choose **Server → Tableau Public → Save to Tableau Public**.
4. Open the published workbook in a signed-out browser.
5. Recheck filters, tooltips, dashboard sizing, and all three dashboards.
6. Add the public URL to this document only after publication.

Publishing is a manual action because it requires the owner's Tableau Public account. Never publish
a workbook with an embedded Databricks token.
