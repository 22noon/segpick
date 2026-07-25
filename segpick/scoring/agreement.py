from __future__ import annotations

from dataclasses import dataclass

from .recommendation import CandidateRecommendation


STRONG_EVIDENCE_CHANNELS = frozenset({"orf_quality", "blastx_consistency"})


@dataclass(frozen=True, slots=True)
class EvidenceAgreement:
    """Agreement between per-channel winners and the final recommendation."""

    channel_winners: dict[str, tuple[str, ...]]
    supporting_channels: tuple[str, ...]
    disagreeing_channels: tuple[str, ...]
    strong_conflicts: tuple[str, ...]
    agreement_fraction: float
    confidence: str

    def to_dict(self) -> dict[str, object]:
        return {
            "channel_winners": {
                name: list(winners)
                for name, winners in self.channel_winners.items()
            },
            "supporting_channels": list(self.supporting_channels),
            "disagreeing_channels": list(self.disagreeing_channels),
            "strong_conflicts": list(self.strong_conflicts),
            "agreement_fraction": self.agreement_fraction,
            "confidence": self.confidence,
        }


def assess_evidence_agreement(
    candidates: tuple[CandidateRecommendation, ...],
    recommended_id: str,
) -> EvidenceAgreement:
    """Identify which candidate each available evidence channel favours."""

    channel_names = tuple(candidates[0].evidence.to_dict())
    channel_winners: dict[str, tuple[str, ...]] = {}

    for channel in channel_names:
        values = [
            (candidate.candidate_id, candidate.evidence.to_dict()[channel])
            for candidate in candidates
            if candidate.evidence.to_dict()[channel] is not None
        ]
        if not values:
            continue

        maximum = max(value for _, value in values)
        channel_winners[channel] = tuple(
            candidate_id
            for candidate_id, value in values
            if abs(value - maximum) <= 1e-12
        )

    supporting = tuple(
        channel
        for channel, winners in channel_winners.items()
        if recommended_id in winners
    )
    disagreeing = tuple(
        channel
        for channel, winners in channel_winners.items()
        if recommended_id not in winners
    )
    strong_conflicts = tuple(
        channel for channel in disagreeing if channel in STRONG_EVIDENCE_CHANNELS
    )

    agreement_fraction = (
        len(supporting) / len(channel_winners)
        if channel_winners
        else 0.0
    )

    if strong_conflicts or agreement_fraction < 0.50:
        confidence = "low"
    elif disagreeing or agreement_fraction < 0.75:
        confidence = "medium"
    else:
        confidence = "high"

    return EvidenceAgreement(
        channel_winners=channel_winners,
        supporting_channels=supporting,
        disagreeing_channels=disagreeing,
        strong_conflicts=strong_conflicts,
        agreement_fraction=agreement_fraction,
        confidence=confidence,
    )
