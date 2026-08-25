from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

import matplotlib

from segpick.models import Sample

from .depth import parse_depth_file

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


def _subtract_interval(
    interval: tuple[int, int],
    other: tuple[int, int],
) -> list[tuple[int, int]]:
    """Return portions of *interval* not covered by *other*."""

    start, end = interval
    other_start, other_end = other
    pieces: list[tuple[int, int]] = []

    if end <= other_start or start >= other_end:
        return [(start, end)]
    if start < other_start:
        pieces.append((start, min(end, other_start)))
    if end > other_end:
        pieces.append((max(start, other_end), end))
    return [(left, right) for left, right in pieces if right > left]


def _merge_intervals(
    intervals: Iterable[tuple[int, int]],
    *,
    maximum_gap: int = 25,
) -> list[tuple[int, int]]:
    """Merge overlapping or nearby inclusive intervals."""

    normalised = sorted((min(start, end), max(start, end)) for start, end in intervals)
    merged: list[list[int]] = []
    for start, end in normalised:
        if not merged or start > merged[-1][1] + maximum_gap + 1:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return [(start, end) for start, end in merged]


def _draw_orf_track(
    axis,
    *,
    start: int,
    end: int,
    strand: str | None,
    y: float,
    color: str,
) -> None:
    """Draw a strand-aware ORF arrow in the annotation strip."""

    interval_start = min(start, end)
    interval_end = max(start, end)
    arrow_start, arrow_end = (
        (interval_end, interval_start)
        if strand == "-"
        else (interval_start, interval_end)
    )
    axis.annotate(
        "",
        xy=(arrow_end, y),
        xytext=(arrow_start, y),
        arrowprops={
            "arrowstyle": "-|>",
            "linewidth": 2.0,
            "color": color,
            "shrinkA": 0,
            "shrinkB": 0,
        },
        annotation_clip=False,
    )


def write_coverage_plot(
    positions: Iterable[int],
    depths: Iterable[int],
    output_path: str | Path,
    *,
    title: str | None = None,
    minimum_depth: int | None = None,
    orf_start: int | None = None,
    orf_end: int | None = None,
    orf_strand: str | None = None,
    orf_label: str = "Selected ORF",
    anchored_orf_start: int | None = None,
    anchored_orf_end: int | None = None,
    anchored_orf_strand: str | None = None,
    anchored_orf_label: str = "BLASTX-anchored ORF",
    reference_supported_intervals: Iterable[tuple[int, int]] | None = None,
    reference_hsp_merge_gap: int = 25,
    reference_supported_label: str = "Reference-supported regions",
    boundary_coverage_assessments: Iterable[object] | None = None,
) -> Path:
    """Write a per-base coverage plot and return its output path."""

    positions_list = list(positions)
    depths_list = list(depths)

    if not positions_list:
        raise ValueError("Cannot plot an empty depth profile")

    if len(positions_list) != len(depths_list):
        raise ValueError("Positions and depths must have the same length")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    figure, (coverage_axis, track_axis) = plt.subplots(
        2,
        1,
        figsize=(10, 4.6),
        sharex=True,
        gridspec_kw={"height_ratios": [4.0, 1.35], "hspace": 0.06},
        layout="constrained",
    )

    coverage_axis.fill_between(
        positions_list,
        depths_list,
        step="mid",
        alpha=0.35,
    )
    coverage_axis.plot(
        positions_list,
        depths_list,
        linewidth=0.8,
    )

    legend_handles: list[Line2D] = []
    if minimum_depth is not None:
        coverage_axis.axhline(
            minimum_depth,
            linestyle="--",
            linewidth=0.8,
        )
        legend_handles.append(
            Line2D(
                [0],
                [0],
                linestyle="--",
                linewidth=0.8,
                color="0.35",
                label=f"Minimum depth: {minimum_depth}",
            )
        )

    coverage_axis.set_xlim(positions_list[0], positions_list[-1])
    coverage_axis.set_ylim(bottom=0)
    coverage_axis.set_ylabel("Read depth")
    coverage_axis.tick_params(axis="x", labelbottom=False)

    if title:
        coverage_axis.set_title(title)

    selected_interval = None
    anchored_interval = None
    if orf_start is not None and orf_end is not None:
        selected_interval = (min(orf_start, orf_end), max(orf_start, orf_end))
    if anchored_orf_start is not None and anchored_orf_end is not None:
        anchored_interval = (
            min(anchored_orf_start, anchored_orf_end),
            max(anchored_orf_start, anchored_orf_end),
        )

    reference_intervals = _merge_intervals(
        reference_supported_intervals or (),
        maximum_gap=reference_hsp_merge_gap,
    )
    boundary_assessments = list(boundary_coverage_assessments or ())

    selected_y = 2.15
    anchored_y = 1.35
    reference_y = 0.45
    if selected_interval and anchored_interval:
        for left, right in _subtract_interval(selected_interval, anchored_interval):
            track_axis.plot(
                [left, right],
                [selected_y, selected_y],
                linewidth=8,
                alpha=0.18,
                color="tab:blue",
                solid_capstyle="butt",
            )
        for left, right in _subtract_interval(anchored_interval, selected_interval):
            track_axis.plot(
                [left, right],
                [anchored_y, anchored_y],
                linewidth=8,
                alpha=0.18,
                color="tab:red",
                solid_capstyle="butt",
            )

    if selected_interval:
        _draw_orf_track(
            track_axis,
            start=selected_interval[0],
            end=selected_interval[1],
            strand=orf_strand,
            y=selected_y,
            color="tab:blue",
        )
        legend_handles.append(
            Line2D(
                [0],
                [0],
                color="tab:blue",
                linewidth=2.0,
                label=f"{orf_label} ({orf_strand or '?'})",
            )
        )

    if anchored_interval:
        _draw_orf_track(
            track_axis,
            start=anchored_interval[0],
            end=anchored_interval[1],
            strand=anchored_orf_strand,
            y=anchored_y,
            color="tab:red",
        )
        legend_handles.append(
            Line2D(
                [0],
                [0],
                color="tab:red",
                linewidth=2.0,
                label=f"{anchored_orf_label} ({anchored_orf_strand or '?'})",
            )
        )

    if reference_intervals:
        for start, end in reference_intervals:
            track_axis.plot(
                [start, end],
                [reference_y, reference_y],
                linewidth=7,
                color="tab:green",
                solid_capstyle="butt",
            )
        for left, right in zip(reference_intervals, reference_intervals[1:]):
            matching = next(
                (
                    item for item in boundary_assessments
                    if getattr(item, "gap_start", None) == left[1] + 1
                    and getattr(item, "gap_end", None) == right[0] - 1
                ),
                None,
            )
            classification = getattr(matching, "classification", None)
            marker_color = (
                "tab:red"
                if classification in {
                    "coverage_gap",
                    "local_coverage_decrease",
                    "asymmetric_flank_drop",
                    "low_coverage_both_sides",
                }
                else "tab:green"
            )
            marker_alpha = 0.8 if marker_color == "tab:red" else 0.45
            for boundary in (left[1], right[0]):
                coverage_axis.axvline(
                    boundary,
                    linestyle=":",
                    linewidth=0.9,
                    color=marker_color,
                    alpha=marker_alpha,
                )
        legend_handles.append(
            Line2D(
                [0],
                [0],
                color="tab:green",
                linewidth=5.0,
                label=reference_supported_label,
            )
        )

    track_axis.set_ylim(0.0, 2.7)
    track_axis.set_yticks([])
    track_axis.set_xlabel("Contig position")
    track_axis.spines["left"].set_visible(False)
    track_axis.spines["right"].set_visible(False)
    track_axis.spines["top"].set_visible(False)

    if legend_handles:
        coverage_axis.legend(
            handles=legend_handles,
            frameon=False,
            fontsize=8,
            loc="upper right",
        )

    coverage_axis.spines["top"].set_visible(False)
    coverage_axis.spines["right"].set_visible(False)

    figure.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(figure)

    return output_path


