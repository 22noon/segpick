from __future__ import annotations

import argparse
import importlib.util
import shutil
import sys
from pathlib import Path

from segpick import __version__
from segpick.alignment.export import export_anchor_fastas, export_gene_fastas, safe_name
from segpick.alignment.minimap import align_gene, attach_existing_paf
from segpick.analysis.containment import analyse_gene
from segpick.config import RunConfig, load_config, resolve_config
from segpick.io.builder import build_sample
from segpick.provenance import write_provenance
from segpick.reporting import (
    write_gene_json_reports,
    write_html_dashboard,
    write_metrics_tsv,
    write_recommendations_tsv,
    write_summary_tsv,
)
from segpick.scoring import rank_gene


def run_doctor() -> int:
    checks = {
        "Python >= 3.12": sys.version_info >= (3, 12),
        "Biopython": importlib.util.find_spec("Bio") is not None,
        "pandas": importlib.util.find_spec("pandas") is not None,
        "Plotly": importlib.util.find_spec("plotly") is not None,
        "Jinja2": importlib.util.find_spec("jinja2") is not None,
        "PyYAML": importlib.util.find_spec("yaml") is not None,
        "minimap2 on PATH": shutil.which("minimap2") is not None,
    }
    print(f"SegPick {__version__}")
    print(f"Imported from: {Path(__file__).resolve().parent}")
    print()
    for label, passed in checks.items():
        print(f"[{'OK' if passed else 'MISSING'}] {label}")
    required = [value for key, value in checks.items() if key != "minimap2 on PATH"]
    return 0 if all(required) else 1


def _add_run_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", help="YAML configuration file")
    parser.add_argument("--hits", default=None)
    parser.add_argument("--contigs", default=None)
    parser.add_argument("--refs", default=None)
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
    _add_run_arguments(run)
    return parser


def _cli_override_values(args: argparse.Namespace) -> dict[str, object]:
    keys = (
        "hits",
        "contigs",
        "refs",
        "outdir",
        "sample_name",
        "strict",
        "align",
        "use_existing_paf",
        "preset",
        "html",
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

    outdir = Path(config.outdir)
    gene_fastas = export_gene_fastas(sample, outdir / "gene_fastas")
    anchor_fastas = export_anchor_fastas(sample, outdir / "anchors")
    paf_dir = outdir / "paf"
    paf_dir.mkdir(parents=True, exist_ok=True)
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

    write_summary_tsv(sample, outdir / "summary.tsv")
    write_metrics_tsv(sample, outdir / "containment_metrics.tsv")
    write_gene_json_reports(sample, outdir / "analysis")
    if config.html:
        dashboard = write_html_dashboard(sample, outdir / "dashboard")
        print(f"Dashboard: {dashboard}")

    write_provenance(config, outdir / "provenance.yml", argv)
    write_recommendations_tsv(
        sample,
        recommendations,
        outdir / "recommendations.tsv",
    )
    write_gene_json_reports(
        sample,
        analysis_dir,
        recommendations=recommendations,
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
    except (ValueError, FileNotFoundError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
