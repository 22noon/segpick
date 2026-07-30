from __future__ import annotations

from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from segpick.analysis.orf_selection import (
    attach_blastx_guided_orf_metrics,
    calculate_blastx_guided_orf_metrics,
)
from segpick.models import (
    BlastXHit,
    CandidateContig,
    ContigMetadata,
    Gene,
    Sample,
)


def _hit(subject_protein: str, *, frame: int = 1) -> BlastXHit:
    return BlastXHit(
        query_id="contig_a",
        subject_id="protein_a",
        subject_title="expected protein",
        percent_identity=100.0,
        alignment_length=len(subject_protein),
        evalue=1e-50,
        bitscore=200.0,
        query_start=1,
        query_end=len(subject_protein) * 3,
        subject_start=1,
        subject_end=len(subject_protein),
        query_length=300,
        subject_length=len(subject_protein),
        query_frame=frame,
        subject_protein=subject_protein,
    )


def test_blastx_protein_can_select_shorter_matching_orf() -> None:
    expected_coding = "ATG" + ("GCT" * 24) + "TAA"
    longer_unrelated = "ATG" + ("GGT" * 40) + "TAA"
    sequence = expected_coding + "CCC" + longer_unrelated
    expected_protein = str(Seq(expected_coding[:-3]).translate())

    metrics = calculate_blastx_guided_orf_metrics(
        sequence,
        _hit(expected_protein),
        minimum_protein_length=10,
    )

    assert metrics.best_orf is not None
    assert metrics.longest_orf is not None
    assert metrics.best_orf.protein == expected_protein
    assert metrics.best_orf.protein_length < metrics.longest_orf.protein_length
    assert metrics.selection_method == "blastx_protein_match"
    assert metrics.selected_matches_longest is False


def test_guided_selection_retains_longest_when_it_is_best_match() -> None:
    coding = "ATG" + ("GCT" * 30) + "TAA"
    expected_protein = str(Seq(coding[:-3]).translate())

    metrics = calculate_blastx_guided_orf_metrics(
        coding,
        _hit(expected_protein),
        minimum_protein_length=10,
        include_partial=False,
    )

    assert metrics.best_orf is not None
    assert metrics.best_orf.protein == expected_protein
    assert metrics.selected_matches_longest is True


def test_attachment_leaves_fallback_selection_without_resolved_protein() -> None:
    sequence = Seq("ATG" + ("GCT" * 25) + "TAA")
    candidate = CandidateContig(
        id="contig_a",
        record=SeqRecord(sequence, id="contig_a"),
        metadata=ContigMetadata(
            segment="2", score=1.0, confidence=1.0, cluster="cluster_a"
        ),
    )
    candidate.analysis.blastx = _hit("M" + ("A" * 25))
    candidate.analysis.blastx.subject_protein = None
    sample = Sample(
        name="sample",
        genes={"VP2": Gene(name="VP2", segment="2", candidates=[candidate])},
    )

    attach_blastx_guided_orf_metrics(sample)

    assert candidate.analysis.orf is None


def test_small_complete_orf_is_not_major_competitor() -> None:
    selected_coding = "ATG" + ("GCT" * 30) + "TAA"
    small_coding = "ATG" + ("GGT" * 8) + "TAA"
    sequence = selected_coding + "CCC" + small_coding
    expected_protein = str(Seq(selected_coding[:-3]).translate())

    metrics = calculate_blastx_guided_orf_metrics(
        sequence,
        _hit(expected_protein),
        minimum_protein_length=5,
        include_partial=False,
    )

    assert metrics.other_complete_orf_count == 1
    assert metrics.major_competing_orf_count == 0
    assert metrics.largest_competing_orf_length == 9


def test_similarly_sized_complete_orf_is_major_competitor() -> None:
    selected_coding = "ATG" + ("GCT" * 30) + "TAA"
    competing_coding = "ATG" + ("GGT" * 24) + "TAA"
    sequence = selected_coding + "CCC" + competing_coding
    expected_protein = str(Seq(selected_coding[:-3]).translate())

    metrics = calculate_blastx_guided_orf_metrics(
        sequence,
        _hit(expected_protein),
        minimum_protein_length=5,
        include_partial=False,
    )

    assert metrics.other_complete_orf_count == 1
    assert metrics.major_competing_orf_count == 1
    assert metrics.largest_competing_orf_length == 25
