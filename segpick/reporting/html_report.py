from __future__ import annotations
from segpick.reporting.view_models import build_gene_page_view

import json
from collections.abc import Mapping
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from plotly.io import to_html

from segpick import __version__
from segpick.alignment.export import safe_name
from segpick.models import Gene, Sample
from segpick.scoring import GeneRecommendation
from segpick.visualization import make_containment_plot, make_dotplot


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
    rows: list[dict[str, object]] = []
    for ref in gene.references:
        m = ref.containment
        rows.append(
            {
                "id": ref.accession,
                "type": "reference",
                "length": ref.length,
                "confidence": None,
                "z": None,
                "cluster": None,
                "query_coverage": m.query_coverage,
                "anchor_coverage": m.anchor_coverage,
                "identity": m.identity,
                "fragmentation": m.fragmentation,
                "n_blocks": m.n_blocks,
                "structural_score": m.structural_score,
                "status": m.status,
                "is_anchor": ref.accession == gene.anchor_id,
            }
        )
    for contig in gene.candidates:
        m = contig.analysis.containment
        rows.append(
            {
                "id": contig.id,
                "type": "candidate",
                "length": contig.length,
                "confidence": contig.metadata.confidence,
                "z": contig.metadata.z,
                "cluster": contig.metadata.cluster,
                "query_coverage": m.query_coverage,
                "anchor_coverage": m.anchor_coverage,
                "identity": m.identity,
                "fragmentation": m.fragmentation,
                "n_blocks": m.n_blocks,
                "structural_score": m.structural_score,
                "status": m.status,
                "is_anchor": contig.id == gene.anchor_id,
            }
        )
    return rows


def _gene_overview(gene: Gene, page: str) -> dict[str, object]:
    recommendation = _provisional_recommendation(gene)
    statuses = [c.analysis.containment.status for c in gene.candidates]
    if any(s in {"COMPLETE", "ANCHOR"} for s in statuses):
        overall_status = "COMPLETE"
    elif any(s == "PARTIAL" for s in statuses):
        overall_status = "PARTIAL"
    elif any(s == "FRAGMENTED" for s in statuses):
        overall_status = "FRAGMENTED"
    elif statuses:
        overall_status = "POOR"
    else:
        overall_status = "NO_CANDIDATE"

    return {
        "gene": gene,
        "page": page,
        "overall_status": overall_status,
        "recommendation": recommendation,
    }


def render_gene_page(
    gene: Gene,
    outdir: Path,
    env: Environment,
    recommendation: GeneRecommendation | None = None,
) -> Path:
    template = env.get_template("gene.html")

    dot_html = to_html(
        make_dotplot(gene),
        include_plotlyjs="inline",
        full_html=False,
        config={"responsive": True, "displaylogo": False},
        div_id="dotplot",
    )
    containment_html = to_html(
        make_containment_plot(gene),
        include_plotlyjs=False,
        full_html=False,
        config={"responsive": True, "displaylogo": False},
        div_id="containment-plot",
    )

    sequences = _sequence_payload(gene)
    rows = _table_rows(gene)
    view = build_gene_page_view( gene, recommendation,)

    out = outdir / "genes" / f"{safe_name(gene.name)}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        template.render(
            view=view,
            gene=gene,
            recommendation=recommendation,
            dotplot=dot_html,
            containment=containment_html,
            rows=rows,
            sequences=sequences,
            sequences_json=json.dumps(sequences),
        )
    )
    return out


def write_html_dashboard(
    sample: Sample,
    outdir: str | Path,
    recommendations: Mapping[str, GeneRecommendation] | None = None,
) -> Path:
    """Write static interactive HTML dashboard pages."""

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

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
        )

        overviews.append(
            {
                "gene": gene.name,
                "segment": gene.segment,
                "candidates": len(gene.candidates),
                "references": len(gene.references),
                "anchor": gene.anchor_id,
                "recommended": (recommendation.recommended.candidate_id if recommendation is not None else None),
                "score": (recommendation.recommended.score if recommendation is not None else None),
            }
        )

    index_template = env.get_template("index.html")
    index = outdir / "index.html"
    index.write_text(
        index_template.render(
            sample=sample,
            genes=overviews,
            package_version=__version__,
        )
    )

    return index
