from __future__ import annotations

import argparse
import importlib.util
import shutil
import sys
from pathlib import Path

from segpick import __version__
from segpick.alignment.export import export_anchor_fastas, export_gene_fastas, safe_name
from segpick.alignment.minimap import align_gene, attach_existing_paf
from segpick.analysis.blastx import attach_blastx_hits
from segpick.analysis.blastx_consistency import attach_blastx_consistency
from segpick.analysis.blastx_anchored_orf import attach_blastx_anchored_orfs
from segpick.analysis.containment import analyse_gene
from segpick.analysis.orf import attach_orf_metrics
from segpick.analysis.orf_selection import attach_blastx_guided_orf_metrics
from segpick.analysis.orf_alignment import attach_orf_alignment_metrics
from segpick.analysis.orf_quality import attach_orf_quality
from segpick.analysis.protein_interpretation import attach_protein_interpretations
from segpick.analysis.observations import attach_observation_intervals
from segpick.analysis.findings import attach_biological_findings
from segpick.analysis.manifest import build_analysis_manifest
from segpick.analysis.reference_dotplot import attach_reference_dotplots
from segpick.analysis.hypotheses import attach_biological_hypotheses
from segpick.config import RunConfig, load_config, resolve_config
from segpick.reasoning import load_active_rules
from segpick.io.builder import build_sample
from segpick.provenance import write_provenance
from segpick.reporting import (
    write_analysis_manifest,
    write_gene_json_reports,
    write_html_dashboard,
    write_metrics_tsv,
    write_recommendations_tsv,
    write_summary_tsv,
)
from segpick.scoring import rank_gene
from segpick.read_support import (
    attach_depth_directory,
    write_sample_coverage_plots,
)


def run_doctor() -> int:
    checks = {
        "Python >= 3.12": sys.version_info >= (3, 12),
        "Biopython": importlib.util.find_spec("Bio") is not None,
        "pandas": importlib.util.find_spec("pandas") is not None,
        "Plotly": importlib.util.find_spec("plotly") is not None,
        "Jinja2": importlib.util.find_spec("jinja2") is not None,
        "PyYAML": importlib.util.find_spec("yaml") is not None,
        "minimap2 on PATH": shutil.which("minimap2") is not None,
        "blastn on PATH": shutil.which("blastn") is not None,
    }
    print(f"SegPick {__version__}")
    print(f"Imported from: {Path(__file__).resolve().parent}")
    print()
    for label, passed in checks.items():
        print(f"[{'OK' if passed else 'MISSING'}] {label}")
    required = [
        value for key, value in checks.items()
        if key not in {"minimap2 on PATH", "blastn on PATH"}
    ]
    return 0 if all(required) else 1


