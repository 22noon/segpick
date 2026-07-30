from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from segpick.analysis.observations import coverage_observations
from segpick.models import (
    CandidateContig,
    ContigMetadata,
    ORFAlignmentMetrics,
    ORFHit,
    ORFMetrics,
)


def _candidate(strand: str = "+") -> CandidateContig:
    candidate = CandidateContig(
        id="candidate",
        record=SeqRecord(Seq("A" * 60), id="candidate"),
        metadata=ContigMetadata(
            segment="1",
            score=1.0,
            confidence=1.0,
            cluster="cluster",
        ),
    )
    candidate.analysis.orf = ORFMetrics(
        best_orf=ORFHit(
            strand=strand,
            frame=0,
            start=0,
            end=60,
            nucleotide_length=60,
            protein="A" * 20,
            has_start_codon=True,
            has_stop_codon=True,
        ),
        orf_count=1,
        complete_orf_count=1,
    )
    candidate.analysis.orf_alignment = ORFAlignmentMetrics(
        reference_id="reference",
        candidate_protein_length=20,
        reference_protein_length=20,
        aligned_residues=20,
        identical_residues=20,
        amino_acid_identity=1.0,
        candidate_coverage=1.0,
        reference_coverage=1.0,
        length_ratio=1.0,
        n_terminal_missing=0,
        c_terminal_missing=0,
        internal_gap_residues=0,
        aligned_candidate="A" * 20,
        aligned_reference="A" * 20,
        match_line="|" * 20,
    )
    candidate.analysis.depth_profile = {position: 100 for position in range(1, 61)}
    return candidate


def test_projects_sustained_forward_coverage_drop() -> None:
    candidate = _candidate("+")
    for position in range(16, 25):
        candidate.analysis.depth_profile[position] = 0

    observations = coverage_observations(candidate)

    assert len(observations) == 1
    observation = observations[0]
    assert observation.observation_type == "coverage_drop"
    assert (observation.start, observation.end) == (6, 8)
    assert observation.attributes["nucleotide_length"] == 9


def test_projects_sustained_reverse_coverage_drop() -> None:
    candidate = _candidate("-")
    for position in range(16, 25):
        candidate.analysis.depth_profile[position] = 0

    observations = coverage_observations(candidate)

    assert len(observations) == 1
    observation = observations[0]
    assert (observation.start, observation.end) == (13, 15)


def test_ignores_short_coverage_dip() -> None:
    candidate = _candidate()
    for position in range(16, 21):
        candidate.analysis.depth_profile[position] = 0

    assert coverage_observations(candidate) == ()
