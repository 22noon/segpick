from __future__ import annotations

from statistics import median

from segpick.models import BoundaryCoverageAssessment, CandidateContig, Sample


def _depths(profile: dict[int, int], start: int, end: int) -> list[int]:
    if end < start:
        return []
    return [profile.get(position, 0) for position in range(start, end + 1)]


def assess_reference_boundaries(
    candidate: CandidateContig,
    *,
    minimum_depth: int = 3,
    merge_gap: int = 25,
    flank_window: int = 30,
) -> tuple[BoundaryCoverageAssessment, ...]:
    """Classify local read coverage across internal reference-alignment gaps."""

    dotplot = candidate.analysis.reference_dotplot
    profile = candidate.analysis.depth_profile
    if dotplot is None or not dotplot.hsps or not profile:
        return ()

    intervals = dotplot.merged_query_intervals(maximum_gap=merge_gap)
    assessments: list[BoundaryCoverageAssessment] = []
    for left, right in zip(intervals, intervals[1:]):
        gap_start = left[1] + 1
        gap_end = right[0] - 1
        if gap_end < gap_start:
            continue

        left_depths = _depths(
            profile,
            max(1, gap_start - flank_window),
            gap_start - 1,
        )
        gap_depths = _depths(profile, gap_start, gap_end)
        right_depths = _depths(
            profile,
            gap_end + 1,
            min(candidate.length, gap_end + flank_window),
        )
        if not left_depths or not right_depths or not gap_depths:
            continue

        left_median = float(median(left_depths))
        gap_median = float(median(gap_depths))
        right_median = float(median(right_depths))
        baseline = float(median(left_depths + right_depths))
        ratio = gap_median / baseline if baseline > 0 else None
        zero_fraction = sum(depth == 0 for depth in gap_depths) / len(gap_depths)
        flank_max = max(left_median, right_median)
        flank_min = min(left_median, right_median)

        if baseline <= 0:
            classification = "insufficient_context"
            severity = "informational"
            summary = "Coverage is too low around this structural boundary to classify it reliably."
        elif left_median < minimum_depth and right_median < minimum_depth:
            classification = "low_coverage_both_sides"
            severity = "review"
            summary = "Low read depth occurs on both sides of this reference-alignment gap."
        elif gap_median < minimum_depth and zero_fraction >= 0.5:
            classification = "coverage_gap"
            severity = "review"
            summary = "A read-coverage gap coincides with this reference-alignment gap."
        elif ratio is not None and ratio < 0.5:
            classification = "local_coverage_decrease"
            severity = "review"
            summary = "A marked local coverage decrease coincides with this reference-alignment gap."
        elif flank_max > 0 and flank_min / flank_max < 0.5:
            classification = "asymmetric_flank_drop"
            severity = "review"
            summary = "Read depth changes sharply across this reference-alignment boundary."
        else:
            classification = "continuous_coverage"
            severity = "informational"
            summary = "Read coverage remains broadly continuous across this reference-alignment gap."

        assessments.append(
            BoundaryCoverageAssessment(
                candidate_id=candidate.id,
                reference_id=dotplot.reference_id,
                gap_start=gap_start,
                gap_end=gap_end,
                gap_length=gap_end - gap_start + 1,
                flank_window=flank_window,
                left_median_depth=left_median,
                gap_median_depth=gap_median,
                right_median_depth=right_median,
                baseline_depth=baseline,
                gap_to_baseline_ratio=ratio,
                zero_fraction=zero_fraction,
                classification=classification,
                severity=severity,
                summary=summary,
            )
        )
    return tuple(assessments)


def attach_boundary_coverage_assessments(
    sample: Sample,
    *,
    minimum_depth: int = 3,
    merge_gap: int = 25,
    flank_window: int = 30,
) -> int:
    """Attach cross-evidence boundary assessments to all eligible candidates."""

    attached = 0
    for gene in sample.genes.values():
        for candidate in gene.candidates:
            candidate.analysis.boundary_coverage = assess_reference_boundaries(
                candidate,
                minimum_depth=minimum_depth,
                merge_gap=merge_gap,
                flank_window=flank_window,
            )
            attached += len(candidate.analysis.boundary_coverage)
    return attached
