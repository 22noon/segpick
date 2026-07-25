from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from segpick.analysis.blastx_consistency import (
    attach_blastx_consistency,
    calculate_blastx_consistency,
)
from segpick.models import (
    BlastXHit,
    CandidateContig,
    ContigMetadata,
    Gene,
    ORFHit,
    ORFMetrics,
    Sample,
)


def make_hit(**overrides) -> BlastXHit:
    values = {
        "query_id": "candidate",
        "subject_id": "protein",
        "subject_title": "protein",
        "percent_identity": 100.0,
        "alignment_length": 26,
        "evalue": 1e-20,
        "bitscore": 100.0,
        "query_start": 4,
        "query_end": 84,
        "subject_start": 1,
        "subject_end": 26,
        "query_length": 90,
        "subject_length": 26,
        "query_frame": 1,
        "subject_protein": "M" + "A" * 25,
    }
    values.update(overrides)
    return BlastXHit(**values)


def make_orf(**overrides) -> ORFHit:
    values = {
        "strand": "+",
        "frame": 0,
        "start": 3,
        "end": 84,
        "nucleotide_length": 81,
        "protein": "M" + "A" * 25,
        "has_start_codon": True,
        "has_stop_codon": True,
    }
    values.update(overrides)
    return ORFHit(**values)


def test_consistent_orf_and_blastx_hit() -> None:
    result = calculate_blastx_consistency(make_orf(), make_hit())

    assert result.strand_agrees is True
    assert result.frame_agrees is True
    assert result.coordinates_agree is True
    assert result.amino_acid_identity == 1.0
    assert result.subject_coverage == 1.0
    assert result.consistent is True
    assert result.warnings == ()


def test_reports_frame_strand_and_coordinate_disagreement() -> None:
    result = calculate_blastx_consistency(
        make_orf(strand="-", frame=1, start=40, end=90),
        make_hit(),
    )

    assert result.strand_agrees is False
    assert result.frame_agrees is False
    assert result.coordinates_agree is False
    assert "strand_disagreement" in result.warnings
    assert "frame_disagreement" in result.warnings
    assert "selected_orf_does_not_cover_blastx_interval" in result.warnings


def test_attachment_uses_selected_orf() -> None:
    sample = Sample(name="sample")
    gene = Gene(name="VP1", segment="1")
    candidate = CandidateContig(
        id="candidate",
        record=SeqRecord(Seq("ATG" + "GCT" * 25 + "TAA"), id="candidate"),
        metadata=ContigMetadata(
            segment="1",
            score=1.0,
            confidence=1.0,
            cluster="cluster",
            sseqid="reference",
        ),
    )
    selected = make_orf()
    candidate.analysis.orf = ORFMetrics(
        best_orf=selected,
        longest_orf=selected,
        orf_count=1,
        complete_orf_count=1,
    )
    candidate.analysis.blastx = make_hit()
    gene.add_candidate(candidate)
    sample.add_gene(gene)

    attach_blastx_consistency(sample)

    assert candidate.analysis.blastx_consistency is not None
    assert candidate.analysis.blastx_consistency.consistent is True
