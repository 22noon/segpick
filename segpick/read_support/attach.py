from __future__ import annotations

from pathlib import Path

from segpick.models import CandidateContig, Gene, ReadSupportMetrics

from .depth import calculate_read_support, parse_depth_file


def attach_read_support(
    candidate: CandidateContig,
    position_depths: dict[int, int],
    *,
    minimum_depth: int = 3,
    terminal_fraction: float = 0.05,
    minimum_terminal_bases: int = 50,
) -> ReadSupportMetrics:
    """Calculate and attach read-support metrics to one candidate."""

    metrics = calculate_read_support(
        sequence_id=candidate.id,
        position_depths=position_depths,
        sequence_length=candidate.length,
        minimum_depth=minimum_depth,
        terminal_fraction=terminal_fraction,
        minimum_terminal_bases=minimum_terminal_bases,
    )

    candidate.analysis.read_support = metrics
    return metrics


def attach_gene_depths(
    gene: Gene,
    depths: dict[str, dict[int, int]],
    *,
    minimum_depth: int = 3,
    terminal_fraction: float = 0.05,
    minimum_terminal_bases: int = 50,
    strict: bool = False,
) -> dict[str, ReadSupportMetrics]:
    """Attach depth-derived metrics to matching candidates in one gene.

    Missing candidates are skipped unless ``strict`` is enabled.
    """

    attached: dict[str, ReadSupportMetrics] = {}

    for candidate in gene.candidates:
        position_depths = depths.get(candidate.id)

        if position_depths is None:
            if strict:
                raise KeyError(
                    f"No depth data found for candidate {candidate.id!r}"
                )
            continue

        attached[candidate.id] = attach_read_support(
            candidate,
            position_depths,
            minimum_depth=minimum_depth,
            terminal_fraction=terminal_fraction,
            minimum_terminal_bases=minimum_terminal_bases,
        )

    return attached


def attach_gene_depth_file(
    gene: Gene,
    path: str | Path,
    **kwargs: object,
) -> dict[str, ReadSupportMetrics]:
    """Parse a depth file and attach matching candidate metrics."""

    return attach_gene_depths(
        gene,
        parse_depth_file(path),
        **kwargs,
    )
