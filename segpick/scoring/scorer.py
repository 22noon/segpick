from __future__ import annotations

from dataclasses import asdict, dataclass

from .evidence import Evidence
from .weights import ScoringWeights


@dataclass(frozen=True, slots=True)
class ScoredEvidence:
    """Weighted scoring result for one candidate."""

    score: float
    contributions: dict[str, float]
    effective_weights: dict[str, float]

    def to_dict(self) -> dict[str, object]:
        return {
            "score": self.score,
            "contributions": dict(self.contributions),
            "effective_weights": dict(self.effective_weights),
        }


def score_evidence(
    evidence: Evidence,
    weights: ScoringWeights,
) -> ScoredEvidence:
    """Score available evidence using redistributed weights.

    Missing evidence channels are excluded. Their weights are redistributed
    proportionally across the evidence channels available for this candidate.
    """

    evidence_values = evidence.available()
    configured_weights = asdict(weights)

    available_weight_total = sum(configured_weights[name] for name in evidence_values)

    if available_weight_total <= 0:
        raise ValueError("No positive scoring weight is available for this candidate's evidence")

    effective_weights = {name: configured_weights[name] / available_weight_total for name in evidence_values}

    contributions = {name: evidence_values[name] * effective_weights[name] for name in evidence_values}

    return ScoredEvidence(
        score=sum(contributions.values()),
        contributions=contributions,
        effective_weights=effective_weights,
    )
