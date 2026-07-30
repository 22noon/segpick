from __future__ import annotations

from collections.abc import Sequence

import plotly.graph_objects as go
from plotly.colors import qualitative
from plotly.subplots import make_subplots

from segpick.models import ReferenceDotplot


def _display_coordinate(position: int, length: int, reverse: bool) -> int:
    return length - position + 1 if reverse else position


def make_reference_dotplot(result: ReferenceDotplot) -> go.Figure:
    """Draw every HSP and make repeated-reference mappings explicit."""

    repeated_pairs = result.repeated_reference_pairs()
    repeated_indices = set(result.repeated_reference_hsp_indices)
    has_repeated = bool(repeated_pairs)
    fig = make_subplots(
        rows=2 if has_repeated else 1,
        cols=1,
        shared_xaxes=has_repeated,
        row_heights=[0.82, 0.18] if has_repeated else None,
        vertical_spacing=0.08 if has_repeated else 0.0,
        subplot_titles=(
            ("Candidate-to-reference HSPs", "Individual candidate mapping blocks")
            if has_repeated
            else None
        ),
    )
    reverse_query = result.display_reverse_complemented

    # Draw ordinary blocks first and diagnostic blocks last so repeated mappings
    # cannot be hidden beneath larger or nearly coincident HSPs.
    ordered_indices = [
        *[index for index in range(len(result.hsps)) if index not in repeated_indices],
        *[index for index in range(len(result.hsps)) if index in repeated_indices],
    ]
    for index in ordered_indices:
        hsp = result.hsps[index]
        repeated = index in repeated_indices
        x_values = [
            _display_coordinate(hsp.query_start, result.query_length, reverse_query),
            _display_coordinate(hsp.query_end, result.query_length, reverse_query),
        ]
        customdata = [
            [hsp.percent_identity, hsp.alignment_length, hsp.bitscore, hsp.evalue, hsp.strand, index + 1, repeated],
            [hsp.percent_identity, hsp.alignment_length, hsp.bitscore, hsp.evalue, hsp.strand, index + 1, repeated],
        ]
        fig.add_trace(
            go.Scattergl(
                x=x_values,
                y=[hsp.subject_start, hsp.subject_end],
                mode="lines+markers" if repeated else "lines",
                name="Repeated-reference HSP" if repeated else f"HSP {index + 1}",
                legendgroup="repeated-reference" if repeated else "ordinary-hsp",
                showlegend=repeated and index == min(repeated_indices),
                line={
                    "width": 7 if repeated else 3,
                    "color": "#c2410c" if repeated else "#2563eb",
                    "dash": "dash" if repeated else "solid",
                },
                marker={"size": 7, "symbol": "diamond"} if repeated else None,
                customdata=customdata,
                hovertemplate=(
                    "HSP %{customdata[5]}<br>"
                    "Candidate: %{x:,} bp<br>Reference: %{y:,} bp<br>"
                    "Identity: %{customdata[0]:.2f}%<br>"
                    "Alignment: %{customdata[1]:,} bp<br>"
                    "Bitscore: %{customdata[2]:.1f}<br>"
                    "E-value: %{customdata[3]:.2g}<br>"
                    "Strand: %{customdata[4]}<br>"
                    "Repeated-reference mapping: %{customdata[6]}<extra></extra>"
                ),
            ),
            row=1,
            col=1,
        )

        if has_repeated:
            lane = index + 1
            fig.add_trace(
                go.Scattergl(
                    x=x_values,
                    y=[lane, lane],
                    mode="lines+markers",
                    name=f"HSP {index + 1} mapping track",
                    showlegend=False,
                    line={
                        "width": 9 if repeated else 5,
                        "color": "#c2410c" if repeated else "#94a3b8",
                        "dash": "dash" if repeated else "solid",
                    },
                    marker={"size": 6},
                    customdata=customdata,
                    hovertemplate=(
                        "HSP %{customdata[5]} candidate interval<br>"
                        "Candidate: %{x:,} bp<br>"
                        "Repeated-reference mapping: %{customdata[6]}<extra></extra>"
                    ),
                ),
                row=2,
                col=1,
            )

    for pair_number, pair in enumerate(repeated_pairs, start=1):
        start, end = pair["reference_interval"]
        fig.add_hrect(
            y0=start,
            y1=end,
            fillcolor="#fb923c",
            opacity=0.16,
            line_width=1,
            line_color="#c2410c",
            annotation_text=f"Repeated reference interval {pair_number}: {start:,}–{end:,} bp",
            annotation_position="top left",
            row=1,
            col=1,
        )

    fig.update_xaxes(
        title_text="Candidate position (bp)" if not has_repeated else None,
        range=[0, max(1, result.query_length)],
        constrain="domain",
        row=1,
        col=1,
    )
    fig.update_yaxes(
        title_text="Reference position (bp)",
        range=[0, max(1, result.reference_length)],
        row=1,
        col=1,
    )
    if has_repeated:
        fig.update_xaxes(
            title_text="Candidate position (bp)",
            range=[0, max(1, result.query_length)],
            row=2,
            col=1,
        )
        fig.update_yaxes(
            title_text="HSP",
            tickmode="array",
            tickvals=list(range(1, len(result.hsps) + 1)),
            ticktext=[str(index) for index in range(1, len(result.hsps) + 1)],
            range=[0.25, len(result.hsps) + 0.75],
            row=2,
            col=1,
        )

    fig.update_layout(
        title=(
            f"{result.candidate_id} vs {result.reference_id}"
            + (" — reverse-complemented for display" if reverse_query else "")
        ),
        template="plotly_white",
        height=700 if has_repeated else 560,
        margin={"l": 75, "r": 35, "t": 80, "b": 65},
        hovermode="closest",
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0},
    )
    return fig


