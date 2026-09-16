"""Thin Databricks entry point for the governed Silver and Gold SQL assets."""

from __future__ import annotations

import argparse
from pathlib import Path


def execute_sql_file(spark_session, path: Path) -> None:
    statements = [item.strip() for item in path.read_text().split(";") if item.strip()]
    for statement in statements:
        spark_session.sql(statement)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", required=True)
    return parser.parse_args()


if __name__ == "__main__":
    repository_root = Path(parse_args().repository_root)
    for relative_path in (
        "sql/ddl/002_silver_gold_foundation.sql",
        "sql/transformations/010_silver_conformed.sql",
        "sql/metrics/020_gold_analytics.sql",
    ):
        sql_path = repository_root / relative_path
        if not sql_path.is_file():
            raise FileNotFoundError(f"required Silver/Gold SQL asset not found: {sql_path}")
        print(f"Executing Silver/Gold SQL asset: {relative_path}")
        execute_sql_file(spark, sql_path)  # noqa: F821
    print("Silver/Gold transformation completed successfully")
