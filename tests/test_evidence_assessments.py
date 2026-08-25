from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from segpick.analysis.evidence_assessments import CHANNEL_REGISTRY, build_evidence_assessments
from segpick.models import CandidateContig, ContigMetadata, ReferenceCompatibility
from segpick.scoring import CandidateRecommendation, Evidence
from segpick.scoring.scorer import ScoredEvidence


def recommendation():
    evidence = Evidence(protein_confidence=.9, length_plausibility=.8, structural_integrity=.7, coverage_sufficiency=.8, coverage_integrity=.6)
    scored = ScoredEvidence(score=.8, contributions={}, effective_weights={})
    return CandidateRecommendation("c1", 1000, .9, evidence, scored)


def candidate():
    c = CandidateContig(id="c1", record=SeqRecord(Seq("A" * 1000), id="c1"), metadata=ContigMetadata(score=1, confidence=.9, cluster="x", segment="1"))
    c.analysis.reference_compatibility = ReferenceCompatibility("r1", 120, 0, 0, .88, .92, 1, 1, 1, .91, "MINOR_DIFFERENCE")
    return c


def test_registry_contains_first_class_channels():
    assert tuple(CHANNEL_REGISTRY) == ("protein_confidence", "read_evidence", "junction_read_support", "structural_integrity", "reference_compatibility", "length_plausibility")


def test_reference_assessment_has_documented_confidence_and_finding():
    items = {item.channel_id: item for item in build_evidence_assessments(candidate(), recommendation())}
    item = items["reference_compatibility"]
    assert item.participates_in_ranking is False
    assert item.confidence.method == "reference_compatibility_confidence"
    assert item.confidence.version == "1.0"
    assert "120 nt" in item.key_finding.title


def test_junction_not_assessable_explains_missing_prerequisite():
    items = {item.channel_id: item for item in build_evidence_assessments(candidate(), recommendation())}
    item = items["junction_read_support"]
    assert item.status == "not_assessable"
    assert item.diagnostics is not None
    assert item.diagnostics.has_failure is True
    assert item.diagnostics.stop_reason
    checks = {check.check_id: check for check in item.diagnostics.checks}
    assert checks["reference_dotplot_available"].status == "fail"
    assert checks["depth_profile_available"].status == "fail"
    assert "dot plot" in item.diagnostics.stop_reason.lower()
    payload = item.to_dict()
    assert payload["diagnostics"]["has_failure"] is True
