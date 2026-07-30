from __future__ import annotations

import json

from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from segpick.analysis.blastx import attach_blastx_hits, read_diamond_blastx
from segpick.models import CandidateContig, ContigMetadata, Gene, Sample
from segpick.reporting import write_gene_json_reports


def _row(query: str, subject: str, bitscore: float, frame: int = 1) -> str:
    return "\t".join(
        [
            query,
            subject,
            "Bluetongue VP2",
            "98.5",
            "100",
            "1e-30",
            str(bitscore),
            "4",
            "303",
            "2",
            "101",
            "600",
            "120",
            str(frame),
        ]
    )


def _sample() -> Sample:
    candidate = CandidateContig(
        id="contig_a",
        record=SeqRecord(Seq("ATG" * 200), id="contig_a"),
        metadata=ContigMetadata(
            segment="2", score=1.0, confidence=1.0, cluster="cluster_a"
        ),
    )
    gene = Gene(name="VP2", segment="2", candidates=[candidate])
    return Sample(name="sample", genes={"VP2": gene})


def test_read_diamond_blastx_sorts_best_hit_first(tmp_path) -> None:
    path = tmp_path / "diamond.tsv"
    path.write_text(_row("contig_a", "protein_low", 50) + "\n" + _row("contig_a", "protein_best", 80, -2) + "\n")

    hits = read_diamond_blastx(path)["contig_a"]

    assert hits[0].subject_id == "protein_best"
    assert hits[0].strand == "-"
    assert hits[0].query_frame == -2
    assert hits[0].query_coverage == 0.5


def test_attach_blastx_hit_and_subject_protein(tmp_path) -> None:
    blastx = tmp_path / "diamond.tsv"
    proteins = tmp_path / "proteins.fa"
    blastx.write_text(_row("contig_a", "protein_a", 80) + "\n")
    proteins.write_text(">protein_a description\nMPEPTIDE\n")
    sample = _sample()

    summary = attach_blastx_hits(sample, blastx, proteins)
    hit = sample.genes["VP2"].candidates[0].analysis.blastx

    assert summary.hits_attached == 1
    assert summary.subjects_resolved == 1
    assert hit is not None
    assert hit.subject_protein == "MPEPTIDE"
    assert hit.subject_coverage == 100 / 120


def test_blastx_metrics_are_written_to_json(tmp_path) -> None:
    blastx = tmp_path / "diamond.tsv"
    proteins = tmp_path / "proteins.fa"
    blastx.write_text(_row("contig_a", "protein_a", 80) + "\n")
    proteins.write_text(">protein_a\nMPEPTIDE\n")
    sample = _sample()
    attach_blastx_hits(sample, blastx, proteins)

    write_gene_json_reports(sample, tmp_path / "reports")
    payload = json.loads((tmp_path / "reports" / "VP2.json").read_text())

    assert payload["candidates"][0]["blastx"]["subject_id"] == "protein_a"
    assert payload["candidates"][0]["blastx"]["subject_protein_found"] is True
    assert "subject_protein" not in payload["candidates"][0]["blastx"]
