from __future__ import annotations

from math import sqrt

from segpick.models import ReferenceDotplot, StructuralIntegrity


def _merged(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    result: list[list[int]] = []
    for start, end in sorted((min(a, b), max(a, b)) for a, b in intervals):
        if not result or start > result[-1][1] + 1:
            result.append([start, end])
        else:
            result[-1][1] = max(result[-1][1], end)
    return [(start, end) for start, end in result]


def _largest_internal_gap(intervals: list[tuple[int, int]]) -> int:
    merged = _merged(intervals)
    return max((right[0] - left[1] - 1 for left, right in zip(merged, merged[1:])), default=0)


def _order_consistency(dotplot: ReferenceDotplot) -> float:
    if len(dotplot.hsps) < 2:
        return 1.0 if dotplot.hsps else 0.0
    dominant = dotplot.display_orientation
    if dominant not in {"forward", "reverse"}:
        return 0.5
    ordered = sorted(dotplot.hsps, key=lambda h: (min(h.query_start, h.query_end), max(h.query_start, h.query_end)))
    mids = [(h.subject_start + h.subject_end) / 2 for h in ordered]
    expected = [b >= a for a, b in zip(mids, mids[1:])] if dominant == "forward" else [b <= a for a, b in zip(mids, mids[1:])]
    return sum(expected) / len(expected) if expected else 1.0


def structural_integrity_from_dotplot(dotplot: ReferenceDotplot) -> StructuralIntegrity:
    """Summarise structural agreement without using nucleotide identity."""

    if not dotplot.hsps:
        return StructuralIntegrity(
            reference_id=dotplot.reference_id,
            candidate_coverage=0.0,
            reference_coverage=0.0,
            block_count=0,
            longest_block_fraction=0.0,
            largest_candidate_gap=dotplot.query_length,
            largest_reference_gap=dotplot.reference_length,
            continuity=0.0,
            orientation_consistency=0.0,
            order_consistency=0.0,
            score=0.0,
            status="NO_ALIGNMENT",
        )

    query_intervals = [(h.query_start, h.query_end) for h in dotplot.hsps]
    reference_intervals = [(h.subject_start, h.subject_end) for h in dotplot.hsps]
    query_gap = _largest_internal_gap(query_intervals)
    reference_gap = _largest_internal_gap(reference_intervals)
    gap_fraction = max(
        query_gap / max(dotplot.query_length, 1),
        reference_gap / max(dotplot.reference_length, 1),
    )
    continuity = max(0.0, 1.0 - gap_fraction)
    orientation = dotplot.dominant_orientation_fraction or 0.0
    order = _order_consistency(dotplot)
    longest = max(h.alignment_length for h in dotplot.hsps) / max(
        min(dotplot.query_length, dotplot.reference_length), 1
    )
    coverage = sqrt(dotplot.query_coverage * dotplot.reference_coverage)
    score = max(0.0, min(1.0, coverage * continuity * orientation * order))

    if score >= 0.85 and query_gap == 0 and reference_gap == 0:
        status = "CONTINUOUS"
    elif score >= 0.65:
        status = "MINOR_DISCONTINUITY"
    elif score >= 0.35:
        status = "REVIEW"
    else:
        status = "DISRUPTED"

    return StructuralIntegrity(
        reference_id=dotplot.reference_id,
        candidate_coverage=dotplot.query_coverage,
        reference_coverage=dotplot.reference_coverage,
        block_count=dotplot.block_count,
        longest_block_fraction=min(1.0, longest),
        largest_candidate_gap=query_gap,
        largest_reference_gap=reference_gap,
        continuity=continuity,
        orientation_consistency=orientation,
        order_consistency=order,
        score=score,
        status=status,
    )


def attach_structural_integrity(sample) -> int:
    attached = 0
    for gene in sample.genes.values():
        for candidate in gene.candidates:
            dotplot = candidate.analysis.reference_dotplot
            if dotplot is None:
                candidate.analysis.structural_integrity = None
                continue
            candidate.analysis.structural_integrity = structural_integrity_from_dotplot(dotplot)
            attached += 1
    return attached