def make_multi_candidate_reference_dotplot(
    results: Sequence[ReferenceDotplot],
) -> go.Figure:
    """Stack candidate alignments that share one nucleotide reference."""

    if not results:
        raise ValueError("At least one reference dot plot is required")

    reference_ids = {result.reference_id for result in results}
    if len(reference_ids) != 1:
        raise ValueError("All results must use the same reference")

    rows = len(results)
    fig = make_subplots(
        rows=rows,
        cols=1,
        shared_yaxes=True,
        vertical_spacing=min(0.08, 0.18 / max(1, rows)),
        subplot_titles=[
            (
                f"{result.candidate_id} ({result.query_length:,} nt)"
                + (" · RC for display" if result.display_reverse_complemented else "")
            )
            for result in results
        ],
    )
    colours = qualitative.Plotly
    max_reference_length = max(result.reference_length for result in results)

    for row, result in enumerate(results, start=1):
        colour = colours[(row - 1) % len(colours)]
        reverse_query = result.display_reverse_complemented
        for index, hsp in enumerate(result.hsps):
            opacity = max(0.35, min(1.0, 0.35 + (hsp.percent_identity / 100.0) * 0.65))
            fig.add_trace(
                go.Scattergl(
                    x=[
                        _display_coordinate(hsp.query_start, result.query_length, reverse_query),
                        _display_coordinate(hsp.query_end, result.query_length, reverse_query),
                    ],
                    y=[hsp.subject_start, hsp.subject_end],
                    mode="lines",
                    name=result.candidate_id,
                    legendgroup=result.candidate_id,
                    showlegend=index == 0,
                    opacity=opacity,
                    line={"width": 4, "color": colour},
                    customdata=[
                        [hsp.percent_identity, hsp.alignment_length, hsp.bitscore, hsp.evalue, hsp.strand],
                        [hsp.percent_identity, hsp.alignment_length, hsp.bitscore, hsp.evalue, hsp.strand],
                    ],
                    hovertemplate=(
                        f"Candidate: {result.candidate_id}<br>"
                        "Candidate position: %{x:,} bp<br>"
                        "Reference position: %{y:,} bp<br>"
                        "Identity: %{customdata[0]:.2f}%<br>"
                        "Alignment: %{customdata[1]:,} bp<br>"
                        "Bitscore: %{customdata[2]:.1f}<br>"
                        "E-value: %{customdata[3]:.2g}<br>"
                        "Strand: %{customdata[4]}<extra></extra>"
                    ),
                ),
                row=row,
                col=1,
            )

        fig.update_xaxes(
            range=[0, max(1, result.query_length)],
            title_text="Candidate position (bp)" if row == rows else None,
            showgrid=True,
            gridcolor="#e2e8f0",
            row=row,
            col=1,
        )
        fig.update_yaxes(
            range=[0, max(1, max_reference_length)],
            title_text="Reference position (bp)" if row == (rows + 1) // 2 else None,
            showgrid=True,
            gridcolor="#e2e8f0",
            row=row,
            col=1,
        )

    reference_id = results[0].reference_id
    fig.update_layout(
        title={
            "text": f"Candidates aligned to shared reference {reference_id}",
            "x": 0.5,
            "xanchor": "center",
        },
        template="plotly_white",
        height=max(430, 210 * rows + 100),
        margin={"l": 85, "r": 35, "t": 90, "b": 65},
        hovermode="closest",
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0},
    )
    return fig
