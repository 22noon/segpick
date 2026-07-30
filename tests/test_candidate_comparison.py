import pytest

from segpick.scoring import (
    CandidateRecommendation,
    Evidence,
    ScoredEvidence,
    build_candidate_comparisons,
    compare_candidates,
)


def make_recommendation(
    candidate_id: str,
    score: float,
    contributions: dict[str, float],
    *,
    confidence: float = 100.0,
    length: int = 1000,
) -> CandidateRecommendation:
    return CandidateRecommendation(
        candidate_id=candidate_id,
        length=length,
        protein_confidence_raw=confidence,
        evidence=Evidence(
            protein_confidence=None,
            length_plausibility=None,
            containment=None,
            identity=None,
            fragmentation=None,
        ),
        scored=ScoredEvidence(
            score=score,
            contributions=contributions,
            effective_weights={name: 0.2 for name in contributions},
        ),
    )


def test_compare_candidates_reports_weighted_differences() -> None:
    selected = make_recommendation(
        "contig_a",
        0.90,
        {
            "protein_confidence": 0.20,
            "orf_quality": 0.12,
            "blastx_consistency": 0.20,
        },
    )
    runner_up = make_recommendation(
        "contig_b",
        0.82,
        {
            "protein_confidence": 0.18,
            "orf_quality": 0.05,
            "blastx_consistency": 0.23,
        },
    )

    comparison = compare_candidates(selected, runner_up)

    assert comparison.candidate_id == "contig_b"
    assert comparison.score_gap == pytest.approx(0.08)
    assert any("ORF quality" in reason for reason in comparison.reasons_not_selected)
    assert any(
        "ORF–BLASTX consistency" in reason
        for reason in comparison.alternative_advantages
    )
    assert comparison.strongest_difference in comparison.reasons_not_selected


def test_build_candidate_comparisons_uses_all_alternatives() -> None:
    selected = make_recommendation("contig_a", 0.90, {"orf_quality": 0.12})
    second = make_recommendation("contig_b", 0.80, {"orf_quality": 0.05})
    third = make_recommendation("contig_c", 0.70, {"orf_quality": 0.02})

    comparisons = build_candidate_comparisons((selected, second, third))

    assert [item.candidate_id for item in comparisons] == ["contig_b", "contig_c"]


def test_tied_scores_explain_deterministic_tie_break() -> None:
    selected = make_recommendation(
        "contig_a",
        0.80,
        {"orf_quality": 0.10},
        confidence=100,
    )
    runner_up = make_recommendation(
        "contig_b",
        0.80,
        {"orf_quality": 0.10},
        confidence=90,
    )

    comparison = compare_candidates(selected, runner_up)

    assert comparison.close_alternative is True
    assert "raw protein confidence" in comparison.strongest_difference
