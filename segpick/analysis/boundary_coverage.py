from __future__ import annotations

from statistics import median

from segpick.models import BoundaryCoverageAssessment, CandidateContig, Sample


def _depths(profile: dict[int, int], start: int, end: int) -> list[int]:
    if end < start:
        return []
    return [profile.get(position, 0) for position in range(start, end + 1)]


def _balanced_ratio(left: float, right: float) -> float | None:
    """Return the smaller/larger depth ratio, preserving zero-depth meaning."""

    high = max(left, right)
    if high <= 0:
        return None
    return min(left, right) / high


def assess_reference_boundaries(
    candidate: CandidateContig,
    *,
    minimum_depth: int = 3,
    merge_gap: int = 25,
    flank_window: int = 30,
    junction_window: int = 10,
    smooth_ratio_threshold: float = 0.5,
) -> tuple[BoundaryCoverageAssessment, ...]:
    """Classify regional and junction read depth for reference-absent intervals.

    Junction smoothness compares short windows immediately inside and outside
    each boundary.  It can identify abrupt depth transitions, but samtools
    depth alone cannot establish that individual reads span a junction.
    """

    if junction_window < 1:
        raise ValueError("junction_window must be at least 1")
    if not 0 < smooth_ratio_threshold <= 1:
        raise ValueError("smooth_ratio_threshold must be in (0, 1]")

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

        left_depths = _depths(profile, max(1, gap_start - flank_window), gap_start - 1)
        gap_depths = _depths(profile, gap_start, gap_end)
        right_depths = _depths(profile, gap_end + 1, min(candidate.length, gap_end + flank_window))
        if not left_depths or not right_depths or not gap_depths:
            continue

        local_window = min(junction_window, len(gap_depths), len(left_depths), len(right_depths))
        left_outer = left_depths[-local_window:]
        left_inner = gap_depths[:local_window]
        right_inner = gap_depths[-local_window:]
        right_outer = right_depths[:local_window]

        left_median = float(median(left_depths))
        gap_median = float(median(gap_depths))
        right_median = float(median(right_depths))
        left_inner_median = float(median(left_inner))
        right_inner_median = float(median(right_inner))
        left_outer_median = float(median(left_outer))
        right_outer_median = float(median(right_outer))
        baseline = float(median(left_depths + right_depths))
        ratio = gap_median / baseline if baseline > 0 else None
        zero_fraction = sum(depth == 0 for depth in gap_depths) / len(gap_depths)

        left_junction_ratio = _balanced_ratio(left_outer_median, left_inner_median)
        right_junction_ratio = _balanced_ratio(right_inner_median, right_outer_median)
        left_assessable = max(left_outer_median, left_inner_median) >= minimum_depth
        right_assessable = max(right_inner_median, right_outer_median) >= minimum_depth
        left_smooth = (
            left_junction_ratio >= smooth_ratio_threshold
            if left_assessable and left_junction_ratio is not None
            else None
        )
        right_smooth = (
            right_junction_ratio >= smooth_ratio_threshold
            if right_assessable and right_junction_ratio is not None
            else None
        )
        regional_supported = gap_median >= minimum_depth and zero_fraction < 0.5

        if baseline <= 0:
            classification = "insufficient_context"
            severity = "informational"
            placement = "not_assessable"
            summary = "Coverage is too low around this reference-absent interval to classify it reliably."
        elif not regional_supported and gap_median < minimum_depth and zero_fraction >= 0.5:
            classification = "coverage_gap"
            severity = "review"
            placement = "sequence_not_supported"
            summary = "A read-coverage gap occurs across this reference-absent candidate interval."
        elif not regional_supported and ratio is not None and ratio < 0.5:
            classification = "local_coverage_decrease"
            severity = "review"
            placement = "sequence_weakly_supported"
            summary = "A marked local coverage decrease occurs across this reference-absent candidate interval."
        elif regional_supported and left_smooth is True and right_smooth is True:
            classification = "continuous_coverage"
            severity = "informational"
            placement = "placement_depth_supported"
            summary = "The reference-absent interval is covered and read depth remains smooth across both junctions."
        elif regional_supported and (left_smooth is False or right_smooth is False):
            classification = "supported_with_junction_discontinuity"
            severity = "review"
            placement = "sequence_supported_placement_uncertain"
            side = (
                "both junctions" if left_smooth is False and right_smooth is False
                else "the left junction" if left_smooth is False
                else "the right junction"
            )
            summary = (
                "The reference-absent sequence has regional read support, but depth changes sharply at "
                f"{side}; the sequence may be genuine while its assembled placement remains uncertain."
            )
        elif regional_supported:
            classification = "supported_junctions_not_assessable"
            severity = "informational"
            placement = "sequence_supported_placement_not_assessable"
            summary = "The reference-absent interval is covered, but one or both junctions lack enough depth for a smoothness assessment."
        else:
            classification = "low_coverage_both_sides"
            severity = "review"
            placement = "not_assessable"
            summary = "Low read depth prevents reliable interpretation of this reference-absent interval and its junctions."

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
                junction_window=local_window,
                left_inner_median_depth=left_inner_median,
                right_inner_median_depth=right_inner_median,
                left_junction_ratio=left_junction_ratio,
                right_junction_ratio=right_junction_ratio,
                left_junction_smooth=left_smooth,
                right_junction_smooth=right_smooth,
                regional_sequence_supported=regional_supported,
                placement_interpretation=placement,
            )
        )
    return tuple(assessments)


def attach_boundary_coverage_assessments(
    sample: Sample,
    *,
    minimum_depth: int = 3,
    merge_gap: int = 25,
    flank_window: int = 30,
    junction_window: int = 10,
    smooth_ratio_threshold: float = 0.5,
) -> int:
    """Attach regional and junction-depth assessments to eligible candidates."""

    attached = 0
    for gene in sample.genes.values():
        for candidate in gene.candidates:
            candidate.analysis.boundary_coverage = assess_reference_boundaries(
                candidate,
                minimum_depth=minimum_depth,
                merge_gap=merge_gap,
                flank_window=flank_window,
                junction_window=junction_window,
                smooth_ratio_threshold=smooth_ratio_threshold,
            )
            attached += len(candidate.analysis.boundary_coverage)
    return attached
