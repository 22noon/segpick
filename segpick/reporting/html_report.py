from __future__ import annotations

import json
import os
from collections import defaultdict
from collections.abc import Mapping
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from plotly.io import to_html
from plotly.offline import get_plotlyjs
from plotly.utils import PlotlyJSONEncoder

from segpick import __version__
from segpick.alignment.export import safe_name
from segpick.analysis import analyse_protein_continuity
from segpick.models import AnalysisManifest, Gene, Sample
from segpick.reporting.view_models import build_gene_page_view
from segpick.scoring import GeneRecommendation
from segpick.visualization import (
    make_contig_dotplot,
    make_multi_candidate_reference_dotplot,
    make_reference_dotplot,
)


def _sequence_payload(gene: Gene) -> list[dict[str, object]]:
    seqs: list[dict[str, object]] = []
    for ref in gene.references:
        seqs.append(
            {
                "id": ref.accession,
                "type": "reference",
                "length": ref.length,
                "sequence": ref.sequence,
            }
        )
    for contig in gene.candidates:
        seqs.append(
            {
                "id": contig.id,
                "type": "candidate",
                "length": contig.length,
                "sequence": contig.sequence,
            }
        )
    return seqs



def _table_rows(gene: Gene) -> list[dict[str, object]]:
    """Return candidate structural rows for compatibility and tests."""
    rows: list[dict[str, object]] = []
    for reference in gene.references:
        rows.append({
            "id": reference.accession, "type": "reference", "length": reference.length,
            "confidence": None, "z": None, "cluster": None,
            "candidate_coverage": None, "reference_coverage": None,
            "block_count": None, "largest_reference_gap": None,
            "structural_integrity": None, "status": "REFERENCE",
            "is_anchor": reference.accession == gene.anchor_id,
        })
    for candidate in gene.candidates:
        m = candidate.analysis.structural_integrity
        rows.append({
            "id": candidate.id,
            "type": "candidate",
            "length": candidate.length,
            "confidence": candidate.metadata.confidence,
            "z": candidate.metadata.z,
            "cluster": candidate.metadata.cluster,
            "candidate_coverage": m.candidate_coverage if m else None,
            "reference_coverage": m.reference_coverage if m else None,
            "block_count": m.block_count if m else None,
            "largest_reference_gap": m.largest_reference_gap if m else None,
            "structural_integrity": m.score if m else None,
            "status": m.status if m else "UNAVAILABLE",
            "is_anchor": candidate.id == gene.anchor_id,
        })
    return rows

