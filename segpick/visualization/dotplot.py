from __future__ import annotations

import plotly.graph_objects as go

from segpick.models import Gene


def make_dotplot(gene: Gene) -> go.Figure:
    """Create an interactive PAF dot plot for one gene."""

    fig = go.Figure()

    for aln in gene.alignments:
        if aln.strand == "+":
            y = [aln.target_start, aln.target_end]
        else:
            y = [aln.target_end, aln.target_start]

        hover = (
            f"Query: {aln.query_id}<br>"
            f"Target: {aln.target_id}<br>"
            f"Strand: {aln.strand}<br>"
            f"Identity: {aln.identity * 100:.2f}%<br>"
            f"Alignment: {aln.alignment_length:,} bp<br>"
            f"MAPQ: {aln.mapq}"
        )

        fig.add_trace(
            go.Scatter(
                x=[aln.query_start, aln.query_end],
                y=y,
                mode="lines",
                name=aln.query_id,
                legendgroup=aln.query_id,
                meta={"sequence_id": aln.query_id},
                customdata=[aln.query_id, aln.query_id],
                hovertemplate=hover + "<extra></extra>",
                line={"width": 4},
            )
        )

    fig.update_layout(
        title=f"{gene.name}: pairwise alignments to anchor {gene.anchor_id}",
        xaxis_title="Query position (bp)",
        yaxis_title="Anchor position (bp)",
        template="plotly_white",
        height=550,
        hovermode="closest",
        legend_title="Sequence",
        clickmode="event+select",
    )
    return fig
