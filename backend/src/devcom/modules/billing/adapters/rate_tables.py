from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast


@dataclass(frozen=True, slots=True)
class ModelRates:
    model_id: str
    input_uncached: str
    input_cached: str
    cache_write: str
    output: str

    @property
    def reservation_input_rate(self) -> str:
        from fractions import Fraction

        write = Fraction(self.cache_write)
        uncached = Fraction(self.input_uncached)
        return self.cache_write if write >= uncached else self.input_uncached


@dataclass(frozen=True, slots=True)
class OpenAiRateTable:
    verified_at: str
    regional_uplift_ratio: str
    models: dict[str, ModelRates]


@dataclass(frozen=True, slots=True)
class FxTable:
    rate: str
    rate_date: str
    source: str
    verified_at: str
    fx_margin_ratio: str


def load_openai_rates(path: Path) -> OpenAiRateTable:
    payload = json.loads(path.read_text(encoding="utf-8"))
    models = {
        model_id: ModelRates(
            model_id=model_id,
            input_uncached=raw["input_uncached_usd_per_mtok"],
            input_cached=raw["input_cached_usd_per_mtok"],
            cache_write=raw["cache_write_usd_per_mtok"],
            output=raw["output_usd_per_mtok"],
        )
        for model_id, raw in payload["models"].items()
    }
    return OpenAiRateTable(
        verified_at=payload["verified_at"],
        regional_uplift_ratio=payload["regional_uplift_ratio"],
        models=models,
    )


def load_fx_table(path: Path) -> FxTable:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return FxTable(
        rate=payload["rate"],
        rate_date=payload["rate_date"],
        source=payload["source"],
        verified_at=payload["verified_at"],
        fx_margin_ratio=payload["fx_margin_ratio"],
    )


def load_call_bounds(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
