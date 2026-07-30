from segpick.cross_evidence import CrossEvidenceContext, evaluate_cross_evidence
from segpick.models import ConfidenceAssessment, EvidenceAssessment, EvidenceFinding


def assessment(channel, finding, level="high"):
    return EvidenceAssessment(
        channel, channel, "1.0", "strong", 0.9,
        ConfidenceAssessment(level, 0.9, f"{channel}_confidence", "1.0"),
        EvidenceFinding(finding, finding.replace("_", " "), "test"),
    )


def test_read_supported_reference_absent_sequence_is_generated():
    context = CrossEvidenceContext((
        assessment("reference_compatibility", "unsupported_internal_candidate_region"),
        assessment("read_evidence", "read_evidence_summary"),
    ), "contig_a", "VP2")
    findings = evaluate_cross_evidence(context)
    assert findings[0].finding_id == "segpick:read_supported_reference_absent_sequence"
    assert findings[0].participates_in_ranking is False
    assert {item.channel_id for item in findings[0].supporting_evidence} == {"reference_compatibility", "read_evidence"}


def test_rule_is_skipped_when_required_finding_is_missing():
    context = CrossEvidenceContext((assessment("reference_compatibility", "reference_organisation_compatible"), assessment("read_evidence", "read_evidence_summary")), "contig_a", "VP2")
    assert not evaluate_cross_evidence(context)


def test_cross_evidence_finding_serialises_provenance():
    context = CrossEvidenceContext((assessment("reference_compatibility", "unexpected_reference_orientation_switch"), assessment("structural_integrity", "structural_integrity_summary")), "contig_a", "VP2")
    payload = evaluate_cross_evidence(context)[0].to_dict()
    assert payload["rule_version"] == "1.0"
    assert payload["source_plugin"] == "segpick.core"


def test_v2_confidence_is_propagated_from_channel_assessments():
    context = CrossEvidenceContext((
        assessment("reference_compatibility", "unsupported_internal_candidate_region", "high"),
        assessment("read_evidence", "read_evidence_summary", "moderate"),
    ), "contig_a", "VP2")
    finding = evaluate_cross_evidence(context)[0]
    assert finding.confidence_score is not None
    assert 0.6 < finding.confidence_score < 1.0
    assert finding.confidence_method == "weighted_evidence_contributions"
    assert finding.match_status == "complete"


def test_structured_reasoner_records_contradictory_and_missing_evidence():
    from segpick.cross_evidence import ContributionSpec, StructuredCrossEvidenceRule

    rule = StructuredCrossEvidenceRule(
        rule_id="lab:test_reasoner", version="1.0", source_plugin="lab.plugin",
        required_channels=frozenset({"reference_compatibility"}),
        required=(ContributionSpec("reference_compatibility", "unsupported_internal_candidate_region"),),
        supporting=(ContributionSpec("read_evidence", "read_evidence_summary"),),
        contradicting=(ContributionSpec("structural_integrity", "structural_integrity_summary"),),
        output_id="lab:test_finding", title="Test finding", description="Test", severity="review", priority=1,
        allow_partial=True,
    )
    context = CrossEvidenceContext((
        assessment("reference_compatibility", "unsupported_internal_candidate_region"),
        assessment("structural_integrity", "structural_integrity_summary"),
    ), "contig_a", "VP2")
    finding = rule.evaluate(context)[0]
    assert finding.match_status == "contested"
    assert finding.conflicting_evidence[0].channel_id == "structural_integrity"
    assert finding.missing_contributions[0].channel_id == "read_evidence"
    payload = finding.to_dict()
    assert payload["contradiction_contributions"]
    assert payload["missing_contributions"]


def test_partial_reasoner_can_emit_incomplete_match():
    from segpick.cross_evidence import ContributionSpec, StructuredCrossEvidenceRule

    rule = StructuredCrossEvidenceRule(
        rule_id="lab:partial", version="1.0", source_plugin="lab.plugin",
        required_channels=frozenset({"reference_compatibility", "read_evidence"}),
        required=(
            ContributionSpec("reference_compatibility", "unsupported_internal_candidate_region"),
            ContributionSpec("read_evidence", "read_evidence_summary"),
        ),
        output_id="lab:partial_finding", title="Partial finding", description="Test", severity="review", priority=1,
        allow_partial=True, minimum_required_fraction=0.5,
    )
    context = CrossEvidenceContext((assessment("reference_compatibility", "unsupported_internal_candidate_region"),), "contig_a", "VP2")
    finding = rule.evaluate(context)[0]
    assert finding.match_status == "partial"
    assert finding.evidence_completeness == 0.5
    assert finding.missing_contributions[0].channel_id == "read_evidence"


def test_supported_sequence_with_discontinuous_junction_suggests_misplacement():
    context = CrossEvidenceContext((
        assessment("reference_compatibility", "unsupported_internal_candidate_region", "high"),
        assessment("read_evidence", "read_region_supported", "high"),
        assessment("junction_read_support", "reference_absent_sequence_supported_junction_discontinuous", "high"),
    ), "contig_a", "VP2")
    findings = evaluate_cross_evidence(context)
    by_id = {item.finding_id: item for item in findings}
    result = by_id["segpick:genuine_sequence_possible_misplacement"]
    assert result.match_status == "complete"
    assert result.severity == "review"
    assert result.confidence_score is not None


def test_discontinuous_junction_generates_misplacement_without_global_read_support():
    """The junction finding already includes regional sequence support."""
    context = CrossEvidenceContext((
        assessment("reference_compatibility", "unsupported_internal_candidate_region", "high"),
        assessment("junction_read_support", "reference_absent_sequence_supported_junction_discontinuous", "high"),
    ), "contig_a", "VP2")

    findings = evaluate_cross_evidence(context)
    by_id = {item.finding_id: item for item in findings}

    result = by_id["segpick:genuine_sequence_possible_misplacement"]
    assert result.match_status == "complete"
    assert result.rule_version == "1.1"
    assert {item.channel_id for item in result.support_contributions} == {
        "reference_compatibility",
        "junction_read_support",
    }


def test_smooth_both_junctions_supports_assembled_placement():
    context = CrossEvidenceContext((
        assessment("reference_compatibility", "unsupported_internal_candidate_region", "high"),
        assessment("read_evidence", "read_region_supported", "high"),
        assessment("junction_read_support", "reference_absent_interval_smooth_both_junctions", "high"),
    ), "contig_a", "VP2")
    findings = evaluate_cross_evidence(context)
    ids = {item.finding_id for item in findings}
    assert "segpick:reference_absent_interval_placement_depth_supported" in ids
