from __future__ import annotations

import plotly.graph_objects as go

from segpick.models import ContigDotplot


def _display_coordinate(position: int, length: int, reverse: bool) -> int:
    return length - position + 1 if reverse else position


def make_contig_dotplot(
    result: ContigDotplot,
    *,
    query_reverse: bool = False,
    target_reverse: bool = False,
) -> go.Figure:
    fig = go.Figure()
    for index, hsp in enumerate(result.hsps, start=1):
        fig.add_trace(
            go.Scattergl(
                x=[
                    _display_coordinate(hsp.query_start, result.query_length, query_reverse),
                    _display_coordinate(hsp.query_end, result.query_length, query_reverse),
                ],
                y=[
                    _display_coordinate(hsp.subject_start, result.target_length, target_reverse),
                    _display_coordinate(hsp.subject_end, result.target_length, target_reverse),
                ],
                mode="lines",
                name=f"HSP {index}",
                showlegend=False,
                line={"width": 4},
                customdata=[
                    [hsp.percent_identity, hsp.alignment_length, hsp.bitscore, hsp.evalue, hsp.strand],
                    [hsp.percent_identity, hsp.alignment_length, hsp.bitscore, hsp.evalue, hsp.strand],
                ],
                hovertemplate=(
                    "Query: %{x:,} bp<br>Target: %{y:,} bp<br>"
                    "Identity: %{customdata[0]:.2f}%<br>"
                    "Alignment: %{customdata[1]:,} bp<br>"
                    "Bitscore: %{customdata[2]:.1f}<br>"
                    "E-value: %{customdata[3]:.2g}<br>"
                    "Strand: %{customdata[4]}<extra></extra>"
                ),
            )
        )
    fig.update_layout(
        title=(
            f"{result.query_id} vs {result.target_id}"
            + (
                " — "
                + ", ".join(
                    label
                    for label, enabled in (
                        (f"{result.query_id} RC for display", query_reverse),
                        (f"{result.target_id} RC for display", target_reverse),
                    )
                    if enabled
                )
                if query_reverse or target_reverse
                else ""
            )
        ),
        xaxis={
            "title": f"{result.query_id} position (bp)" + (" · RC display" if query_reverse else ""),
            "range": [0, max(1, result.query_length)],
            "constrain": "domain",
        },
        yaxis={
            "title": f"{result.target_id} position (bp)" + (" · RC display" if target_reverse else ""),
            "range": [0, max(1, result.target_length)],
            "scaleanchor": "x",
            "scaleratio": 1,
        },
        template="plotly_white",
        height=560,
        margin={"l": 80, "r": 30, "t": 70, "b": 75},
        hovermode="closest",
    )
    return fig
