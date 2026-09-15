"""Configuration loading and validation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ScaleConfig:
    lots_per_line_day: int
    lot_quantity_min: int
    lot_quantity_max: int


@dataclass(frozen=True)
class GeneratorConfig:
    seed: int
    start_date: date
    end_date: date
    output_path: Path
    scale_name: str
    scale: ScaleConfig
    enabled_incidents: tuple[str, ...]


def load_config(path: Path, *, seed: int | None = None, output: Path | None = None,
                scale: str | None = None) -> GeneratorConfig:
    """Load YAML config, applying explicit CLI overrides."""
    raw: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8"))
    scale_name = scale or str(raw["scale"])
    scales = raw["scales"]
    if scale_name not in scales:
        raise ValueError(f"Unknown scale {scale_name!r}; choose from {sorted(scales)}")
    selected = scales[scale_name]
    start = date.fromisoformat(str(raw["start_date"]))
    end = date.fromisoformat(str(raw["end_date"]))
    if end < start:
        raise ValueError("end_date must be on or after start_date")
    scale_config = ScaleConfig(
        lots_per_line_day=int(selected["lots_per_line_day"]),
        lot_quantity_min=int(selected["lot_quantity_min"]),
        lot_quantity_max=int(selected["lot_quantity_max"]),
    )
    if scale_config.lot_quantity_min <= 0 or scale_config.lot_quantity_max < scale_config.lot_quantity_min:
        raise ValueError("scale quantities must be positive and ordered")
    return GeneratorConfig(
        seed=int(seed if seed is not None else raw["seed"]),
        start_date=start,
        end_date=end,
        output_path=output or Path(raw["output_path"]),
        scale_name=scale_name,
        scale=scale_config,
        enabled_incidents=tuple(raw.get("incidents", {}).get("enabled", [])),
    )
