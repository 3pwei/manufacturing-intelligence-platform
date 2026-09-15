"""Stable random helpers isolated from domain logic."""

from __future__ import annotations

import random
from collections.abc import Sequence
from typing import TypeVar

T = TypeVar("T")


class DeterministicRng:
    def __init__(self, seed: int) -> None:
        self._rng = random.Random(seed)

    def randint(self, low: int, high: int) -> int:
        return self._rng.randint(low, high)

    def random(self) -> float:
        return self._rng.random()

    def weighted(self, values: Sequence[T], weights: Sequence[float]) -> T:
        return self._rng.choices(values, weights=weights, k=1)[0]
