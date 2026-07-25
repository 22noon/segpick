from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .evidence import Evidence
from .scorer import ScoredEvidence

if TYPE_CHECKING:
    from .reasoning import RecommendationReport


@dataclass(frozen=True, slots=True)
class CandidateRecommendation:
    """Scoring and evidence details for one candidate."""

    candidate_id: str
    length: int
    protein_confidence_raw: float
    evidence: Evidence
    scored: ScoredEvidence

    @property
    def score(self) -> float:
        return self.scored.score

    def to_dict(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "length": self.length,
            "protein_confidence_raw": self.protein_confidence_raw,
            "score": self.score,
            "evidence": self.evidence.to_dict(),
            "contributions": dict(self.scored.contributions),
            "effective_weights": dict(self.scored.effective_weights),
        }


@dataclass(frozen=True, slots=True)
class GeneRecommendation:
    """Ranked recommendation result for one gene."""

    gene: str
    recommended: CandidateRecommendation
    candidates: tuple[CandidateRecommendation, ...]
    agreement: object | None = None
    report: RecommendationReport | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "gene": self.gene,
            "recommended": self.recommended.to_dict(),
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "agreement": (
                self.agreement.to_dict()
                if self.agreement is not None
                else None
            ),
            "report": (
                self.report.to_dict()
                if self.report is not None
                else None
            ),
        }
