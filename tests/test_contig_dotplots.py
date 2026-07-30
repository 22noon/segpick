from pathlib import Path

from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from segpick.analysis.contig_dotplot import (
    canonical_contig_pair,
    contig_dotplot_filename,
    parse_contig_megablast_tsv,
    run_contig_pair_megablast,
)
from segpick.models import CandidateContig, ContigMetadata


def candidate(candidate_id: str, length: int = 100) -> CandidateContig:
    return CandidateContig(
        id=candidate_id,
        record=SeqRecord(Seq("A" * length), id=candidate_id),
        metadata=ContigMetadata(segment="1", score=1.0, confidence=1.0, cluster="c1"),
    )


def test_contig_dotplot_filename_is_pair_canonical_and_safe():
    assert canonical_contig_pair("B/2", "A|1") == ("A|1", "B/2")
    assert contig_dotplot_filename("B/2", "A|1") == "A_1__vs__B_2.megablast.tsv"
    assert contig_dotplot_filename("A|1", "B/2") == "A_1__vs__B_2.megablast.tsv"


def test_parse_contig_dotplot_summary(tmp_path: Path):
    path = tmp_path / "pair.tsv"
    path.write_text(
        "A\tB\t100\t120\t98\t40\t1\t0\t1\t40\t5\t44\t1e-20\t80\n"
        "A\tB\t100\t120\t94\t31\t2\t0\t70\t100\t90\t60\t1e-10\t55\n"
    )
    result = parse_contig_megablast_tsv(
        path,
        query_id="A",
        target_id="B",
        query_length=100,
        target_length=120,
        reused_existing=True,
    )
    assert result.block_count == 2
    assert result.query_coverage == 0.71
    assert result.target_coverage == 71 / 120
    assert result.orientation == "mixed"
    assert result.pair_key == "A__vs__B"


def test_existing_canonical_pair_file_is_reused(tmp_path: Path):
    first = candidate("B/2", 120)
    second = candidate("A|1", 100)
    output = tmp_path / contig_dotplot_filename(first.id, second.id)
    output.write_text(
        "A|1\tB/2\t100\t120\t99\t100\t1\t0\t1\t100\t1\t100\t1e-50\t200\n"
    )
    result = run_contig_pair_megablast(first, second, tmp_path)
    assert result.reused_existing is True
    assert result.query_id == "A|1"
    assert result.target_id == "B/2"
    assert result.output_path == str(output)
