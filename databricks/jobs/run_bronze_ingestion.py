"""Databricks job entry point; core logic lives in the installable package."""

from __future__ import annotations

import argparse
import json

from manufacturing_analytics.bronze.ingestion import BronzeIngestion, IngestionConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-path", default="s3://manufacturing-intelligence-3pwei/source/synthetic/"
    )
    parser.add_argument("--catalog", default="manufacturing_intelligence")
    parser.add_argument("--bronze-schema", default="bronze")
    parser.add_argument("--quarantine-schema", default="quarantine")
    parser.add_argument("--batch-id", default="")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    result = BronzeIngestion(
        spark,  # noqa: F821 - injected by the Databricks runtime
        IngestionConfig(
            args.source_path,
            args.catalog,
            args.bronze_schema,
            args.quarantine_schema,
            args.batch_id,
        ),
    ).run()
    print(json.dumps({"batch_id": args.batch_id or "generated", "tables": result}, indent=2))
