from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from segpick.analysis.convergence import detect_evidence_convergence
from segpick.analysis.findings import candidate_biological_findings
from segpick.models import CandidateContig, ContigMetadata, ObservationInterval


def observation(start, end, source, observation_type):
    return ObservationInterval(
        coordinate_system="reference_protein:ref1",
        start=start,
        end=end,
        observation_type=observation_type,
        source=source,
        description=observation_type,
    )


def make_candidate():
    return CandidateContig(
        id="contig_a",
        record=SeqRecord(Seq("ATGAAATAA"), id="contig_a"),
        metadata=ContigMetadata(
            segment="1", score=1.0, confidence=1.0, cluster="c1"
        ),
    )


def test_detects_convergence_between_independent_sources():
    observations = (
        observation(214, 217, "protein_alignment", "internal_deletion"),
        observation(219, 225, "read_coverage", "coverage_drop"),
    )

    result = detect_evidence_convergence(observations, "contig_a")

    assert len(result) == 1
    assert result[0].start == 214
    assert result[0].end == 225
    assert result[0].sources == ("protein_alignment", "read_coverage")
    assert result[0].strength == "moderate"


def test_same_source_does_not_create_convergence():
    observations = (
        observation(10, 12, "protein_alignment", "internal_deletion"),
        observation(13, 15, "protein_alignment", "internal_insertion"),
    )

    assert detect_evidence_convergence(observations, "contig_a") == ()


def test_distant_observations_remain_separate():
    observations = (
        observation(10, 12, "protein_alignment", "internal_deletion"),
        observation(20, 22, "read_coverage", "coverage_drop"),
    )

    assert detect_evidence_convergence(observations, "contig_a") == ()


def test_candidate_findings_include_convergence():
    candidate = make_candidate()
    candidate.analysis.observations = (
        observation(50, 52, "protein_alignment", "internal_deletion"),
        observation(49, 55, "read_coverage", "coverage_drop"),
    )

    findings = candidate_biological_findings(candidate)

    assert len(candidate.analysis.convergences) == 1
    assert findings[-1].title == "Local evidence convergence"
    assert findings[-1].sources == ("protein_alignment", "read_coverage")
