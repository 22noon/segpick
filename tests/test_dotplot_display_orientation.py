from segpick.models import BlastNHSP, ContigDotplot, ReferenceDotplot
from segpick.visualization import make_contig_dotplot, make_reference_dotplot


def hsp(*, strand: str, length: int = 80) -> BlastNHSP:
    subject_start, subject_end = ((10, 89) if strand == "+" else (89, 10))
    return BlastNHSP(
        query_id="contig",
        subject_id="ref",
        query_length=100,
        subject_length=120,
        percent_identity=95.0,
        alignment_length=length,
        mismatches=2,
        gap_opens=0,
        query_start=1,
        query_end=80,
        subject_start=subject_start,
        subject_end=subject_end,
        evalue=1e-20,
        bitscore=100.0,
    )


def reference_result(hsps: tuple[BlastNHSP, ...]) -> ReferenceDotplot:
    return ReferenceDotplot(
        candidate_id="contig",
        reference_id="ref",
        query_length=100,
        reference_length=120,
        hsps=hsps,
        query_coverage=0.8,
        reference_coverage=0.7,
        identity_min=95.0,
        identity_max=95.0,
        output_path="hits.tsv",
        reused_existing=True,
    )


def test_reverse_dominant_reference_alignment_is_reoriented_for_display() -> None:
    result = reference_result((hsp(strand="-", length=90), hsp(strand="+", length=10)))
    assert result.display_orientation == "reverse"
    assert result.display_reverse_complemented is True
    assert result.dominant_orientation_fraction == 0.9

    fig = make_reference_dotplot(result)
    assert list(fig.data[0].x) == [100, 21]
    assert "reverse-complemented for display" in fig.layout.title.text


def test_mixed_reference_alignment_is_not_reoriented() -> None:
    result = reference_result((hsp(strand="-", length=55), hsp(strand="+", length=45)))
    assert result.display_orientation == "uncertain"
    assert result.display_reverse_complemented is False

    fig = make_reference_dotplot(result)
    assert list(fig.data[0].x) == [1, 80]


def test_contig_plot_can_reorient_both_axes_for_display() -> None:
    result = ContigDotplot(
        query_id="A",
        target_id="B",
        query_length=100,
        target_length=120,
        hsps=(hsp(strand="+"),),
        query_coverage=0.8,
        target_coverage=0.7,
        identity_min=95.0,
        identity_max=95.0,
        output_path="pair.tsv",
        reused_existing=True,
    )
    fig = make_contig_dotplot(result, query_reverse=True, target_reverse=True)
    assert list(fig.data[0].x) == [100, 21]
    assert list(fig.data[0].y) == [111, 32]
    assert "A RC for display" in fig.layout.title.text
    assert "B RC for display" in fig.layout.title.text
