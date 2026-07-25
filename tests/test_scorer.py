import pytest

from segpick.scoring import Evidence, ScoringWeights, score_evidence


def test_score_uses_all_available_channels() -> None:
    evidence = Evidence(
        protein_confidence=1.0,
        length_plausibility=0.5,
        containment=0.8,
        identity=0.9,
        fragmentation=1.0,
        read_support=0.75,
    )

    weights = ScoringWeights(
        protein_confidence=0.25,
        length_plausibility=0.10,
        containment=0.20,
        identity=0.15,
        fragmentation=0.10,
        read_support=0.20,
        orf_quality=0.0,
        blastx_consistency=0.0,
    )
    result = score_evidence(evidence, weights)

    expected = (
        1.0 * 0.25
        + 0.5 * 0.10
        + 0.8 * 0.20
        + 0.9 * 0.15
        + 1.0 * 0.10
        + 0.75 * 0.20
    )

    assert result.score == pytest.approx(expected)
    assert sum(result.effective_weights.values()) == pytest.approx(1.0)


def test_missing_channel_weight_is_redistributed() -> None:
    evidence = Evidence(
        protein_confidence=1.0,
        length_plausibility=None,
        containment=0.8,
        identity=0.9,
        fragmentation=1.0,
        read_support=0.75,
    )

    weights = ScoringWeights(
        protein_confidence=0.25,
        length_plausibility=0.10,
        containment=0.20,
        identity=0.15,
        fragmentation=0.10,
        read_support=0.20,
        orf_quality=0.0,
        blastx_consistency=0.0,
    )
    result = score_evidence(evidence, weights)

    assert "length_plausibility" not in result.effective_weights
    assert sum(result.effective_weights.values()) == pytest.approx(1.0)

    assert result.effective_weights["protein_confidence"] == pytest.approx( 0.25 / 0.90)
    assert result.effective_weights["containment"] == pytest.approx( 0.20 / 0.90)
    assert result.effective_weights["read_support"] == pytest.approx( 0.20 / 0.90)

def test_missing_evidence_does_not_count_as_zero() -> None:
    missing = Evidence(
        protein_confidence=1.0,
        length_plausibility=None,
        containment=1.0,
        identity=1.0,
        fragmentation=1.0,
        read_support=1.0,
    )

    zero = Evidence(
        protein_confidence=1.0,
        length_plausibility=0.0,
        containment=1.0,
        identity=1.0,
        fragmentation=1.0,
        read_support=1.0,
    )
    weights = ScoringWeights(
        protein_confidence=0.25,
        length_plausibility=0.10,
        containment=0.20,
        identity=0.15,
        fragmentation=0.10,
        read_support=0.20,
        orf_quality=0.0,
        blastx_consistency=0.0,
    )
    assert score_evidence(missing, weights).score == pytest.approx(1.0)
    assert score_evidence(zero, weights).score == pytest.approx(0.90)


def test_candidate_can_be_scored_with_one_available_channel() -> None:
    evidence = Evidence(
        protein_confidence=0.7,
        length_plausibility=None,
        containment=None,
        identity=None,
        fragmentation=None,
        read_support=None,
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
        read_support=None,
    )

    with pytest.raises(ValueError):
        score_evidence(evidence, ScoringWeights())

def test_missing_read_support_weight_is_redistributed() -> None:
    evidence = Evidence(
        protein_confidence=1.0,
        length_plausibility=1.0,
        containment=1.0,
        identity=1.0,
        fragmentation=1.0,
        read_support=None,
    )

    result = score_evidence(
        evidence,
        ScoringWeights(),
    )

    assert "read_support" not in result.effective_weights
    assert sum(result.effective_weights.values()) == pytest.approx(1.0)
    assert result.score == pytest.approx(1.0)
