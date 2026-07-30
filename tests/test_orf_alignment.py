from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from segpick.analysis.orf import attach_orf_metrics
from segpick.analysis.orf_alignment import (
    align_orf_proteins,
    attach_orf_alignment_metrics,
)
from segpick.models import (
    CandidateContig,
    ContigMetadata,
    Gene,
    ReferenceSequence,
    Sample,
)


def test_align_orf_proteins_reports_identity_and_terminal_loss():
    metrics = align_orf_proteins(
        "MABCDE",
        "XXMABCDEYY",
        reference_id="reference",
    )

    assert metrics.amino_acid_identity == 1.0
    assert metrics.candidate_coverage == 1.0
    assert metrics.reference_coverage == 6 / 10
    assert metrics.n_terminal_missing == 2
    assert metrics.c_terminal_missing == 2
    assert metrics.internal_gap_residues == 0


def test_attach_orf_alignment_uses_candidate_blast_reference():
    sample = Sample(name="sample")
    gene = Gene(name="VP2", segment="2")
    metadata = ContigMetadata(
        segment="2",
        score=1.0,
        confidence=1.0,
        cluster="cluster",
        sseqid="reference_2",
    )
    gene.add_candidate(
        CandidateContig(
            id="candidate",
            record=SeqRecord(Seq("ATG" + "GCT" * 25 + "TAA"), id="candidate"),
            metadata=metadata,
        )
    )
    gene.add_reference(
        ReferenceSequence(
            accession="reference_2",
            record=SeqRecord(
                Seq("ATG" + "GCT" * 25 + "TAA"),
                id="reference_2",
            ),
        )
    )
    sample.add_gene(gene)

    attach_orf_metrics(sample)
    attach_orf_alignment_metrics(sample)

    metrics = gene.candidates[0].analysis.orf_alignment
    assert metrics is not None
    assert metrics.reference_id == "reference_2"
    assert metrics.amino_acid_identity == 1.0
    assert metrics.reference_coverage == 1.0


def test_attach_orf_alignment_is_missing_without_matching_reference():
    sample = Sample(name="sample")
    gene = Gene(name="VP2", segment="2")
    metadata = ContigMetadata(
        segment="2",
        score=1.0,
        confidence=1.0,
        cluster="cluster",
        sseqid="missing_reference",
    )
    gene.add_candidate(
        CandidateContig(
            id="candidate",
            record=SeqRecord(Seq("ATG" + "GCT" * 25 + "TAA"), id="candidate"),
            metadata=metadata,
        )
    )
    sample.add_gene(gene)

    attach_orf_metrics(sample)
    attach_orf_alignment_metrics(sample)

    assert gene.candidates[0].analysis.orf_alignment is None


def test_align_orf_proteins_classifies_internal_insertion():
    metrics = align_orf_proteins(
        "MABQQQCDE",
        "MABCDE",
        reference_id="reference",
    )

    assert metrics.internal_insertion_events == 1
    assert metrics.internal_insertion_residues == 3
    assert metrics.largest_internal_insertion == 3
    assert metrics.internal_deletion_events == 0


def test_align_orf_proteins_classifies_internal_deletion():
    metrics = align_orf_proteins(
        "MABCDE",
        "MABQQQCDE",
        reference_id="reference",
    )

    assert metrics.internal_deletion_events == 1
    assert metrics.internal_deletion_residues == 3
    assert metrics.largest_internal_deletion == 3
    assert metrics.internal_insertion_events == 0
