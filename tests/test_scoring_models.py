import pytest

from segpick.scoring import Evidence, ScoringWeights


def test_evidence_accepts_normalised_values() -> None:
    evidence = Evidence(
        protein_confidence=0.9,
        length_plausibility=0.8,
        containment=0.7,
        identity=0.95,
        fragmentation=1.0,
    )

    assert evidence.identity == 0.95


def test_evidence_rejects_values_outside_zero_one() -> None:
    with pytest.raises(ValueError):
        Evidence(
            protein_confidence=1.2,
            length_plausibility=0.8,
            containment=0.7,
            identity=0.95,
            fragmentation=1.0,
        )


def test_weights_normalise_to_one() -> None:
    weights = ScoringWeights(
        protein_confidence=3,
        length_plausibility=1,
        containment=2,
        identity=2,
        fragmentation=2,
        read_support=2,
    ).normalised()

    assert weights.total == pytest.approx(1.0)
    assert weights.protein_confidence == pytest.approx(0.25)
    assert weights.read_support == pytest.approx(2 / 12)

def test_weights_allow_partial_overrides() -> None:
    weights = ScoringWeights().with_overrides(
        protein_confidence=0.5,
        containment=None,
    )

    assert weights.protein_confidence == 0.5
    assert weights.containment == 0.20
    assert weights.read_support == 0.20


def test_weights_reject_all_zero() -> None:
    with pytest.raises(ValueError):
        ScoringWeights(
            protein_confidence=0,
            length_plausibility=0,
            containment=0,
            identity=0,
            fragmentation=0,
            read_support=0,
        )

def test_evidence_accepts_missing_read_support() -> None:
    evidence = Evidence(
        protein_confidence=1.0,
        length_plausibility=1.0,
        containment=1.0,
        identity=1.0,
        fragmentation=1.0,
        read_support=None,
    )

    assert evidence.read_support is None

def test_evidence_rejects_invalid_read_support() -> None:
    with pytest.raises(ValueError):
        Evidence(
            protein_confidence=1.0,
            length_plausibility=1.0,
            containment=1.0,
            identity=1.0,
            fragmentation=1.0,
            read_support=1.5,
        )
