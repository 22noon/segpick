from __future__ import annotations

from dataclasses import dataclass

from .agreement import EvidenceAgreement
from .recommendation import CandidateRecommendation


CHANNEL_LABELS = {
    "protein_confidence": "Protein confidence",
    "length_plausibility": "Length plausibility",
    "containment": "Containment",
    "identity": "Reference identity",
    "fragmentation": "Fragmentation",
    "read_support": "Read support",
    "orf_quality": "ORF quality",
    "blastx_consistency": "ORF–BLASTX consistency",
}


@dataclass(frozen=True, slots=True)
class CandidateComparison:
    """Explain why an alternative candidate ranked below the recommendation."""

    candidate_id: str
    score: float
    score_gap: float
    reasons_not_selected: tuple[str, ...]
    alternative_advantages: tuple[str, ...]
    strongest_difference: str
    close_alternative: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "score": self.score,
            "score_gap": self.score_gap,
            "reasons_not_selected": list(self.reasons_not_selected),
            "alternative_advantages": list(self.alternative_advantages),
            "strongest_difference": self.strongest_difference,
            "close_alternative": self.close_alternative,
        }


@dataclass(frozen=True, slots=True)
class RecommendationReport:
    """Human-readable reasoning attached to a gene recommendation."""

    recommended_candidate: str
    confidence: str
    supporting_evidence: tuple[str, ...]
    opposing_evidence: tuple[str, ...]
    evidence_conflicts: tuple[str, ...]
    manual_review: bool
    summary: str

    def to_dict(self) -> dict[str, object]:
        return {
            "recommended_candidate": self.recommended_candidate,
            "confidence": self.confidence,
            "supporting_evidence": list(self.supporting_evidence),
            "opposing_evidence": list(self.opposing_evidence),
            "evidence_conflicts": list(self.evidence_conflicts),
            "manual_review": self.manual_review,
            "summary": self.summary,
        }


def build_recommendation_report(
    recommended_candidate: str,
    agreement: EvidenceAgreement,
) -> RecommendationReport:
    """Convert evidence agreement into an initial explanation report."""

    supporting = tuple(
        f"{_label(channel)} supports the recommended candidate."
        for channel in agreement.supporting_channels
    )

    opposing = tuple(
        f"{_label(channel)} favours {_format_winners(agreement.channel_winners[channel])}."
        for channel in agreement.disagreeing_channels
    )

    conflicts = tuple(
        f"Strong structural evidence from {_label(channel)} favours "
        f"{_format_winners(agreement.channel_winners[channel])}."
        for channel in agreement.strong_conflicts
    )

    manual_review = bool(agreement.strong_conflicts) or agreement.confidence == "low"

    if manual_review:
        summary = (
            f"{recommended_candidate} is the weighted recommendation, but conflicting "
            "evidence warrants manual review."
        )
    elif agreement.confidence == "medium":
        summary = (
            f"{recommended_candidate} is recommended, although some evidence favours "
            "an alternative candidate."
        )
    else:
        summary = (
            f"{recommended_candidate} is supported by the available evidence with no "
            "major conflicts detected."
        )

    return RecommendationReport(
        recommended_candidate=recommended_candidate,
        confidence=agreement.confidence,
        supporting_evidence=supporting,
        opposing_evidence=opposing,
        evidence_conflicts=conflicts,
        manual_review=manual_review,
        summary=summary,
    )


def _label(channel: str) -> str:
    return CHANNEL_LABELS.get(channel, channel.replace("_", " ").title())


def _format_winners(winners: tuple[str, ...]) -> str:
    if len(winners) == 1:
        return winners[0]
    return ", ".join(winners[:-1]) + f" and {winners[-1]}"


def compare_candidates(
    recommended: CandidateRecommendation,
    alternative: CandidateRecommendation,
    *,
    contribution_threshold: float = 0.01,
) -> CandidateComparison:
    """Explain the weighted evidence differences between two candidates."""

    differences: list[tuple[float, str]] = []
    advantages: list[tuple[float, str]] = []

    channels = sorted(
        set(recommended.scored.contributions)
        | set(alternative.scored.contributions)
    )

    for channel in channels:
        recommended_contribution = recommended.scored.contributions.get(channel, 0.0)
        alternative_contribution = alternative.scored.contributions.get(channel, 0.0)
        delta = recommended_contribution - alternative_contribution
        label = _label(channel)

        if delta >= contribution_threshold:
            differences.append(
                (
                    delta,
                    f"{label} contributes more strongly to the recommended candidate.",
                )
            )
        elif delta <= -contribution_threshold:
            advantages.append(
                (
                    -delta,
                    f"{label} is stronger for {alternative.candidate_id}.",
                )
            )

    differences.sort(key=lambda item: (-item[0], item[1]))
    advantages.sort(key=lambda item: (-item[0], item[1]))

    reasons = tuple(message for _, message in differences[:3])
    alternative_advantages = tuple(message for _, message in advantages[:3])

    if not reasons:
        reasons = (_tie_break_reason(recommended, alternative),)

    score_gap = recommended.score - alternative.score

    return CandidateComparison(
        candidate_id=alternative.candidate_id,
        score=alternative.score,
        score_gap=score_gap,
        reasons_not_selected=reasons,
        alternative_advantages=alternative_advantages,
        strongest_difference=reasons[0],
        close_alternative=score_gap < 0.05,
    )


def build_candidate_comparisons(
    candidates: tuple[CandidateRecommendation, ...],
) -> tuple[CandidateComparison, ...]:
    if len(candidates) < 2:
        return ()

    recommended = candidates[0]
    return tuple(
        compare_candidates(recommended, alternative)
        for alternative in candidates[1:]
    )


def _tie_break_reason(
    recommended: CandidateRecommendation,
    alternative: CandidateRecommendation,
) -> str:
    if recommended.protein_confidence_raw > alternative.protein_confidence_raw:
        return "The weighted scores are effectively tied, but raw protein confidence is higher."
    if recommended.length > alternative.length:
        return "The weighted scores and protein confidence are tied, but the recommended candidate is longer."
    return "The candidates are effectively tied; deterministic candidate ordering selected the recommendation."
