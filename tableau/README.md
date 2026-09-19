# Tableau Manufacturing Dashboard MVP

PR #12 connects Tableau Desktop to the governed Databricks Gold layer and defines a five-minute
manufacturing-quality demo. Tableau must not read Bronze or Silver.

## Data flow

```text
manufacturing_intelligence.gold
→ Databricks SQL Warehouse
→ Tableau Desktop
→ Executive Overview / Manufacturing Quality / Root Cause Analysis
```

## Allowed data sources

Use live connections while building and validating. Each Tableau data source must point to exactly
one Gold table.

| Tableau data source | Gold table | Primary use |
|---|---|---|
| Manufacturing Daily | `gold_manufacturing_daily` | production KPIs, trends, line analysis |
| Factory Quality | `gold_factory_quality` | factory comparison |
| Product Quality | `gold_product_quality` | product comparison and product mix |
| Supplier Quality | `gold_supplier_quality` | supplier/component contribution |
| Defect Pareto | `gold_defect_pareto` | defect Pareto and defect trend |

Do not create cross-table physical joins. The tables have different grains; joining them can
multiply additive measures. Dashboard filter actions may pass Date, Factory, Product, Line,
Component, Supplier, or Defect values between sheets.

## Desktop connection

1. Start the Databricks Serverless Starter Warehouse.
2. In Tableau Desktop select **Connect → To a Server → Databricks**.
3. Enter the workspace Server Hostname and HTTP Path shown in the warehouse connection details.
4. Authenticate interactively. Do not save a token or credentials in the repository.
5. Select catalog `manufacturing_intelligence`, schema `gold`, and the five tables above.
6. Rename the Tableau data sources as listed above.
7. Confirm a row count and date range before building sheets.

## Workbook contract

Save the editable workbook as `tableau/manufacturing_dashboard_mvp.twb` when the live connection
uses no embedded secret. Use `tableau/manufacturing_dashboard_mvp.twbx` only for a sanitized
portfolio export. Before committing either format, inspect it for hostname, username, token,
personal paths, or embedded credentials.

Screenshots belong under `tableau/screenshots/`:

- `executive-overview.png`
- `manufacturing-quality.png`
- `root-cause-analysis.png`
- `incident-e-product-mix.png`

The workbook and screenshots are created in Tableau Desktop; this repository does not generate
Tableau XML.

## Dashboard build

Follow `docs/tableau-dashboard.md` for sheet layout, filters, formatting, Incident A–E demo paths,
validation, and Tableau Public publication. Calculated fields are defined in
`tableau/calculated_fields.md`.

## Published portfolio views

- [Manufacturing Executive Overview](https://public.tableau.com/app/profile/.60581246/viz/manufacturing_intelligence_public_sanitized/ExecutiveOverview)
- [Manufacturing Quality](https://public.tableau.com/app/profile/.60581246/viz/manufacturing_intelligence_public_sanitized/ManufacturingQuality)
- [Root Cause Analysis](https://public.tableau.com/app/profile/.60581246/viz/manufacturing_intelligence_public_sanitized/RootCauseAnalysis)

These public views use sanitized embedded extracts containing only deterministic synthetic data.
They do not use the private live Databricks connection described above and contain no hostname,
warehouse path, access token, or embedded credential.

## Validation

Run `databricks bundle run -t dev tableau_mvp_validation`. The serverless job executes
`sql/validation/040_tableau_mvp_validation.sql`, prints machine-readable PASS/FAIL events, and
fails closed when any check fails. Tableau manual validation is limited to filter/action behavior,
layout, tooltips, and credential inspection. KPI values must still be recomputed from additive
numerators and denominators; never average row-level percentages.
