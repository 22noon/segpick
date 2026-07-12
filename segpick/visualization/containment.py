from __future__ import annotations

import plotly.graph_objects as go

from segpick.models import Gene


def _sequence_rows(gene: Gene):
    rows = []
    for ref in gene.references:
        rows.append(
            {
                "id": ref.accession,
                "type": "reference",
                "length": ref.length,
                "metrics": ref.containment,
                "confidence": None,
                "z": None,
                "cluster": None,
            }
        )
    for contig in gene.candidates:
        rows.append(
            {
                "id": contig.id,
                "type": "candidate",
                "length": contig.length,
                "metrics": contig.analysis.containment,
                "confidence": contig.metadata.confidence,
                "z": contig.metadata.z,
                "cluster": contig.metadata.cluster,
            }
        )
    return rows


def make_containment_plot(gene: Gene) -> go.Figure:
    """Create interactive containment tracks on the anchor coordinate system."""

    rows = _sequence_rows(gene)
    fig = go.Figure()

    for idx, row in enumerate(rows):
        seq_id = row["id"]
        metrics = row["metrics"]
        y = len(rows) - idx

        fig.add_trace(
            go.Scatter(
                x=[0, row["length"]],
                y=[y, y],
                mode="lines",
                line={"width": 12, "color": "#d1d5db"},
                showlegend=False,
                meta={"sequence_id": seq_id, "track": "background"},
                customdata=[seq_id, seq_id],
                hovertemplate=f"{seq_id}<br>Length: {row['length']:,} bp<extra></extra>",
            )
        )

        hits = [a for a in gene.alignments if a.query_id == seq_id]
        if seq_id == gene.anchor_id:
            anchor_len = row["length"]
            fig.add_trace(
                go.Scatter(
                    x=[0, anchor_len],
                    y=[y, y],
                    mode="lines",
                    line={"width": 12, "color": "#111827"},
                    name="Anchor",
                    showlegend=False,
                    meta={"sequence_id": seq_id, "track": "alignment"},
                    customdata=[seq_id, seq_id],
                    hovertemplate=(
                        f"{seq_id}<br>Anchor<br>Length: {anchor_len:,} bp<extra></extra>"
                    ),
                )
            )
        else:
            for aln in hits:
                color = "#2563eb" if aln.strand == "+" else "#f97316"
                hover = (
                    f"{seq_id}<br>"
                    f"Type: {row['type']}<br>"
                    f"Identity: {aln.identity * 100:.2f}%<br>"
                    f"Query coverage: {metrics.query_coverage * 100:.1f}%<br>"
                    f"Anchor coverage: {metrics.anchor_coverage * 100:.1f}%<br>"
                    f"Status: {metrics.status}"
                )
                fig.add_trace(
                    go.Scatter(
                        x=[aln.target_start, aln.target_end],
                        y=[y, y],
                        mode="lines",
                        line={"width": 12, "color": color},
                        showlegend=False,
                        meta={"sequence_id": seq_id, "track": "alignment"},
                        customdata=[seq_id, seq_id],
                        hovertemplate=hover + "<extra></extra>",
                    )
                )

    fig.update_layout(
        title=f"{gene.name}: containment map",
        xaxis_title=f"Position on anchor {gene.anchor_id} (bp)",
        yaxis={
            "tickmode": "array",
            "tickvals": list(range(1, len(rows) + 1)),
            "ticktext": [r["id"] for r in reversed(rows)],
        },
        template="plotly_white",
        height=max(400, 95 * len(rows) + 140),
        margin={"l": 180, "r": 30, "t": 70, "b": 60},
        showlegend=False,
        clickmode="event+select",
    )
    return fig
