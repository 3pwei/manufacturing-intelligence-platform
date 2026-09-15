"""Dataset serialization."""

from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq


def _json_default(value: Any) -> str:
    if isinstance(value, date):
        return value.isoformat()
    raise TypeError(f"Cannot serialize {type(value)}")


def write_dataset(tables: dict[str, list[dict[str, Any]]], incidents: list[dict[str, Any]],
                  output: Path, formats: tuple[str, ...] = ("parquet", "csv")) -> None:
    output.mkdir(parents=True, exist_ok=True)
    for name, rows in tables.items():
        if "parquet" in formats:
            pq.write_table(pa.Table.from_pylist(rows), output / f"{name}.parquet")
        if "csv" in formats:
            with (output / f"{name}.csv").open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
                writer.writeheader()
                writer.writerows(rows)
    truth = output / "ground_truth"
    truth.mkdir(exist_ok=True)
    (truth / "incidents.json").write_text(
        json.dumps(incidents, indent=2, default=_json_default) + "\n", encoding="utf-8"
    )
