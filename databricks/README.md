# Databricks

Planned Lakehouse layers:

- `bronze/`: raw ingestion and ingestion metadata
- `silver/`: cleaned, validated, conformed entities/events
- `gold/`: dimensional models, governed metrics, analytical views
- `jobs/`: orchestration definitions when the pipeline is implemented

PR #1 intentionally contains architecture only; pipeline code begins in later PRs.
