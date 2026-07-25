from __future__ import annotations

from collections.abc import Iterable

from segpick.models import Gene, ProteinContinuity

_COMPLETE_THRESHOLD = 0.90
_REDUNDANT_OVERLAP_THRESHOLD = 0.50


def _merge_intervals(
    intervals: Iterable[tuple[float, float]],
) -> tuple[tuple[float, float], ...]:
    ordered = sorted(
        (max(0.0, start), min(1.0, end))
        for start, end in intervals
        if end > start
    )
    if not ordered:
        return ()

    merged: list[list[float]] = [[ordered[0][0], ordered[0][1]]]
    for start, end in ordered[1:]:
        current = merged[-1]
        if start <= current[1]:
            current[1] = max(current[1], end)
        else:
            merged.append([start, end])
    return tuple((start, end) for start, end in merged)


def _coverage(intervals: Iterable[tuple[float, float]]) -> float:
    return sum(end - start for start, end in _merge_intervals(intervals))


def _uncovered_regions(
    merged: tuple[tuple[float, float], ...],
) -> tuple[tuple[float, float], ...]:
    if not merged:
        return ((0.0, 1.0),)

    gaps: list[tuple[float, float]] = []
    cursor = 0.0
    for start, end in merged:
        if start > cursor:
            gaps.append((cursor, start))
        cursor = max(cursor, end)
    if cursor < 1.0:
        gaps.append((cursor, 1.0))
    return tuple(gaps)


def _has_redundant_overlap(
    intervals: tuple[tuple[str, float, float], ...],
) -> bool:
    for index, (_, start_a, end_a) in enumerate(intervals):
        length_a = end_a - start_a
        for _, start_b, end_b in intervals[index + 1 :]:
            length_b = end_b - start_b
            overlap = max(0.0, min(end_a, end_b) - max(start_a, start_b))
            shorter = min(length_a, length_b)
            if shorter > 0 and overlap / shorter >= _REDUNDANT_OVERLAP_THRESHOLD:
                return True
    return False


def analyse_protein_continuity(gene: Gene) -> ProteinContinuity:
    """Summarise how candidate BLASTX hits cover expected protein coordinates.

    Coordinates are normalised independently by each hit's subject length. This
    is a conservative assembly-level review aid and does not alter ranking.
    """

    intervals = tuple(
        (
            candidate.id,
            (
                min(
                    candidate.analysis.blastx.subject_start,
                    candidate.analysis.blastx.subject_end,
                )
                - 1
            )
            / candidate.analysis.blastx.subject_length,
            max(
                candidate.analysis.blastx.subject_start,
                candidate.analysis.blastx.subject_end,
            )
            / candidate.analysis.blastx.subject_length,
        )
        for candidate in gene.candidates
        if candidate.analysis.blastx is not None
        and candidate.analysis.blastx.subject_length > 0
    )

    if not intervals:
        return ProteinContinuity(
            classification="unavailable",
            candidate_count=0,
            combined_coverage=0.0,
            best_single_coverage=0.0,
            complementary_candidate_ids=(),
            redundant_overlap=False,
            uncovered_regions=((0.0, 1.0),),
            summary="Protein continuity could not be evaluated because no usable DIAMOND coordinates were available.",
            findings=(),
        )

    candidate_intervals = tuple((start, end) for _, start, end in intervals)
    merged = _merge_intervals(candidate_intervals)
    combined_coverage = _coverage(candidate_intervals)
    best_single_coverage = max(end - start for _, start, end in intervals)
    redundant_overlap = _has_redundant_overlap(intervals)
    uncovered_regions = _uncovered_regions(merged)

    findings: list[str] = []
    complementary_ids: tuple[str, ...] = ()

    if best_single_coverage >= _COMPLETE_THRESHOLD:
        classification = "complete_single_candidate"
        summary = "At least one candidate spans most of the expected protein length."
    elif combined_coverage >= _COMPLETE_THRESHOLD and len(intervals) >= 2:
        classification = "complementary_fragments"
        complementary_ids = tuple(candidate_id for candidate_id, _, _ in intervals)
        summary = (
            "Multiple candidates collectively span most of the expected protein, "
            "consistent with a possible split assembly."
        )
        findings.append(
            "Complementary protein regions are distributed across "
            + ", ".join(complementary_ids)
            + "."
        )
    else:
        classification = "incomplete_recovery"
        summary = (
            "Available candidate alignments collectively cover "
            f"{combined_coverage:.1%} of the expected protein coordinate range."
        )

    if redundant_overlap:
        findings.append(
            "Two or more candidates cover substantially overlapping protein regions, "
            "which may represent redundant fragments."
        )

    return ProteinContinuity(
        classification=classification,
        candidate_count=len(intervals),
        combined_coverage=combined_coverage,
        best_single_coverage=best_single_coverage,
        complementary_candidate_ids=complementary_ids,
        redundant_overlap=redundant_overlap,
        uncovered_regions=uncovered_regions,
        summary=summary,
        findings=tuple(findings),
    )
