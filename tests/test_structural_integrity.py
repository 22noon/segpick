import pytest

from segpick.analysis.structural_integrity import structural_integrity_from_dotplot
from segpick.models import BlastNHSP, ReferenceDotplot


def _hsp(q1, q2, s1, s2, length):
    return BlastNHSP(
        query_id="contig", subject_id="ref", query_length=1000,
        subject_length=1000, percent_identity=80.0, alignment_length=length,
        mismatches=0, gap_opens=0, query_start=q1, query_end=q2,
        subject_start=s1, subject_end=s2, evalue=0.0, bitscore=100.0,
    )


def _dotplot(hsps):
    return ReferenceDotplot(
        candidate_id="contig", reference_id="ref", query_length=1000,
        reference_length=1000, hsps=tuple(hsps), query_coverage=0.9,
        reference_coverage=0.9, identity_min=80.0, identity_max=80.0,
        output_path="x.tsv", reused_existing=False,
    )


def test_continuous_collinear_alignment_has_high_integrity():
    metrics = structural_integrity_from_dotplot(_dotplot([_hsp(1, 900, 1, 900, 900)]))
    assert metrics.score == pytest.approx(0.9)
    assert metrics.status == "CONTINUOUS"
    assert metrics.orientation_consistency == 1.0


def test_internal_gap_reduces_integrity():
    metrics = structural_integrity_from_dotplot(_dotplot([
        _hsp(1, 300, 1, 300, 300),
        _hsp(601, 900, 601, 900, 300),
    ]))
    assert metrics.largest_candidate_gap == 300
    assert metrics.largest_reference_gap == 300
    assert metrics.score < 0.9


def test_mixed_orientation_is_penalised():
    metrics = structural_integrity_from_dotplot(_dotplot([
        _hsp(1, 450, 1, 450, 450),
        _hsp(551, 1000, 1000, 551, 450),
    ]))
    assert metrics.orientation_consistency == pytest.approx(0.5)
    assert metrics.score < 0.5


def test_identity_does_not_change_structural_score():
    high = _hsp(1, 900, 1, 900, 900)
    low = BlastNHSP(
        query_id=high.query_id, subject_id=high.subject_id,
        query_length=high.query_length, subject_length=high.subject_length,
        percent_identity=55.0, alignment_length=high.alignment_length,
        mismatches=high.mismatches, gap_opens=high.gap_opens,
        query_start=high.query_start, query_end=high.query_end,
        subject_start=high.subject_start, subject_end=high.subject_end,
        evalue=high.evalue, bitscore=high.bitscore,
    )
    assert structural_integrity_from_dotplot(_dotplot([high])).score == pytest.approx(
        structural_integrity_from_dotplot(_dotplot([low])).score
    )