def _add_run_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", help="YAML configuration file")
    parser.add_argument("--hits", default=None)
    parser.add_argument("--contigs", default=None)
    parser.add_argument("--refs", default=None)
    parser.add_argument("--blastx-results", default=None)
    parser.add_argument("--protein-refs", default=None)
    parser.add_argument(
        "--rule-file",
        dest="rule_files",
        action="append",
        default=None,
        help="Additional YAML hypothesis rule file; may be supplied more than once",
    )
    parser.add_argument("--outdir", default=None)
    parser.add_argument("--sample-name", default=None)
    parser.add_argument("--preset", default=None)

    parser.add_argument("--strict", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--align", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--use-existing-paf", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--html", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument(
        "--show-config",
        action="store_true",
        help="print the fully resolved configuration before running",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="segpick",
        description="Evidence-based curation of segmented viral genome assemblies.",
    )
    parser.add_argument("--version", action="version", version=f"SegPick {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("doctor", help="check dependencies and import location")
    run = sub.add_parser("run", help="run the complete SegPick workflow")
    run.add_argument(
        "--depth-dir",
        default=None,
        help="Directory containing one depth file per candidate",
    )

    run.add_argument(
        "--depth-suffix",
        default=None,
        help="Suffix appended to candidate IDs; default .depth.txt",
    )

    run.add_argument(
        "--minimum-depth",
        type=int,
        default=None,
    )

    run.add_argument(
        "--terminal-fraction",
        type=float,
        default=None,
    )

    run.add_argument(
        "--minimum-terminal-bases",
        type=int,
        default=None,
    )

    run.add_argument(
        "--strict-depth",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Fail when a candidate depth file is missing",
    )
    run.add_argument(
        "--reference-dotplots",
        dest="reference_dotplots_enabled",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Run BLASTN against each candidate's closest nucleotide reference",
    )
    run.add_argument(
        "--reference-dotplot-task",
        choices=("megablast", "dc-megablast", "blastn"),
        default=None,
    )
    run.add_argument("--reference-dotplot-evalue", type=float, default=None)
    run.add_argument("--reference-dotplot-word-size", type=int, default=None)
    run.add_argument(
        "--force-reference-dotplots",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Rerun BLASTN even when a non-empty cached TSV exists",
    )
    _add_run_arguments(run)
    return parser


def _cli_override_values(args: argparse.Namespace) -> dict[str, object]:
    keys = (
        "hits",
        "contigs",
        "refs",
        "blastx_results",
        "protein_refs",
        "rule_files",
        "outdir",
        "sample_name",
        "strict",
        "align",
        "use_existing_paf",
        "preset",
        "html",
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
    )
    return {key: getattr(args, key) for key in keys}


def execute_run(config: RunConfig, argv: list[str], show_config: bool = False) -> None:
    missing = [key for key in ("hits", "contigs", "refs") if not getattr(config, key)]
    if missing:
        raise ValueError("Missing required configuration values: " + ", ".join(missing))
    if config.align and config.use_existing_paf:
        raise ValueError("Choose either align or use_existing_paf, not both")

    if show_config:
        import yaml

        print(yaml.safe_dump(config.to_dict(), sort_keys=False))

    sample = build_sample(
        hits_path=config.hits,
        contigs_fasta=config.contigs,
        references_fasta=config.refs,
        sample_name=config.sample_name,
        strict=config.strict,
    )

    if (config.blastx_results is None) != (config.protein_refs is None):
        raise ValueError("blastx_results and protein_refs must be provided together")
    if config.blastx_results is not None:
        blastx_summary = attach_blastx_hits(
            sample,
            config.blastx_results,
            config.protein_refs,
            strict=config.strict,
        )
        print(
            "BLASTX: "
            f"{blastx_summary.hits_attached}/"
            f"{blastx_summary.candidate_count} candidates attached; "
            f"{blastx_summary.subjects_resolved} proteins resolved"
        )

    outdir = Path(config.outdir)
    analysis_dir = outdir / "analysis"

    if config.reference_dotplots.enabled:
        attached, attempted = attach_reference_dotplots(
            sample,
            analysis_dir / "reference_dotplots",
            task=config.reference_dotplots.task,
            evalue=config.reference_dotplots.evalue,
            word_size=config.reference_dotplots.word_size,
            force=config.reference_dotplots.force,
            strict=config.strict,
        )
        print(
            "Reference dot plots: "
            f"{attached}/{attempted} candidate-reference comparisons attached"
        )

    gene_fastas = export_gene_fastas(sample, outdir / "gene_fastas")
    anchor_fastas = export_anchor_fastas(sample, outdir / "anchors")

    paf_dir = outdir / "paf"
    paf_dir.mkdir(parents=True, exist_ok=True)

    if config.read_support.depth_dir is not None:
        depth_summary = attach_depth_directory(
            sample,
            config.read_support.depth_dir,
            suffix=config.read_support.suffix,
            strict=config.read_support.strict,
            minimum_depth=config.read_support.minimum_depth,
            terminal_fraction=config.read_support.terminal_fraction,
            minimum_terminal_bases=config.read_support.minimum_terminal_bases,
        )
        print(
            "Read support: "
            f"{depth_summary.metrics_attached}/"
            f"{depth_summary.candidate_count} candidates attached"
        )

    attach_orf_metrics(sample)
    attach_blastx_guided_orf_metrics(sample)
    attach_blastx_anchored_orfs(sample)
    attach_blastx_consistency(sample)
    attach_orf_alignment_metrics(sample)
    attach_protein_interpretations(sample)
    attach_observation_intervals(
        sample,
        minimum_depth=config.read_support.minimum_depth,
    )
    attach_orf_quality(sample)
    attach_biological_findings(sample)
    candidate_rules, gene_rules = load_active_rules(config.rule_files)
    attach_biological_hypotheses(
        sample,
        candidate_rules=candidate_rules,
        gene_rules=gene_rules,
    )

    coverage_plot_paths = {}
    if config.html and config.read_support.depth_dir is not None:
        coverage_plot_paths = write_sample_coverage_plots(
            sample,
            config.read_support.depth_dir,
            outdir / "dashboard" / "coverage",
            suffix=config.read_support.suffix,
            minimum_depth=config.read_support.minimum_depth,
        )

    recommendations = {}

    for gene_name, gene in sample.genes.items():
        paf_path = paf_dir / f"{safe_name(gene_name)}.paf"

        if config.align:
            align_gene(
                gene=gene,
                anchor_fasta=anchor_fastas[gene_name],
                query_fasta=gene_fastas[gene_name],
                paf_out=paf_path,
                preset=config.preset,
            )
        elif config.use_existing_paf:
            if not paf_path.exists():
                raise FileNotFoundError(f"Existing PAF not found: {paf_path}")

            attach_existing_paf(gene, paf_path)


        analyse_gene(gene)
        recommendations[gene_name] = rank_gene(
            gene,
            config.scoring_weights,
        )

    write_summary_tsv(
        sample,
        outdir / "summary.tsv",
    )

    write_metrics_tsv(
        sample,
        outdir / "containment_metrics.tsv",
    )

    write_recommendations_tsv(
        sample,
        recommendations,
        outdir / "recommendations.tsv",
    )

    active_rules = (*candidate_rules, *gene_rules)
    manifest = build_analysis_manifest(
        sample,
        config,
        active_rules,
        recommendations=recommendations,
    )
    write_analysis_manifest(manifest, analysis_dir / "manifest.json")

    write_gene_json_reports(
        sample,
        analysis_dir,
        recommendations=recommendations,
        manifest=manifest,
    )

    if config.html:
        dashboard = write_html_dashboard(
            sample,
            outdir / "dashboard",
            recommendations=recommendations,
            coverage_plot_paths=coverage_plot_paths,
            manifest=manifest,
        )
        print(f"Dashboard: {dashboard}")

    write_provenance(
        config,
        outdir / "provenance.yml",
        argv,
        manifest=manifest,
    )
    print("\n".join(sample.summary_lines()))
    print(f"\nGenerated by SegPick {__version__}")
    print(f"Wrote outputs to: {outdir}")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "doctor":
        raise SystemExit(run_doctor())

    try:
        yaml_values = load_config(args.config)
        config = resolve_config(yaml_values, _cli_override_values(args))
        execute_run(config, sys.argv, show_config=args.show_config)
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
