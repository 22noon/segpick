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


def test_agreement_distinguishes_unique_shared_and_conflicting_channels():
    from segpick.scoring import CandidateRecommendation, Evidence, ScoringWeights, assess_evidence_agreement, score_evidence

    def candidate(candidate_id, protein, length, structure):
        evidence = Evidence(
            protein_confidence=protein,
            length_plausibility=length,
            structural_integrity=structure,
        )
        return CandidateRecommendation(
            candidate_id=candidate_id,
            length=100,
            protein_confidence_raw=protein,
            evidence=evidence,
            scored=score_evidence(evidence, ScoringWeights()),
        )

    candidates = (
        candidate("a", 0.9, 0.8, 0.5),
        candidate("b", 0.7, 0.8, 0.9),
    )
    agreement = assess_evidence_agreement(candidates, "a")
    statuses = {item.channel: item.status for item in agreement.channel_assessments}

    assert statuses["protein_confidence"] == "supports"
    assert statuses["length_plausibility"] == "shared"
    assert statuses["structural_integrity"] == "conflicts"
    assert agreement.unique_supporting_channels == ("protein_confidence",)
    assert agreement.shared_supporting_channels == ("length_plausibility",)
