from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import yaml


@dataclass(slots=True)
class RunConfig:
    """Resolved configuration for a SegPick run."""

    hits: str | None = None
    contigs: str | None = None
    refs: str | None = None
    outdir: str = "results"
    sample_name: str = "sample"
    strict: bool = False
    align: bool = False
    use_existing_paf: bool = False
    preset: str = "asm5"
    html: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


DEFAULTS = RunConfig()


def _flatten_yaml(data: dict[str, Any]) -> dict[str, Any]:
    """Map the documented nested YAML structure to RunConfig fields."""

    result: dict[str, Any] = {}
    input_cfg = data.get("input", {}) or {}
    alignment_cfg = data.get("alignment", {}) or {}
    dashboard_cfg = data.get("dashboard", {}) or {}

    result["hits"] = input_cfg.get("hits", data.get("hits"))
    result["contigs"] = input_cfg.get("contigs", data.get("contigs"))
    result["refs"] = input_cfg.get("references", input_cfg.get("refs", data.get("refs")))
    result["outdir"] = data.get("outdir")
    result["sample_name"] = data.get("sample", data.get("sample_name"))
    result["strict"] = data.get("strict")
    result["align"] = alignment_cfg.get("run", alignment_cfg.get("align", data.get("align")))
    result["use_existing_paf"] = alignment_cfg.get(
        "use_existing_paf", data.get("use_existing_paf")
    )
    result["preset"] = alignment_cfg.get("preset", data.get("preset"))
    result["html"] = dashboard_cfg.get("html", data.get("html"))
    return {key: value for key, value in result.items() if value is not None}


def load_config(path: str | Path | None) -> dict[str, Any]:
    """Load a YAML configuration file, returning only explicitly set values."""

    if path is None:
        return {}
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    raw = yaml.safe_load(config_path.read_text()) or {}
    if not isinstance(raw, dict):
        raise ValueError("The YAML configuration root must be a mapping")
    return _flatten_yaml(raw)


def resolve_config(
    yaml_values: dict[str, Any],
    cli_values: dict[str, Any],
) -> RunConfig:
    """Resolve defaults < YAML < explicitly supplied command-line values."""

    merged = DEFAULTS.to_dict()
    merged.update({k: v for k, v in yaml_values.items() if v is not None})
    merged.update({k: v for k, v in cli_values.items() if v is not None})
    return RunConfig(**merged)
