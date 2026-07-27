from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

from segpick.scoring import ScoringWeights

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ReadSupportConfig:
    depth_dir: Path | None = None
    suffix: str = ".depth.txt"
    minimum_depth: int = 3
    terminal_fraction: float = 0.05
    minimum_terminal_bases: int = 50
    strict: bool = False



@dataclass(frozen=True, slots=True)
class PairwiseDotplotConfig:
    enabled: bool = False
    task: str = "megablast"
    evalue: float = 1e-5
    word_size: int | None = None
    force: bool = False


@dataclass(frozen=True, slots=True)
class ReferenceDotplotConfig:
    enabled: bool = False
    task: str = "megablast"
    evalue: float = 1e-5
    word_size: int | None = None
    force: bool = False

@dataclass(slots=True)
class RunConfig:
    hits: Path | None = None
    contigs: Path | None = None
    refs: Path | None = None
    blastx_results: Path | None = None
    protein_refs: Path | None = None
    rule_files: tuple[Path, ...] = ()
    outdir: Path = Path("results")
    sample_name: str = "sample"
    align: bool = False
    use_existing_paf: bool = False
    preset: str = "asm5"
    html: bool = False
    strict: bool = False
    scoring_weights: ScoringWeights = field(default_factory=ScoringWeights)
    read_support: ReadSupportConfig = field(
        default_factory=ReadSupportConfig
    )
    reference_dotplots: ReferenceDotplotConfig = field(
        default_factory=ReferenceDotplotConfig
    )
    contig_dotplots: PairwiseDotplotConfig = field(
        default_factory=PairwiseDotplotConfig
    )
    def to_dict(self) -> dict[str, Any]:
        """Return a YAML/JSON-safe representation of the resolved config."""
        def serialise(value: Any) -> Any:
            if isinstance(value, Path):
                return str(value)

            if isinstance(value, dict):
                return {
                    key: serialise(item)
                    for key, item in value.items()
                }

            if isinstance(value, (list, tuple)):
                return [serialise(item) for item in value]

            return value

        return serialise(asdict(self))


DEFAULTS = RunConfig()


