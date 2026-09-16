"""Verify the generated demo source before it is uploaded to S3."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pyarrow import parquet

EXPECTED_TABLES = (
    "dim_date",
    "dim_factory",
    "dim_line",
    "dim_product",
    "dim_component",
    "dim_supplier",
    "dim_defect",
    "fact_production",
    "fact_quality_event",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/generated"))
    return parser.parse_args()


def main() -> None:
    source = parse_args().input
    actual = {path.stem: path for path in source.glob("*.parquet")}
    missing = sorted(set(EXPECTED_TABLES) - actual.keys())
    unexpected = sorted(actual.keys() - set(EXPECTED_TABLES))
    if missing or unexpected:
        raise SystemExit(
            f"demo source inventory mismatch: missing={missing}, unexpected={unexpected}"
        )

    row_counts = {
        table: parquet.ParquetFile(actual[table]).metadata.num_rows for table in EXPECTED_TABLES
    }
    empty = [table for table, count in row_counts.items() if count <= 0]
    if empty:
        raise SystemExit(f"demo source contains empty Parquet tables: {empty}")

    print(json.dumps({"source": str(source), "files": 9, "row_counts": row_counts}, indent=2))


if __name__ == "__main__":
    main()
