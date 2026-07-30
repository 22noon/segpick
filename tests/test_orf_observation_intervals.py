from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from segpick.analysis.observations import orf_structure_observations
from segpick.models import (
    CandidateContig,
    ContigMetadata,
    ORFAlignmentMetrics,
    ORFHit,
    ORFMetrics,
)


def _candidate(*, has_start: bool, has_stop: bool) -> CandidateContig:
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
            strand="+",
            frame=0,
            start=0,
            end=60,
            nucleotide_length=60,
            protein="A" * 20,
            has_start_codon=has_start,
            has_stop_codon=has_stop,
        ),
        orf_count=1,
        complete_orf_count=int(has_start and has_stop),
    )
    candidate.analysis.orf_alignment = ORFAlignmentMetrics(
        reference_id="reference",
        candidate_protein_length=20,
        reference_protein_length=25,
        aligned_residues=20,
        identical_residues=20,
        amino_acid_identity=1.0,
        candidate_coverage=1.0,
        reference_coverage=0.8,
        length_ratio=0.8,
        n_terminal_missing=2,
        c_terminal_missing=3,
        internal_gap_residues=0,
        aligned_candidate="--" + ("A" * 20) + "---",
        aligned_reference="A" * 25,
        match_line="  " + ("|" * 20) + "   ",
    )
    return candidate


def test_projects_partial_start_boundary() -> None:
    observations = orf_structure_observations(
        _candidate(has_start=False, has_stop=True)
    )

    assert len(observations) == 1
    observation = observations[0]
    assert observation.observation_type == "partial_orf_start_boundary"
    assert observation.source == "orf_structure"
    assert (observation.start, observation.end) == (3, 3)


def test_projects_partial_end_boundary() -> None:
    observations = orf_structure_observations(
        _candidate(has_start=True, has_stop=False)
    )

    assert len(observations) == 1
    observation = observations[0]
    assert observation.observation_type == "partial_orf_end_boundary"
    assert (observation.start, observation.end) == (23, 23)


def test_complete_orf_has_no_boundary_observations() -> None:
    observations = orf_structure_observations(
        _candidate(has_start=True, has_stop=True)
    )

    assert observations == ()