def _flatten_yaml(data: dict[str, Any]) -> dict[str, Any]:
    """Map the documented nested YAML structure to RunConfig fields."""

    result: dict[str, Any] = {}
    input_cfg = data.get("input", {}) or {}
    alignment_cfg = data.get("alignment", {}) or {}
    dashboard_cfg = data.get("dashboard", {}) or {}
    reasoning_cfg = data.get("reasoning", {}) or {}
    reference_dotplot_cfg = data.get("reference_dotplots", {}) or {}
    contig_dotplot_cfg = data.get("contig_dotplots", {}) or {}

    result["hits"] = input_cfg.get("hits", data.get("hits"))
    result["contigs"] = input_cfg.get("contigs", data.get("contigs"))
    result["refs"] = input_cfg.get("references", input_cfg.get("refs", data.get("refs")))
    result["blastx_results"] = input_cfg.get("blastx_results", data.get("blastx_results"))
    result["protein_refs"] = input_cfg.get("protein_refs", data.get("protein_refs"))
    result["rule_files"] = reasoning_cfg.get("rule_files", data.get("rule_files"))
    result["outdir"] = data.get("outdir")
    result["sample_name"] = data.get("sample", data.get("sample_name"))
    result["strict"] = data.get("strict")
    result["align"] = alignment_cfg.get("run", alignment_cfg.get("align", data.get("align")))
    result["use_existing_paf"] = alignment_cfg.get("use_existing_paf", data.get("use_existing_paf"))
    result["preset"] = alignment_cfg.get("preset", data.get("preset"))
    result["html"] = dashboard_cfg.get("html", data.get("html"))
    if reference_dotplot_cfg:
        result["reference_dotplots"] = reference_dotplot_cfg
    if contig_dotplot_cfg:
        result["contig_dotplots"] = contig_dotplot_cfg
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
    read_data = yaml_values.get("read_support", {}) or {}

    read_support = ReadSupportConfig(
        depth_dir=(
            Path(read_data["depth_dir"])
            if read_data.get("depth_dir")
            else None
        ),
        suffix=str(read_data.get("suffix", ".depth.txt")),
        minimum_depth=int(read_data.get("minimum_depth", 3)),
        terminal_fraction=float(
            read_data.get("terminal_fraction", 0.05)
        ),
        minimum_terminal_bases=int(
            read_data.get("minimum_terminal_bases", 50)
        ),
        strict=bool(read_data.get("strict", False)),
    )

    dotplot_data = yaml_values.get("reference_dotplots", {}) or {}
    reference_dotplots = ReferenceDotplotConfig(
        enabled=bool(dotplot_data.get("enabled", False)),
        task=str(dotplot_data.get("task", "megablast")),
        evalue=float(dotplot_data.get("evalue", 1e-5)),
        word_size=(
            int(dotplot_data["word_size"])
            if dotplot_data.get("word_size") is not None
            else None
        ),
        force=bool(dotplot_data.get("force", False)),
    )

    contig_dotplot_data = yaml_values.get("contig_dotplots", {}) or {}
    contig_dotplots = PairwiseDotplotConfig(
        enabled=bool(contig_dotplot_data.get("enabled", False)),
        task=str(contig_dotplot_data.get("task", "megablast")),
        evalue=float(contig_dotplot_data.get("evalue", 1e-5)),
        word_size=(
            int(contig_dotplot_data["word_size"])
            if contig_dotplot_data.get("word_size") is not None
            else None
        ),
        force=bool(contig_dotplot_data.get("force", False)),
    )

    merged = DEFAULTS.to_dict()

    # Extract nested scoring configuration separately.
    scoring_data = yaml_values.get("scoring", {}) or {}
    weights_data = scoring_data.get("weights", {}) or {}

    default_weights = ScoringWeights()
    scoring_weights = ScoringWeights(
        protein_confidence=float(
            weights_data.get(
                "protein_confidence",
                default_weights.protein_confidence,
            )
        ),
        length_plausibility=float(
            weights_data.get(
                "length_plausibility",
                default_weights.length_plausibility,
            )
        ),
        containment=float(
            weights_data.get("containment", default_weights.containment)
        ),
        identity=float(
            weights_data.get("identity", default_weights.identity)
        ),
        fragmentation=float(
            weights_data.get(
                "fragmentation",
                default_weights.fragmentation,
            )
        ),
        coverage_sufficiency=float(
            weights_data.get(
                "coverage_sufficiency",
                float(weights_data.get("read_support", 0.08)) / 2.0
                if "read_support" in weights_data
                else default_weights.coverage_sufficiency,
            )
        ),
        coverage_integrity=float(
            weights_data.get(
                "coverage_integrity",
                float(weights_data.get("read_support", 0.08)) / 2.0
                if "read_support" in weights_data
                else default_weights.coverage_integrity,
            )
        ),
        orf_quality=float(
            weights_data.get("orf_quality", default_weights.orf_quality)
        ),
        blastx_consistency=float(
            weights_data.get(
                "blastx_consistency",
                default_weights.blastx_consistency,
            )
        ),
    )

    # Do not pass the nested "scoring" dictionary directly to RunConfig.
    yaml_flat = {
        key: value
        for key, value in yaml_values.items()
        if value is not None
        and key not in {"scoring", "read_support", "reference_dotplots", "contig_dotplots"}
    }

    merged.update(yaml_flat)
    if "rule_files" in merged:
        merged["rule_files"] = tuple(Path(path) for path in (merged["rule_files"] or ()))
    merged["scoring_weights"] = scoring_weights

    # CLI values override YAML values.
    read_support = ReadSupportConfig(
        depth_dir=(
            Path(cli_values["depth_dir"])
            if cli_values.get("depth_dir") is not None
            else read_support.depth_dir
        ),
        suffix=(
            cli_values["depth_suffix"]
            if cli_values.get("depth_suffix") is not None
            else read_support.suffix
        ),
        minimum_depth=(
            cli_values["minimum_depth"]
            if cli_values.get("minimum_depth") is not None
            else read_support.minimum_depth
        ),
        terminal_fraction=(
            cli_values["terminal_fraction"]
            if cli_values.get("terminal_fraction") is not None
            else read_support.terminal_fraction
        ),
        minimum_terminal_bases=(
            cli_values["minimum_terminal_bases"]
            if cli_values.get("minimum_terminal_bases") is not None
            else read_support.minimum_terminal_bases
        ),
        strict=(
            cli_values["strict_depth"]
            if cli_values.get("strict_depth") is not None
            else read_support.strict
        ),
    )

    reference_dotplots = ReferenceDotplotConfig(
        enabled=(
            bool(cli_values["reference_dotplots_enabled"])
            if cli_values.get("reference_dotplots_enabled") is not None
            else reference_dotplots.enabled
        ),
        task=(
            str(cli_values["reference_dotplot_task"])
            if cli_values.get("reference_dotplot_task") is not None
            else reference_dotplots.task
        ),
        evalue=(
            float(cli_values["reference_dotplot_evalue"])
            if cli_values.get("reference_dotplot_evalue") is not None
            else reference_dotplots.evalue
        ),
        word_size=(
            int(cli_values["reference_dotplot_word_size"])
            if cli_values.get("reference_dotplot_word_size") is not None
            else reference_dotplots.word_size
        ),
        force=(
            bool(cli_values["force_reference_dotplots"])
            if cli_values.get("force_reference_dotplots") is not None
            else reference_dotplots.force
        ),
    )

    contig_dotplots = PairwiseDotplotConfig(
        enabled=(
            bool(cli_values["contig_dotplots_enabled"])
            if cli_values.get("contig_dotplots_enabled") is not None
            else contig_dotplots.enabled
        ),
        task=(
            str(cli_values["contig_dotplot_task"])
            if cli_values.get("contig_dotplot_task") is not None
            else contig_dotplots.task
        ),
        evalue=(
            float(cli_values["contig_dotplot_evalue"])
            if cli_values.get("contig_dotplot_evalue") is not None
            else contig_dotplots.evalue
        ),
        word_size=(
            int(cli_values["contig_dotplot_word_size"])
            if cli_values.get("contig_dotplot_word_size") is not None
            else contig_dotplots.word_size
        ),
        force=(
            bool(cli_values["force_contig_dotplots"])
            if cli_values.get("force_contig_dotplots") is not None
            else contig_dotplots.force
        ),
    )

    merged["read_support"] = read_support
    merged["reference_dotplots"] = reference_dotplots
    merged["contig_dotplots"] = contig_dotplots
    cli_clean = {key: value for key, value in cli_values.items() if value is not None}
    if "rule_files" in cli_clean:
        cli_clean["rule_files"] = tuple(Path(path) for path in cli_clean["rule_files"])
    merged.update(cli_clean)
    for key in (
        "depth_dir",
        "depth_suffix",
        "minimum_depth",
        "terminal_fraction",
        "minimum_terminal_bases",
        "strict_depth",
        "reference_dotplots_enabled",
        "reference_dotplot_task",
        "reference_dotplot_evalue",
        "reference_dotplot_word_size",
        "force_reference_dotplots",
        "contig_dotplots_enabled",
        "contig_dotplot_task",
        "contig_dotplot_evalue",
        "contig_dotplot_word_size",
        "force_contig_dotplots",
    ):
        merged.pop(key, None)


    return RunConfig(**merged)
