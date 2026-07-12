from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from segpick.scoring import ScoringWeights
from dataclasses import dataclass, field

import yaml

@dataclass(slots=True)
class RunConfig:
    hits: Path | None = None
    contigs: Path | None = None
    refs: Path | None = None
    outdir: Path = Path("results")
    sample_name: str = "sample"
    align: bool = False
    use_existing_paf: bool = False
    preset: str = "asm5"
    html: bool = False
    strict: bool = False
    scoring_weights: ScoringWeights = field(
        default_factory=ScoringWeights
    )

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
    result["use_existing_paf"] = alignment_cfg.get("use_existing_paf", data.get("use_existing_paf"))
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
    """Resolve built-in defaults < YAML < explicit CLI values."""

    merged = DEFAULTS.to_dict()

    # Extract nested scoring configuration separately.
    scoring_data = yaml_values.get("scoring", {}) or {}
    weights_data = scoring_data.get("weights", {}) or {}

    scoring_weights = ScoringWeights(
        protein_confidence=float(
            weights_data.get("protein_confidence", 0.30)
        ),
        length_plausibility=float(
            weights_data.get("length_plausibility", 0.15)
        ),
        containment=float(
            weights_data.get("containment", 0.25)
        ),
        identity=float(
            weights_data.get("identity", 0.15)
        ),
        fragmentation=float(
            weights_data.get("fragmentation", 0.15)
        ),
    )

    # Do not pass the nested "scoring" dictionary directly to RunConfig.
    yaml_flat = {
        key: value
        for key, value in yaml_values.items()
        if value is not None and key != "scoring"
    }

    merged.update(yaml_flat)
    merged["scoring_weights"] = scoring_weights

    # CLI values override YAML values.
    merged.update(
        {
            key: value
            for key, value in cli_values.items()
            if value is not None
        }
    )

    return RunConfig(**merged)
