import pytest

from segpick.scoring import Evidence, ScoringWeights, score_evidence


def test_score_uses_all_available_channels() -> None:
    evidence = Evidence(
        protein_confidence=1.0,
        length_plausibility=0.5,
        containment=0.8,
        identity=0.9,
        fragmentation=1.0,
    )

    result = score_evidence(evidence, ScoringWeights())

    expected = 1.0 * 0.30 + 0.5 * 0.15 + 0.8 * 0.25 + 0.9 * 0.15 + 1.0 * 0.15

    assert result.score == pytest.approx(expected)
    assert sum(result.effective_weights.values()) == pytest.approx(1.0)


def test_missing_channel_weight_is_redistributed() -> None:
    evidence = Evidence(
        protein_confidence=1.0,
        length_plausibility=None,
        containment=0.8,
        identity=0.9,
        fragmentation=1.0,
    )

    result = score_evidence(evidence, ScoringWeights())

    assert "length_plausibility" not in result.effective_weights
    assert sum(result.effective_weights.values()) == pytest.approx(1.0)

    assert result.effective_weights["protein_confidence"] == pytest.approx(0.30 / 0.85)
    assert result.effective_weights["containment"] == pytest.approx(0.25 / 0.85)


def test_missing_evidence_does_not_count_as_zero() -> None:
    missing = Evidence(
        protein_confidence=1.0,
        length_plausibility=None,
        containment=1.0,
        identity=1.0,
        fragmentation=1.0,
    )

    zero = Evidence(
        protein_confidence=1.0,
        length_plausibility=0.0,
        containment=1.0,
        identity=1.0,
        fragmentation=1.0,
    )

    weights = ScoringWeights()

    assert score_evidence(missing, weights).score == pytest.approx(1.0)
    assert score_evidence(zero, weights).score == pytest.approx(0.85)


def test_candidate_can_be_scored_with_one_available_channel() -> None:
    evidence = Evidence(
        protein_confidence=0.7,
        length_plausibility=None,
        containment=None,
        identity=None,
        fragmentation=None,
    )

    result = score_evidence(evidence, ScoringWeights())

    assert result.score == pytest.approx(0.7)
    assert result.effective_weights == {"protein_confidence": 1.0}


def test_scoring_fails_when_no_evidence_is_available() -> None:
    evidence = Evidence(
        protein_confidence=None,
        length_plausibility=None,
        containment=None,
        identity=None,
        fragmentation=None,
    )

    with pytest.raises(ValueError):
        score_evidence(evidence, ScoringWeights())
