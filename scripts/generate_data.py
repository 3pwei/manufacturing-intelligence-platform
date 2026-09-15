#!/usr/bin/env python3
"""Generate reproducible manufacturing demo data."""

from __future__ import annotations

import argparse
from pathlib import Path

from manufacturing_analytics.generator import ManufacturingDataGenerator
from manufacturing_analytics.generator.config import load_config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("config/data_generation.yaml"))
    parser.add_argument("--seed", type=int)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--scale", choices=("test", "demo", "full"))
    parser.add_argument("--format", choices=("csv", "parquet", "both"), default="both")
    args = parser.parse_args()
    config = load_config(args.config, seed=args.seed, output=args.output, scale=args.scale)
    formats = ("csv", "parquet") if args.format == "both" else (args.format,)
    counts = ManufacturingDataGenerator(config).generate_to(formats=formats)
    for table, count in counts.items():
        print(f"{table}: {count:,} rows")


if __name__ == "__main__":
    main()
