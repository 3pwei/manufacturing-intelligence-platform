"""Generator orchestration service."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

from .config import GeneratorConfig, load_config
from .dimensions import build_dimensions
from .incidents import manifest
from .io import write_dataset
from .production import generate_lot_plans
from .quality import generate_outcomes
from .rng import DeterministicRng
from .validation import validate_dataset


class ManufacturingDataGenerator:
    """Create a deterministic dataset for one immutable configuration."""

    def __init__(self, config: GeneratorConfig | None = None, *, seed: int | None = None) -> None:
        if config is None:
            config = load_config(Path("config/data_generation.yaml"), seed=seed)
        elif seed is not None:
            config = replace(config, seed=seed)
        self.config = config

    def generate(self) -> dict[str, list[dict[str, Any]]]:
        rng = DeterministicRng(self.config.seed)
        tables = build_dimensions(self.config.start_date, self.config.end_date)
        lots = generate_lot_plans(self.config, rng)
        production, quality = generate_outcomes(lots, self.config, rng)
        tables["fact_production"] = production
        tables["fact_quality_event"] = quality
        validate_dataset(tables, self.config.start_date, self.config.end_date)
        return tables

    def generate_to(self, output: Path | None = None,
                    formats: tuple[str, ...] = ("parquet", "csv")) -> dict[str, int]:
        tables = self.generate()
        write_dataset(tables, manifest(self.config.enabled_incidents), output or self.config.output_path, formats)
        return {name: len(rows) for name, rows in tables.items()}
