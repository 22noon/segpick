from segpick.scoring import (
    CandidateRecommendation,
    Evidence,
    ScoredEvidence,
    assess_evidence_agreement,
)


def _candidate(candidate_id: str, **values) -> CandidateRecommendation:
    evidence = Evidence(
        protein_confidence=values.get("protein_confidence"),
        length_plausibility=values.get("length_plausibility"),
        containment=values.get("containment"),
        identity=values.get("identity"),
        fragmentation=values.get("fragmentation"),
        coverage_sufficiency=values.get("read_support"),
        coverage_integrity=values.get("read_support"),
        orf_quality=values.get("orf_quality"),
        blastx_consistency=values.get("blastx_consistency"),
    )
    return CandidateRecommendation(
        candidate_id=candidate_id,
        length=100,
        protein_confidence_raw=1.0,
        evidence=evidence,
        scored=ScoredEvidence(score=0.5, contributions={}, effective_weights={}),
    )


def test_agreement_is_high_when_all_channels_support_recommendation():
    candidates = (
        _candidate("a", protein_confidence=1.0, orf_quality=1.0, blastx_consistency=1.0),
        _candidate("b", protein_confidence=0.5, orf_quality=0.5, blastx_consistency=0.5),
    )

    agreement = assess_evidence_agreement(candidates, "a")

    assert agreement.confidence == "high"
    assert agreement.disagreeing_channels == ()


def test_blastx_conflict_lowers_confidence():
    candidates = (
        _candidate("a", protein_confidence=1.0, orf_quality=0.8, blastx_consistency=0.4),
        _candidate("b", protein_confidence=0.5, orf_quality=0.7, blastx_consistency=1.0),
    )

    agreement = assess_evidence_agreement(candidates, "a")

    assert agreement.confidence == "low"
    assert agreement.strong_conflicts == ("blastx_consistency",)
    assert agreement.channel_winners["blastx_consistency"] == ("b",)
