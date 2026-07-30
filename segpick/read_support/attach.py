from __future__ import annotations

from pathlib import Path

from segpick.models import CandidateContig, Gene, ReadSupportMetrics

from .depth import calculate_read_support, parse_depth_file


def _evidence_region(candidate: CandidateContig) -> tuple[int, int, str]:
    anchored = candidate.analysis.blastx_anchored_orf
    if anchored is not None:
        return anchored.start, anchored.end, "blastx_anchored_orf"

    selected = candidate.analysis.orf.best_orf if candidate.analysis.orf else None
    if selected is not None:
        return selected.start, selected.end, "selected_orf"

    return 0, candidate.length, "whole_contig_fallback"


def attach_read_support(
    candidate: CandidateContig,
    position_depths: dict[int, int],
    *,
    minimum_depth: int = 3,
    terminal_fraction: float = 0.05,
    minimum_terminal_bases: int = 50,
) -> ReadSupportMetrics:
    """Calculate and attach ORF-centred read-evidence measurements."""

    region_start, region_end, region_source = _evidence_region(candidate)
    metrics = calculate_read_support(
        sequence_id=candidate.id,
        position_depths=position_depths,
        sequence_length=candidate.length,
        region_start=region_start,
        region_end=region_end,
        region_source=region_source,
        minimum_depth=minimum_depth,
        terminal_fraction=terminal_fraction,
        minimum_terminal_bases=minimum_terminal_bases,
    )

    candidate.analysis.read_support = metrics
    candidate.analysis.depth_profile = dict(position_depths)
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
    attached: dict[str, ReadSupportMetrics] = {}
    for candidate in gene.candidates:
        position_depths = depths.get(candidate.id)
        if position_depths is None:
            if strict:
                raise KeyError(f"No depth data found for candidate {candidate.id!r}")
            continue
        attached[candidate.id] = attach_read_support(
            candidate,
            position_depths,
            minimum_depth=minimum_depth,
            terminal_fraction=terminal_fraction,
            minimum_terminal_bases=minimum_terminal_bases,
        )
    return attached


def attach_gene_depth_file(gene: Gene, path: str | Path, **kwargs: object) -> dict[str, ReadSupportMetrics]:
    return attach_gene_depths(gene, parse_depth_file(path), **kwargs)
