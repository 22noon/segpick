from __future__ import annotations

from dataclasses import dataclass

from .agreement import EvidenceAgreement


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
