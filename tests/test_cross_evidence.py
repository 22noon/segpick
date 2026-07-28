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
