from __future__ import annotations

from pathlib import Path
import re
from typing import Iterable

from segpick.models import Sample

from .depth import parse_depth_file

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt


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

    figure, axis = plt.subplots(figsize=(10, 3.2))

    axis.fill_between(
        positions_list,
        depths_list,
        step="mid",
        alpha=0.35,
    )
    axis.plot(
        positions_list,
        depths_list,
        linewidth=0.8,
    )

    if minimum_depth is not None:
        axis.axhline(
            minimum_depth,
            linestyle="--",
            linewidth=0.8,
            label=f"Minimum depth: {minimum_depth}",
        )
        axis.legend(frameon=False, fontsize=8)

    axis.set_xlim(positions_list[0], positions_list[-1])
    axis.set_ylim(bottom=0)
    axis.set_xlabel("Contig position")
    axis.set_ylabel("Read depth")

    if title:
        axis.set_title(title)

    if orf_start is not None and orf_end is not None:
        interval_start = min(orf_start, orf_end)
        interval_end = max(orf_start, orf_end)
        arrow_start, arrow_end = (
            (interval_end, interval_start)
            if orf_strand == "-"
            else (interval_start, interval_end)
        )
        axis.annotate(
            orf_label,
            xy=(arrow_end, -0.20),
            xytext=(arrow_start, -0.20),
            xycoords=("data", "axes fraction"),
            textcoords=("data", "axes fraction"),
            arrowprops={"arrowstyle": "->", "linewidth": 1.2},
            annotation_clip=False,
            ha="center",
            va="center",
            fontsize=8,
        )

    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)

    figure.tight_layout(rect=(0, 0.10, 1, 1))
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
            )
            plot_paths[candidate.id] = output_path

    return plot_paths
