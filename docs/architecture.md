# Architecture

## Objective

Provide a modular analytics path from reproducible synthetic manufacturing data to governed business metrics, Tableau analysis, and evidence-grounded AI explanations.

```mermaid
flowchart TD
    A[Synthetic Data Specification] --> B[Python Data Generator]
    B --> S[Read-only S3 external location]
    S --> V[Schema enforcement and DQ]
    V -->|valid| C[Bronze: source-shaped Delta]
    V -->|invalid| Q[Quarantine: record and errors]
    C --> D[Silver: cleaned and conformed data]
    D --> E[Gold: dimensional model and business metrics]
    E --> F[Governed SQL / Semantic Views]
    F --> G[Tableau Dashboards]
    F --> H[AI Analytics Agent]
    G --> I[Business Stakeholder]
    H --> I
```

## Layer responsibilities

### Synthetic generator
Creates deterministic manufacturing, quality, and later supply-chain/RMA events. It also injects known incidents so analytical findings can be regression-tested.

### Bronze
Reads Parquet through the Unity Catalog external location, enforces the PR #2 physical schema,
and preserves source-shaped valid records with ingestion metadata in managed Delta tables.
File-level audit plus existing-key checks provide basic rerun idempotency. No business KPI logic
belongs here.

### Quarantine
Preserves the original rejected record, source file, batch, error code/message, and quarantine
timestamp. It is an explicit observability path, not a silent filter. Dimensions load before facts
so basic FK and orphan production-lot validation can run during Bronze ingestion.

### Silver
Applies type normalization, deduplication, conformance, validation, and reusable entity relationships.

### Gold
Publishes fact/dimension models, metric-ready aggregates, benchmark views, and root-cause inputs.

### Tableau
Provides interactive business exploration. Tableau-specific calculations are permitted when they are visualization- or view-grain-specific; canonical KPI truth remains upstream.

### AI analytics
Uses governed query results as evidence. It can decompose questions, request approved metrics, compare dimensions, summarize findings, and suggest next investigations.

## MVP boundary

PRs #1–#9 focus on manufacturing quality. Supplier delivery and field RMA are extension domains, not prerequisites for the first complete demo.
