import pytest

from segpick.models import BlastXConsistency
from segpick.scoring import Evidence, ScoringWeights, score_evidence
from segpick.scoring.builder import blastx_consistency_evidence


class _Analysis:
    def __init__(self, consistency):
        self.blastx_consistency = consistency


class _Candidate:
    def __init__(self, consistency):
        self.analysis = _Analysis(consistency)


def _consistency(**overrides):
    values = {
        "strand_agrees": True,
        "frame_agrees": True,
        "blastx_interval_coverage": 1.0,
        "orf_interval_coverage": 1.0,
        "amino_acid_identity": 1.0,
        "subject_coverage": 1.0,
        "length_agreement": 1.0,
    }
    values.update(overrides)
    return BlastXConsistency(**values)


def test_perfect_blastx_consistency_scores_one():
    assert blastx_consistency_evidence(_Candidate(_consistency())) == pytest.approx(1.0)


def test_frame_and_strand_disagreement_are_strong_penalties():
    score = blastx_consistency_evidence(
        _Candidate(_consistency(strand_agrees=False, frame_agrees=False))
    )

    assert score == pytest.approx(0.60)


def test_missing_blastx_consistency_is_unavailable():
    assert blastx_consistency_evidence(_Candidate(None)) is None


def test_default_blastx_consistency_weight_is_twenty_percent():
    weights = ScoringWeights()

    assert weights.blastx_consistency == pytest.approx(0.20)
    assert weights.total == pytest.approx(1.0)


def test_blastx_consistency_contributes_to_score():
    evidence = Evidence(
        protein_confidence=1.0,
        length_plausibility=1.0,
        containment=1.0,
        identity=1.0,
        fragmentation=1.0,
        read_support=1.0,
        orf_quality=1.0,
        blastx_consistency=0.0,
    )

    scored = score_evidence(evidence, ScoringWeights())

    assert scored.effective_weights["blastx_consistency"] == pytest.approx(0.20)
    assert scored.score == pytest.approx(0.80)