def safe_coverage_filename(candidate_id: str) -> str:
    """Return a filesystem-safe coverage plot filename."""

    safe_id = re.sub(r"[^A-Za-z0-9._-]+", "_", candidate_id)
    return f"{safe_id}.coverage.png"


def write_sample_coverage_plots(
    sample: Sample,
    depth_dir: str | Path,
    output_dir: str | Path,
    *,
    suffix: str = ".depth.txt",
    minimum_depth: int | None = None,
) -> dict[str, Path]:
    """Write one coverage plot for each candidate with a depth file."""

    depth_dir = Path(depth_dir)
    output_dir = Path(output_dir)
    plot_paths: dict[str, Path] = {}

    for gene in sample.genes.values():
        for candidate in gene.candidates:
            depth_path = depth_dir / f"{candidate.id}{suffix}"
            if not depth_path.exists():
                continue

            parsed = parse_depth_file(depth_path)
            if candidate.id in parsed:
                position_depths = parsed[candidate.id]
            elif len(parsed) == 1:
                position_depths = next(iter(parsed.values()))
            else:
                available = ", ".join(sorted(parsed))
                raise KeyError(
                    f"Depth file {depth_path} does not contain candidate "
                    f"{candidate.id!r}. Available sequence IDs: {available}"
                )

            positions = list(range(1, candidate.length + 1))
            depths = [position_depths.get(position, 0) for position in positions]
            output_path = output_dir / safe_coverage_filename(candidate.id)

            selected_orf = (
                candidate.analysis.orf.best_orf
                if candidate.analysis.orf is not None
                else None
            )
            anchored_orf = candidate.analysis.blastx_anchored_orf
            write_coverage_plot(
                positions,
                depths,
                output_path,
                title=f"{gene.name}: {candidate.id}",
                minimum_depth=minimum_depth,
                orf_start=selected_orf.start if selected_orf else None,
                orf_end=selected_orf.end if selected_orf else None,
                orf_strand=selected_orf.strand if selected_orf else None,
                orf_label=f"Selected ORF ({selected_orf.strand})" if selected_orf else "Selected ORF",
                anchored_orf_start=(anchored_orf.start + 1 if anchored_orf else None),
                anchored_orf_end=(anchored_orf.end if anchored_orf else None),
                anchored_orf_strand=(anchored_orf.strand if anchored_orf else None),
                anchored_orf_label=(
                    f"BLASTX-anchored ORF ({anchored_orf.strand})"
                    if anchored_orf
                    else "BLASTX-anchored ORF"
                ),
                reference_supported_intervals=(
                    [
                        (hsp.query_start, hsp.query_end)
                        for hsp in candidate.analysis.reference_dotplot.hsps
                    ]
                    if candidate.analysis.reference_dotplot is not None
                    else None
                ),
                boundary_coverage_assessments=candidate.analysis.boundary_coverage,
            )
            plot_paths[candidate.id] = output_path

    return plot_paths
