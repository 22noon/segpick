from segpick.models import BlastNHSP, ReferenceDotplot
from segpick.visualization import make_multi_candidate_reference_dotplot


def _result(candidate_id: str, query_length: int) -> ReferenceDotplot:
    hsp = BlastNHSP(
        query_id=candidate_id,
        subject_id="REF1",
        query_length=query_length,
        subject_length=1000,
        percent_identity=95.0,
        alignment_length=800,
        mismatches=20,
        gap_opens=1,
        query_start=10,
        query_end=min(810, query_length),
        subject_start=20,
        subject_end=820,
        evalue=1e-50,
        bitscore=900.0,
    )
    return ReferenceDotplot(
        candidate_id=candidate_id,
        reference_id="REF1",
        query_length=query_length,
        reference_length=1000,
        hsps=(hsp,),
        query_coverage=0.8,
        reference_coverage=0.8,
        identity_min=95.0,
        identity_max=95.0,
        output_path=f"{candidate_id}.tsv",
        reused_existing=True,
    )


def test_multi_candidate_reference_dotplot_stacks_candidates() -> None:
    fig = make_multi_candidate_reference_dotplot(
        [_result("contig_a", 900), _result("contig_b", 850)]
    )

    assert len(fig.data) == 2
    assert {trace.name for trace in fig.data} == {"contig_a", "contig_b"}
    assert "shared reference REF1" in fig.layout.title.text
    assert fig.layout.height >= 500


def test_multi_candidate_reference_dotplot_rejects_mixed_references() -> None:
    first = _result("contig_a", 900)
    second = ReferenceDotplot(
        candidate_id="contig_b",
        reference_id="REF2",
        query_length=850,
        reference_length=1000,
        hsps=first.hsps,
        query_coverage=0.8,
        reference_coverage=0.8,
        identity_min=95.0,
        identity_max=95.0,
        output_path="contig_b.tsv",
        reused_existing=True,
    )

    try:
        make_multi_candidate_reference_dotplot([first, second])
    except ValueError as error:
        assert "same reference" in str(error)
    else:
        raise AssertionError("Mixed references should be rejected")
