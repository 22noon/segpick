from __future__ import annotations

from segpick.analysis.structural_integrity import _largest_internal_gap, _order_consistency
from segpick.models import ReferenceCompatibility, ReferenceDotplot


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _overlap(a: tuple[int, int], b: tuple[int, int]) -> int:
    left = max(min(a), min(b))
    right = min(max(a), max(b))
    return max(0, right - left + 1)


def _duplicated_reference_bases(dotplot: ReferenceDotplot) -> int:
    """Estimate reference bases represented by separate candidate regions.

    Overlap between subject intervals is counted only when the corresponding
    query intervals do not overlap, which is compatible with a duplicated or
    repeated representation of the same expected reference region.
    """

    duplicated = 0
    hsps = tuple(dotplot.hsps)
    for index, left in enumerate(hsps):
        for right in hsps[index + 1 :]:
            query_overlap = _overlap(
                (left.query_start, left.query_end),
                (right.query_start, right.query_end),
            )
            if query_overlap:
                continue
            duplicated += _overlap(
                (left.subject_start, left.subject_end),
                (right.subject_start, right.subject_end),
            )
    return min(duplicated, dotplot.reference_length)


def reference_compatibility_from_dotplot(dotplot: ReferenceDotplot) -> ReferenceCompatibility:
    """Measure agreement with expected reference organisation.

    Percentage identity is deliberately excluded. Internal query gaps measure
    unsupported candidate sequence; internal subject gaps measure missing
    expected reference sequence. Terminal differences are represented through
    overall reference coverage rather than being labelled rearrangements.
    """

    if not dotplot.hsps:
        return ReferenceCompatibility(
            reference_id=dotplot.reference_id,
            unsupported_internal_candidate_bases=dotplot.query_length,
            missing_internal_reference_bases=dotplot.reference_length,
            duplicated_reference_bases=0,
            internal_candidate_compatibility=0.0,
            expected_reference_completeness=0.0,
            block_order_compatibility=0.0,
            orientation_compatibility=0.0,
            duplication_compatibility=1.0,
            score=0.0,
            status="NO_ALIGNMENT",
        )

    query_gap = _largest_internal_gap(
        [(h.query_start, h.query_end) for h in dotplot.hsps]
    )
    reference_gap = _largest_internal_gap(
        [(h.subject_start, h.subject_end) for h in dotplot.hsps]
    )
    duplicated = _duplicated_reference_bases(dotplot)

    internal_candidate = _clamp(1.0 - query_gap / max(dotplot.query_length, 1))
    expected_reference = _clamp(
        dotplot.reference_coverage
        * (1.0 - reference_gap / max(dotplot.reference_length, 1))
    )
    order = _order_consistency(dotplot)
    orientation = dotplot.dominant_orientation_fraction or 0.0
    duplication = _clamp(1.0 - duplicated / max(dotplot.reference_length, 1))

    components = (internal_candidate, expected_reference, order, orientation, duplication)
    score = sum(components) / len(components)

    if score >= 0.90 and query_gap == 0 and reference_gap == 0 and duplicated == 0:
        status = "REFERENCE_COMPATIBLE"
    elif score >= 0.75:
        status = "MINOR_DIFFERENCE"
    elif score >= 0.50:
        status = "REVIEW"
    else:
        status = "REFERENCE_INCOMPATIBLE"

    return ReferenceCompatibility(
        reference_id=dotplot.reference_id,
        unsupported_internal_candidate_bases=query_gap,
        missing_internal_reference_bases=reference_gap,
        duplicated_reference_bases=duplicated,
        internal_candidate_compatibility=internal_candidate,
        expected_reference_completeness=expected_reference,
        block_order_compatibility=order,
        orientation_compatibility=orientation,
        duplication_compatibility=duplication,
        score=score,
        status=status,
    )


def attach_reference_compatibility(sample) -> int:
    attached = 0
    for gene in sample.genes.values():
        for candidate in gene.candidates:
            dotplot = candidate.analysis.reference_dotplot
            if dotplot is None:
                candidate.analysis.reference_compatibility = None
                continue
            candidate.analysis.reference_compatibility = reference_compatibility_from_dotplot(dotplot)
            attached += 1
    return attached
