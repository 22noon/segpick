from __future__ import annotations

from .engine import ContributionSpec, StructuredCrossEvidenceRule, register_rule


for rule in (
    StructuredCrossEvidenceRule(
        "segpick:read_supported_reference_absent_sequence", "1.1", "segpick.core",
        frozenset({"reference_compatibility", "read_evidence"}),
        (
            ContributionSpec("reference_compatibility", "unsupported_internal_candidate_region", 1.0, "Defines the reference-absent interval."),
            ContributionSpec("read_evidence", "read_region_supported", 1.0, "Shows that the biologically relevant region has regional read support."),
        ),
        "segpick:read_supported_reference_absent_sequence",
        "Reference-absent sequence has regional read support",
        "An internal candidate interval absent from the closest reference occurs in a candidate whose biologically relevant region is supported by read coverage. This supports the existence of the sequence but does not by itself establish that the interval is assembled at the correct locus.",
        "information", 88,
        supporting=(
            ContributionSpec("junction_read_support", "reference_absent_interval_smooth_both_junctions", 0.5, "Smooth local depth would additionally support placement."),
        ),
        contradicting=(
            ContributionSpec("junction_read_support", "reference_absent_sequence_supported_junction_discontinuous", 0.8, "A junction depth discontinuity weakens confidence in placement, not necessarily sequence existence."),
        ),
        limitations=("Regional read coverage supports sequence authenticity more directly than placement authenticity.",),
    ),
    StructuredCrossEvidenceRule(
        "segpick:reference_absent_interval_placement_depth_supported", "1.1", "segpick.core",
        frozenset({"reference_compatibility", "junction_read_support"}),
        (
            ContributionSpec("reference_compatibility", "unsupported_internal_candidate_region", 1.0),
            ContributionSpec("junction_read_support", "reference_absent_interval_smooth_both_junctions", 1.2),
        ),
        "segpick:reference_absent_interval_placement_depth_supported",
        "Reference-absent interval has smooth depth support at both junctions",
        "The reference-absent sequence is regionally covered and local read depth remains smooth across both attachment points. This supports, but does not prove, that the interval is integrated at the assembled locus.",
        "information", 95,
        limitations=(
            "Depth continuity is not direct evidence that individual reads or read pairs span both junctions.",
            "Repeated or ambiguously mapped sequence can retain smooth depth across an incorrect join.",
        ),
    ),
    StructuredCrossEvidenceRule(
        "segpick:genuine_sequence_possible_misplacement", "1.1", "segpick.core",
        frozenset({"reference_compatibility", "junction_read_support"}),
        (
            ContributionSpec("reference_compatibility", "unsupported_internal_candidate_region", 1.0),
            ContributionSpec("junction_read_support", "reference_absent_sequence_supported_junction_discontinuous", 1.3),
        ),
        "segpick:genuine_sequence_possible_misplacement",
        "Reference-absent sequence may be genuine but misplaced",
        "The reference-absent interval has regional read support, but one or both attachment points show an abrupt depth transition. The sequence may therefore be real while its placement or neighbouring join requires review.",
        "review", 110,
        contradicting=(
            ContributionSpec("junction_read_support", "reference_absent_interval_smooth_both_junctions", 1.0),
        ),
        limitations=(
            "A depth transition can also reflect amplification bias, mapping ambiguity, or genuine local coverage variation.",
            "Confirm placement with junction-spanning reads, paired-end consistency, long reads, or assembly-graph inspection.",
        ),
    ),
    StructuredCrossEvidenceRule(
        "segpick:reference_relative_rearrangement", "1.0", "segpick.core",
        frozenset({"reference_compatibility", "structural_integrity"}),
        (
            ContributionSpec("reference_compatibility", "reference_block_order_disrupted", 1.0),
            ContributionSpec("structural_integrity", "structural_integrity_summary", 0.9),
        ),
        "segpick:reference_relative_rearrangement",
        "Reference-relative rearrangement with coherent assembly structure",
        "Reference alignment blocks are reordered while the independent structural channel remains coherent, supporting review for genuine reference-relative structural variation.",
        "review", 80,
    ),
    StructuredCrossEvidenceRule(
        "segpick:reference_relative_inversion", "1.0", "segpick.core",
        frozenset({"reference_compatibility", "structural_integrity"}),
        (
            ContributionSpec("reference_compatibility", "unexpected_reference_orientation_switch", 1.0),
            ContributionSpec("structural_integrity", "structural_integrity_summary", 0.9),
        ),
        "segpick:reference_relative_inversion",
        "Reference-relative inversion with coherent assembly structure",
        "A reference-relative orientation switch is present without independent evidence of structural incoherence.",
        "review", 85,
    ),
):
    register_rule(rule)
