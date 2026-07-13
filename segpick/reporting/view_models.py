from __future__ import annotations

from dataclasses import dataclass

from segpick.models import Gene
from segpick.scoring import GeneRecommendation


@dataclass(frozen=True, slots=True)
class EvidenceView:
    name: str
    value: float | None
    contribution: float | None
    effective_weight: float | None


@dataclass(frozen=True, slots=True)
class RecommendationView:
    candidate_id: str
    score: float
    evidence: tuple[EvidenceView, ...]


@dataclass(frozen=True, slots=True)
class CandidateView:
    candidate_id: str
    length: int
    confidence: float
    z: float | None
    cluster: str
    query_coverage: float
    anchor_coverage: float
    identity: float
    fragmentation: float
    structural_score: float
    status: str
    recommended: bool


@dataclass(frozen=True, slots=True)
class GenePageView:
    gene: str
    segment: str
    anchor: str | None
    recommendation: RecommendationView | None
    candidates: tuple[CandidateView, ...]


def build_recommendation_view(
    recommendation: GeneRecommendation | None,
) -> RecommendationView | None:
    if recommendation is None:
        return None

    selected = recommendation.recommended

    evidence = tuple(
        EvidenceView(
            name=name,
            value=value,
            contribution=selected.scored.contributions.get(name),
            effective_weight=selected.scored.effective_weights.get(name),
        )
        for name, value in selected.evidence.to_dict().items()
    )

    return RecommendationView(
        candidate_id=selected.candidate_id,
        score=selected.score,
        evidence=evidence,
    )


def build_gene_page_view(
    gene: Gene,
    recommendation: GeneRecommendation | None,
) -> GenePageView:
    recommended_id = (
        recommendation.recommended.candidate_id
        if recommendation is not None
        else None
    )

    candidates = tuple(
        CandidateView(
            candidate_id=candidate.id,
            length=candidate.length,
            confidence=float(candidate.metadata.confidence),
            z=candidate.metadata.z,
            cluster=str(candidate.metadata.cluster),
            query_coverage=candidate.analysis.containment.query_coverage,
            anchor_coverage=candidate.analysis.containment.anchor_coverage,
            identity=candidate.analysis.containment.identity,
            fragmentation=candidate.analysis.containment.fragmentation,
            structural_score=(
                candidate.analysis.containment.structural_score
            ),
            status=candidate.analysis.containment.status,
            recommended=candidate.id == recommended_id,
        )
        for candidate in gene.candidates
    )

    return GenePageView(
        gene=gene.name,
        segment=gene.segment,
        anchor=gene.anchor_id,
        recommendation=build_recommendation_view(recommendation),
        candidates=candidates,
    )
