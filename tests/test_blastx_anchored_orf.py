from __future__ import annotations

import json

from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from segpick.analysis.blastx_anchored_orf import (
    attach_blastx_anchored_orfs,
    calculate_blastx_anchored_orf,
)
from segpick.analysis.orf import calculate_orf_metrics
from segpick.models import BlastXHit, CandidateContig, ContigMetadata, Gene, Sample
from segpick.reporting import write_gene_json_reports, write_html_dashboard


def _hit(
    *,
    query_start: int,
    query_end: int,
    frame: int = 1,
    query_length: int,
) -> BlastXHit:
    return BlastXHit(
        query_id="contig_a",
        subject_id="protein_a",
        subject_title="expected protein",
        percent_identity=90.0,
        alignment_length=5,
        evalue=1e-20,
        bitscore=100.0,
        query_start=query_start,
        query_end=query_end,
        subject_start=2,
        subject_end=6,
        query_length=query_length,
        subject_length=10,
        query_frame=frame,
        subject_protein="MAAAAAAA",
    )


def test_forward_blastx_anchor_extends_to_start_and_stop() -> None:
    sequence = "CCC" + "ATG" + ("GCT" * 8) + "TAA" + "CCC"
    hit = _hit(query_start=10, query_end=24, query_length=len(sequence))
    selected = calculate_orf_metrics(sequence, minimum_protein_length=3).best_orf

    anchored = calculate_blastx_anchored_orf(sequence, hit, selected)

    assert anchored.start == 3
    assert anchored.end == 33
    assert anchored.has_start_codon is True
    assert anchored.has_stop_codon is True
    assert anchored.protein_sequence == "M" + ("A" * 8)
    assert anchored.nucleotide_sequence.endswith("TAA")
    assert anchored.matches_selected_orf is True


def test_reverse_blastx_anchor_returns_coding_strand_sequence() -> None:
    coding = "ATG" + ("GCT" * 6) + "TAA"
    sequence = "CCC" + str(Seq(coding).reverse_complement()) + "GGG"
    # Reverse-strand coordinates cover an internal part of the coding sequence.
    hit = _hit(
        query_start=len(sequence) - 8,
        query_end=7,
        frame=-1,
        query_length=len(sequence),
    )

    anchored = calculate_blastx_anchored_orf(sequence, hit)

    assert anchored.strand == "-"
    assert anchored.start == 3
    assert anchored.end == 27
    assert anchored.nucleotide_sequence == coding
    assert anchored.protein_sequence == "M" + ("A" * 6)
    assert anchored.complete is True


def test_anchor_retains_missing_stop_as_partial() -> None:
    sequence = "ATG" + ("GCT" * 8)
    hit = _hit(query_start=4, query_end=18, query_length=len(sequence))

    anchored = calculate_blastx_anchored_orf(sequence, hit)

    assert anchored.has_start_codon is True
    assert anchored.has_stop_codon is False
    assert anchored.reaches_contig_end is True
    assert anchored.complete is False


def test_attachment_json_and_dashboard_exports(tmp_path) -> None:
    sequence = Seq("ATG" + ("GCT" * 8) + "TAA")
    candidate = CandidateContig(
        id="contig_a",
        record=SeqRecord(sequence, id="contig_a"),
        metadata=ContigMetadata(
            segment="2", score=1.0, confidence=1.0, cluster="A"
        ),
    )
    candidate.analysis.blastx = _hit(
        query_start=4,
        query_end=18,
        query_length=len(sequence),
    )
    candidate.analysis.orf = calculate_orf_metrics(
        sequence,
        minimum_protein_length=3,
    )
    sample = Sample(
        name="sample",
        genes={"VP2": Gene(name="VP2", segment="2", candidates=[candidate])},
    )

    attach_blastx_anchored_orfs(sample)
    write_gene_json_reports(sample, tmp_path / "json")
    write_html_dashboard(sample, tmp_path / "dashboard")

    payload = json.loads((tmp_path / "json" / "VP2.json").read_text())
    anchored = payload["candidates"][0]["blastx_anchored_orf"]
    assert anchored["complete"] is True
    assert anchored["protein_sequence"] == "M" + ("A" * 8)

    html = (tmp_path / "dashboard" / "genes" / "VP2.html").read_text()
    assert "BLASTX-anchored coding sequence" in html
    assert "Copy anchored protein" in html
    assert "Copy anchored CDS" in html
    assert "blastx_anchored.faa" in html
    assert "blastx_anchored.fna" in html
