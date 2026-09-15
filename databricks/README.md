# Databricks

- `jobs/`: serverless workflow definitions and thin entry points.
- Bronze core contracts/runtime: `src/manufacturing_analytics/bronze/`.
- Bootstrap DDL: `sql/ddl/001_bronze_foundation.sql`.
- Operational guide: `docs/databricks-bronze-ingestion.md`.

Silver and Gold remain future layers. Bronze contains no business KPI or analytical aggregation.
