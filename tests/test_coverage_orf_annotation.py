from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from segpick.models import (
    CandidateContig,
    ContigMetadata,
    Gene,
    ORFHit,
    ORFMetrics,
    Sample,
)
from segpick.read_support import write_sample_coverage_plots


def test_coverage_plot_receives_selected_orf_annotation(tmp_path, monkeypatch) -> None:
    candidate = CandidateContig(
        id="contig_a",
        record=SeqRecord(Seq("A" * 12), id="contig_a"),
        metadata=ContigMetadata(
            segment="2",
            score=1.0,
            confidence=1.0,
            cluster="A",
            z=0.0,
        ),
    )
    selected = ORFHit(
        strand="-",
        frame=-1,
        start=3,
        end=11,
        nucleotide_length=9,
        protein="MK",
        has_start_codon=True,
        has_stop_codon=True,
    )
    candidate.analysis.orf = ORFMetrics(
        best_orf=selected,
        longest_orf=selected,
        orf_count=1,
        complete_orf_count=1,
    )
    gene = Gene(name="VP2", segment="2", candidates=[candidate])
    sample = Sample(name="sample", genes={"VP2": gene})
    depth_dir = tmp_path / "depth"
    depth_dir.mkdir()
    (depth_dir / "contig_a.depth.txt").write_text(
        "".join(f"contig_a\t{position}\t10\n" for position in range(1, 13))
    )

    captured = {}

    def fake_write_coverage_plot(*args, **kwargs):
        captured.update(kwargs)
        output = args[2]
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"plot")
        return output

    monkeypatch.setattr(
        "segpick.read_support.plotting.write_coverage_plot",
        fake_write_coverage_plot,
    )

    write_sample_coverage_plots(sample, depth_dir, tmp_path / "plots")

    assert captured["orf_start"] == 3
    assert captured["orf_end"] == 11
    assert captured["orf_strand"] == "-"
    assert captured["orf_label"] == "Selected ORF (-)"