def render_gene_page(
    gene: Gene,
    outdir: Path,
    env: Environment,
    recommendation: GeneRecommendation | None = None,
    coverage_plot_paths: Mapping[str, str | Path] | None = None,
) -> Path:
    template = env.get_template("gene.html")

    sequences = _sequence_payload(gene)
    out = outdir / "genes" / f"{safe_name(gene.name)}.html"
    relative_coverage_paths = {
        candidate_id: Path(
            os.path.relpath(path, start=out.parent)
        ).as_posix()
        for candidate_id, path in (coverage_plot_paths or {}).items()
    }
    view = build_gene_page_view(
        gene,
        recommendation,
        coverage_plot_paths=relative_coverage_paths,
    )
    reference_orientations = {
        candidate.id: (
            candidate.analysis.reference_dotplot.display_reverse_complemented
            if candidate.analysis.reference_dotplot is not None
            else False
        )
        for candidate in gene.candidates
    }

    contig_dotplots = {}
    for result in gene.contig_dotplots:
        query_reverse = reference_orientations.get(result.query_id, False)
        target_reverse = reference_orientations.get(result.target_id, False)
        figure = make_contig_dotplot(
            result,
            query_reverse=query_reverse,
            target_reverse=target_reverse,
        )
        key = result.pair_key
        contig_dotplots[key] = {
            "figure": figure.to_plotly_json(),
            "query_id": result.query_id,
            "target_id": result.target_id,
            "block_count": result.block_count,
            "query_coverage": result.query_coverage,
            "target_coverage": result.target_coverage,
            "identity_min": result.identity_min,
            "identity_max": result.identity_max,
            "orientation": result.orientation,
            "reused_existing": result.reused_existing,
            "query_reverse_complemented_for_display": query_reverse,
            "target_reverse_complemented_for_display": target_reverse,
        }

    reference_groups: dict[str, list[object]] = defaultdict(list)
    candidate_order = (
        [item.candidate_id for item in recommendation.candidates]
        if recommendation is not None
        else [candidate.id for candidate in gene.candidates]
    )
    order_index = {candidate_id: index for index, candidate_id in enumerate(candidate_order)}
    for candidate in gene.candidates:
        result = candidate.analysis.reference_dotplot
        if result is not None:
            reference_groups[result.reference_id].append(result)

    reference_overviews = []
    for reference_id, results in reference_groups.items():
        if len(results) < 2:
            continue
        results.sort(key=lambda item: order_index.get(item.candidate_id, len(order_index)))
        overview = make_multi_candidate_reference_dotplot(results)
        reference_overviews.append(
            {
                "reference_id": reference_id,
                "candidate_count": len(results),
                "plot_html": to_html(
                    overview,
                    include_plotlyjs=False,
                    full_html=False,
                    config={"responsive": True, "displaylogo": False},
                    div_id=f"reference-overview-{safe_name(reference_id)}",
                ),
            }
        )

    reference_dotplots = {}
    for candidate in gene.candidates:
        result = candidate.analysis.reference_dotplot
        if result is None:
            continue
        figure = make_reference_dotplot(result)
        reference_dotplots[candidate.id] = {
            "figure": figure.to_plotly_json(),
            "reference_id": result.reference_id,
            "block_count": result.block_count,
            "query_coverage": result.query_coverage,
            "reference_coverage": result.reference_coverage,
            "identity_min": result.identity_min,
            "identity_max": result.identity_max,
            "orientation": result.orientation,
            "display_orientation": result.display_orientation,
            "display_reverse_complemented": result.display_reverse_complemented,
            "dominant_orientation_fraction": result.dominant_orientation_fraction,
            "reused_existing": result.reused_existing,
            "output_path": result.output_path,
        }

    protein_sequences = {
        candidate.candidate_id: {
            "predicted_header": candidate.orf.predicted_header,
            "predicted_sequence": candidate.orf.predicted_protein,
            "reference_header": candidate.orf.reference_header,
            "reference_sequence": candidate.orf.reference_protein,
            "predicted_coding_header": candidate.orf.predicted_coding_header,
            "predicted_coding_sequence": candidate.orf.predicted_coding_sequence,
            "anchored_protein_header": candidate.orf.anchored_protein_header,
            "anchored_protein_sequence": candidate.orf.anchored_protein,
            "anchored_coding_header": candidate.orf.anchored_coding_header,
            "anchored_coding_sequence": candidate.orf.anchored_coding_sequence,
            "alignment": candidate.orf.alignment_text,
        }
        for candidate in view.candidates
        if candidate.orf.predicted_protein is not None
    }

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        template.render(
            view=view,
            gene=gene,
            sequences=sequences,
            sequences_json=json.dumps(sequences),
            protein_sequences_json=json.dumps(protein_sequences),
            reference_overviews=reference_overviews,
            reference_dotplots_json=json.dumps(
                reference_dotplots, cls=PlotlyJSONEncoder
            ),
            contig_dotplots_json=json.dumps(
                contig_dotplots, cls=PlotlyJSONEncoder
            ),
            package_version=__version__,
        )
    )
    return out


def write_html_dashboard(
    sample: Sample,
    outdir: str | Path,
    recommendations: Mapping[str, GeneRecommendation] | None = None,
    coverage_plot_paths: Mapping[str, str | Path] | None = None,
    manifest: AnalysisManifest | None = None,
) -> Path:
    """Write static interactive HTML dashboard pages."""

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    assets_dir = outdir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    (assets_dir / "plotly.min.js").write_text(get_plotlyjs(), encoding="utf-8")

    templates = Path(__file__).resolve().parent / "templates"
    env = Environment(
        loader=FileSystemLoader(templates),
        autoescape=select_autoescape(["html"]),
    )

    overviews: list[dict[str, object]] = []

    for gene_name, gene in sample.genes.items():
        recommendation = None

        if recommendations is not None:
            recommendation = recommendations.get(gene_name)

        render_gene_page(
            gene,
            outdir,
            env,
            recommendation=recommendation,
            coverage_plot_paths=coverage_plot_paths,
        )

        report = recommendation.report if recommendation is not None else None
        agreement = recommendation.agreement if recommendation is not None else None
        continuity = analyse_protein_continuity(gene)

        overviews.append(
            {
                "gene": gene.name,
                "segment": gene.segment,
                "candidate_count": len(gene.candidates),
                "reference_count": len(gene.references),
                "anchor": gene.anchor_id,
                "recommended_candidate": (
                    recommendation.recommended.candidate_id
                    if recommendation is not None
                    else None
                ),
                "recommendation_score": (
                    recommendation.recommended.score
                    if recommendation is not None
                    else None
                ),
                "confidence": (
                    report.confidence
                    if report is not None
                    else agreement.confidence if agreement is not None else "unknown"
                ),
                "manual_review": report.manual_review if report is not None else False,
                "summary": report.summary if report is not None else None,
                "conflict_count": (
                    len(report.evidence_conflicts)
                    if report is not None
                    else 0
                ),
                "protein_continuity": continuity.classification,
                "protein_continuity_summary": continuity.summary,
                "page": f"genes/{safe_name(gene.name)}.html",
            }
        )

    index_template = env.get_template("index.html")
    index = outdir / "index.html"
    index.write_text(
        index_template.render(
            sample=sample,
            genes=overviews,
            package_version=__version__,
            manifest=manifest,
        )
    )

    return index
