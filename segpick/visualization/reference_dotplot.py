from __future__ import annotations

import plotly.graph_objects as go

from segpick.models import ReferenceDotplot


def make_reference_dotplot(result: ReferenceDotplot) -> go.Figure:
    fig = go.Figure()
    for index, hsp in enumerate(result.hsps, start=1):
        fig.add_trace(
            go.Scattergl(
                x=[hsp.query_start, hsp.query_end],
                y=[hsp.subject_start, hsp.subject_end],
                mode="lines",
                name=f"HSP {index}",
                showlegend=False,
                line={"width": 4},
                customdata=[
                    [hsp.percent_identity, hsp.alignment_length, hsp.bitscore, hsp.evalue, hsp.strand],
                    [hsp.percent_identity, hsp.alignment_length, hsp.bitscore, hsp.evalue, hsp.strand],
                ],
                hovertemplate=(
                    "Candidate: %{x:,} bp<br>Reference: %{y:,} bp<br>"
                    "Identity: %{customdata[0]:.2f}%<br>"
                    "Alignment: %{customdata[1]:,} bp<br>"
                    "Bitscore: %{customdata[2]:.1f}<br>"
                    "E-value: %{customdata[3]:.2g}<br>"
                    "Strand: %{customdata[4]}<extra></extra>"
                ),
            )
        )
    fig.update_layout(
        title=f"{result.candidate_id} vs {result.reference_id}",
        xaxis={
            "title": "Candidate position (bp)",
            "range": [0, max(1, result.query_length)],
            "constrain": "domain",
        },
        yaxis={
            "title": "Reference position (bp)",
            "range": [0, max(1, result.reference_length)],
            "scaleanchor": "x",
            "scaleratio": 1,
        },
        template="plotly_white",
        height=560,
        margin={"l": 70, "r": 30, "t": 70, "b": 65},
        hovermode="closest",
    )
    return fig
