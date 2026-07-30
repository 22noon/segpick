from pathlib import Path

from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from segpick.analysis.reference_dotplot import (
    parse_megablast_tsv,
    reference_dotplot_filename,
    run_candidate_megablast,
)
from segpick.models import CandidateContig, ContigMetadata, ReferenceSequence


def _candidate() -> CandidateContig:
    return CandidateContig(
        id="CONTIG/1",
        record=SeqRecord(Seq("A" * 100), id="CONTIG/1"),
        metadata=ContigMetadata(
            segment="1",
            score=1.0,
            confidence=1.0,
            cluster="c1",
            sseqid="REF|A",
        ),
    )


def _reference() -> ReferenceSequence:
    return ReferenceSequence(
        accession="REF|A",
        record=SeqRecord(Seq("A" * 120), id="REF|A"),
    )


def test_reference_dotplot_filename_contains_candidate_and_reference():
    assert reference_dotplot_filename("CONTIG/1", "REF|A") == (
        "CONTIG_1__vs__REF_A.megablast.tsv"
    )


def test_parse_megablast_tsv_calculates_summary(tmp_path: Path):
    path = tmp_path / "hits.tsv"
    path.write_text(
        "q\ts\t100\t120\t95.0\t40\t2\t0\t1\t40\t5\t44\t1e-20\t80\n"
        "q\ts\t100\t120\t90.0\t31\t3\t0\t70\t100\t90\t60\t1e-10\t55\n"
    )
    result = parse_megablast_tsv(
        path,
        candidate_id="q",
        reference_id="s",
        query_length=100,
        reference_length=120,
        reused_existing=True,
    )
    assert result.block_count == 2
    assert result.query_coverage == 0.71
    assert result.reference_coverage == 71 / 120
    assert result.identity_min == 90.0
    assert result.identity_max == 95.0
    assert result.orientation == "mixed"
    assert result.reused_existing is True


def test_existing_non_empty_pair_file_is_reused_without_blastn(tmp_path: Path):
    candidate = _candidate()
    reference = _reference()
    output = tmp_path / reference_dotplot_filename(candidate.id, reference.accession)
    output.write_text(
        "CONTIG/1\tREF|A\t100\t120\t99\t100\t1\t0\t1\t100\t1\t100\t1e-50\t200\n"
    )
    result = run_candidate_megablast(candidate, reference, tmp_path)
    assert result.reused_existing is True
    assert result.output_path == str(output)
    assert result.block_count == 1


def test_repeated_reference_pairs_preserve_distinct_query_blocks(tmp_path: Path):
    path = tmp_path / "repeated.tsv"
    path.write_text(
        "q\ts\t3000\t3000\t95.0\t1000\t0\t0\t1\t1000\t1\t1000\t1e-20\t100\n"
        "q\ts\t3000\t3000\t94.0\t1000\t0\t0\t1501\t2500\t501\t1500\t1e-18\t90\n"
    )
    result = parse_megablast_tsv(
        path,
        candidate_id="q",
        reference_id="s",
        query_length=3000,
        reference_length=3000,
        reused_existing=True,
    )

    pairs = result.repeated_reference_pairs()
    assert len(pairs) == 1
    assert pairs[0]["left_query_interval"] == (1, 1000)
    assert pairs[0]["right_query_interval"] == (1501, 2500)
    assert pairs[0]["reference_interval"] == (501, 1000)
    assert pairs[0]["overlap_bases"] == 500
    assert result.repeated_reference_hsp_indices == (0, 1)


def test_reference_dotplot_highlights_repeated_mapping_blocks(tmp_path: Path):
    from segpick.visualization.reference_dotplot import make_reference_dotplot

    path = tmp_path / "repeated.tsv"
    path.write_text(
        "q\ts\t3000\t3000\t95.0\t1000\t0\t0\t1\t1000\t1\t1000\t1e-20\t100\n"
        "q\ts\t3000\t3000\t94.0\t1000\t0\t0\t1501\t2500\t501\t1500\t1e-18\t90\n"
    )
    result = parse_megablast_tsv(
        path,
        candidate_id="q",
        reference_id="s",
        query_length=3000,
        reference_length=3000,
        reused_existing=True,
    )

    figure = make_reference_dotplot(result)
    diagnostic_traces = [
        trace for trace in figure.data
        if trace.line.color == "#c2410c"
    ]
    assert len(diagnostic_traces) == 4  # two dot-plot traces and two mapping-track traces
    assert all(trace.line.dash == "dash" for trace in diagnostic_traces)
    assert len(figure.layout.shapes) == 1
    assert figure.layout.shapes[0].y0 == 501
    assert figure.layout.shapes[0].y1 == 1000
