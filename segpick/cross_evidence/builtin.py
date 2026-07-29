from __future__ import annotations

from .engine import ContributionSpec, StructuredCrossEvidenceRule, register_rule


for rule in (
    StructuredCrossEvidenceRule(
        "segpick:read_supported_reference_absent_sequence", "1.0", "segpick.core",
        frozenset({"reference_compatibility", "read_evidence"}),
        (
            ContributionSpec("reference_compatibility", "unsupported_internal_candidate_region", 1.0, "Defines the reference-absent interval."),
            ContributionSpec("read_evidence", "read_evidence_summary", 1.0, "Provides independent read support."),
        ),
        "segpick:read_supported_reference_absent_sequence",
        "Reference-absent sequence is supported by reads",
        "An internal candidate interval absent from the closest reference occurs in a candidate whose biologically relevant region is supported by read coverage. This favours genuine divergence or insertion over an unsupported assembly addition.",
        "information", 90,
        limitations=("Read support is currently assessed across the biologically relevant region rather than both insertion junctions specifically.",),
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
