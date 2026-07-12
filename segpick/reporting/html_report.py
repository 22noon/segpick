from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from plotly.io import to_html

from segpick import __version__
from segpick.alignment.export import safe_name
from segpick.models import Gene, Sample
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


def _provisional_recommendation(gene: Gene) -> dict[str, object] | None:
    """Return a transparent dashboard-only curation hint.

    This is not the final configurable weighting engine. COMPLETE/ANCHOR candidates
    are preferred and ranked by protein confidence. If none are structurally
    complete, structural score is used first and confidence breaks ties.
    """

    if not gene.candidates:
        return None

    complete = [c for c in gene.candidates if c.analysis.containment.status in {"COMPLETE", "ANCHOR"}]
    if complete:
        chosen = max(complete, key=lambda c: c.metadata.confidence)
        reason = [
            "Structurally complete relative to the selected anchor.",
            "Highest protein confidence among complete candidates.",
        ]
    else:
        chosen = max(
            gene.candidates,
            key=lambda c: (
                c.analysis.containment.structural_score,
                c.metadata.confidence,
            ),
        )
        reason = [
            "No candidate met the current COMPLETE criteria.",
            "Highest structural score, with protein confidence used as a tie-breaker.",
        ]

    m = chosen.analysis.containment
    if m.fragmentation <= 0.10:
        reason.append("Alignment is not strongly fragmented.")
    if m.identity >= 0.95:
        reason.append("High nucleotide identity to the anchor.")

    return {
        "id": chosen.id,
        "confidence": chosen.metadata.confidence,
        "z": chosen.metadata.z,
        "status": m.status,
        "query_coverage": m.query_coverage,
        "anchor_coverage": m.anchor_coverage,
        "identity": m.identity,
        "fragmentation": m.fragmentation,
        "structural_score": m.structural_score,
        "reason": reason,
    }


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


def render_gene_page(gene: Gene, outdir: Path, env: Environment) -> Path:
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
    recommendation = _provisional_recommendation(gene)

    out = outdir / "genes" / f"{safe_name(gene.name)}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        template.render(
            gene=gene,
            dotplot=dot_html,
            containment=containment_html,
            rows=rows,
            sequences=sequences,
            sequences_json=json.dumps(sequences),
            recommendation=recommendation,
            package_version=__version__,
        )
    )
    return out


def write_html_dashboard(sample: Sample, outdir: str | Path) -> Path:
    """Write static interactive HTML dashboard pages."""

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    templates = Path(__file__).resolve().parent / "templates"
    env = Environment(
        loader=FileSystemLoader(templates),
        autoescape=select_autoescape(["html"]),
    )

    overviews: list[dict[str, object]] = []
    for gene_name in sorted(sample.genes):
        gene = sample.genes[gene_name]
        page = f"genes/{safe_name(gene_name)}.html"
        render_gene_page(gene, outdir, env)
        overviews.append(_gene_overview(gene, page))

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
