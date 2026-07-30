import pytest

from segpick.models import ORFQuality
from segpick.scoring import Evidence, ScoringWeights, score_evidence
from segpick.scoring.builder import orf_quality_evidence


class _Analysis:
    def __init__(self, orf_quality):
        self.orf_quality = orf_quality


class _Candidate:
    def __init__(self, orf_quality):
        self.analysis = _Analysis(orf_quality)


def _quality(score: float) -> ORFQuality:
    return ORFQuality(
        score=score,
        complete_orf=score,
        start_codon=score,
        stop_codon=score,
        protein_identity=None,
        reference_coverage=None,
        length_agreement=None,
        terminal_completeness=None,
        gap_integrity=None,
    )


def test_default_orf_and_blastx_weights_prioritise_structural_evidence():
    weights = ScoringWeights()

    assert weights.orf_quality == pytest.approx(0.12)
    assert weights.blastx_consistency == pytest.approx(0.20)
    assert weights.total == pytest.approx(1.0)


def test_orf_quality_evidence_uses_attached_score():
    assert orf_quality_evidence(_Candidate(_quality(0.73))) == pytest.approx(0.73)
    assert orf_quality_evidence(_Candidate(None)) is None


def test_missing_orf_quality_weight_is_redistributed():
    evidence = Evidence(
        protein_confidence=1.0,
        length_plausibility=1.0,
        structural_integrity=1.0,
        coverage_sufficiency=1.0,
        coverage_integrity=1.0,
        orf_quality=None,
        blastx_consistency=None,
    )

    scored = score_evidence(evidence, ScoringWeights())

    assert scored.score == pytest.approx(1.0)
    assert "orf_quality" not in scored.effective_weights
    assert sum(scored.effective_weights.values()) == pytest.approx(1.0)


def test_orf_quality_contributes_to_weighted_score():
    evidence = Evidence(
        protein_confidence=1.0,
        length_plausibility=1.0,
        structural_integrity=1.0,
        coverage_sufficiency=1.0,
        coverage_integrity=1.0,
        orf_quality=0.0,
        blastx_consistency=None,
    )

    scored = score_evidence(evidence, ScoringWeights())

    assert scored.effective_weights["orf_quality"] == pytest.approx(0.15)
    assert scored.score == pytest.approx(0.85)
