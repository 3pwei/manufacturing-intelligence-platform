# Deployment and End-to-End Verification

This runbook deploys the existing PR #1–#10 implementation without changing its data grains,
metric contracts, or Bronze/Silver/Gold semantics. Run commands from the repository root.

## Prerequisites

- Python 3.10+ and the project dependencies;
- AWS CLI authenticated to an identity allowed to write only the source prefix;
- Databricks CLI authenticated to the target AWS workspace;
- Unity Catalog access to `manufacturing_intelligence` and `READ FILES` on the S3 external
  location;
- an available Databricks SQL warehouse for the final validation queries.

Credentials belong in the AWS and Databricks credential stores or environment supplied by the
operator. Never add them to this repository.

## 1. Generate and verify the source

```bash
python scripts/generate_data.py --seed 42 --scale demo --output data/generated
python scripts/verify_demo_source.py --input data/generated
```

The verification must report exactly nine non-empty Parquet files. Upload only those files:

```bash
aws s3 sync data/generated/ \
  s3://manufacturing-intelligence-3pwei/source/synthetic/ \
  --exclude '*' --include '*.parquet' --delete
aws s3 ls s3://manufacturing-intelligence-3pwei/source/synthetic/
```

`--delete` makes the prefix match the verified nine-file demo inventory. Confirm the bucket and
prefix before running it; do not use it on a broader path.

## 2. Validate and deploy the bundle

```bash
databricks auth describe
databricks bundle validate -t dev
databricks bundle deploy -t dev
```

The bundle builds the project wheel and deploys the existing serverless Bronze and Silver/Gold
jobs. It does not contain cloud credentials.

## 3. Run in dependency order

```bash
databricks bundle run -t dev bronze_ingestion
databricks bundle run -t dev silver_gold_transform
```

Run Bronze again with the unchanged source to test file-level idempotency:

```bash
databricks bundle run -t dev bronze_ingestion
```

The second run must not increase any Bronze table count or add quarantine rows. Silver/Gold uses
full-refresh `CREATE OR REPLACE TABLE`, so it can also be rerun safely.

## 4. Validate in Databricks SQL

Execute `sql/validation/030_silver_gold_validation.sql` in a Databricks SQL editor. The script
returns:

- the required Bronze, quarantine, Silver, and Gold inventory;
- Bronze and Gold row counts;
- quarantine counts and ingestion audit totals;
- duplicate and invalid-quantity checks, which must be zero;
- Incident A–E evidence, including the Incident E aggregate/product-level comparison.

For the seed-42 demo, the expected source/Bronze counts are:

| Table | Rows |
|---|---:|
| dim_date | 181 |
| dim_factory | 3 |
| dim_line | 6 |
| dim_product | 5 |
| dim_component | 6 |
| dim_supplier | 8 |
| dim_defect | 6 |
| fact_production | 2,110 |
| fact_quality_event | 9,488 |

Expected Gold counts are 1,798 manufacturing daily, 543 factory quality, 1,442 product quality,
8,045 supplier quality, and 8,649 defect Pareto rows. The clean demo is expected to have zero
quarantined records.

## Known limitations

- Source objects are immutable after a successful file audit. Publish a new URI or perform a
  controlled audit correction instead of overwriting an already-ingested URI.
- Bronze writes and the file audit are not one transaction. The existing-key guard protects a
  retry after interruption, but audit/write atomicity is deferred.
- Silver/Gold intentionally uses a full refresh for this six-month demo dataset.
- The CLI deploys jobs, but Databricks SQL validation still requires an operator-selected SQL
  warehouse. Tableau connection and dashboard work are PR #12 scope.

## Cost control and teardown

Serverless job compute terminates after each run. Stop an idle SQL warehouse after validation.
To remove the deployed bundle resources without deleting Unity Catalog data, run:

```bash
databricks bundle destroy -t dev
```

Catalog/table deletion and S3 source deletion are destructive data operations and are deliberately
not part of bundle teardown. Perform them only through an explicitly reviewed cleanup procedure.
