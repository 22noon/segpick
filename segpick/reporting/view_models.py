from __future__ import annotations

from dataclasses import dataclass

from segpick.models import CandidateContig, Gene
from segpick.scoring import GeneRecommendation


@dataclass(frozen=True, slots=True)
class ReadSupportView:
    available: bool
    mean_depth: float | None
    median_depth: float | None
    covered_fraction: float | None
    uniformity: float | None
    left_terminal_support: float | None
    right_terminal_support: float | None
    overall_support: float | None


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
    runner_up_id: str | None
    runner_up_score: float | None
    score_gap: float | None
    runner_up_strength: str | None


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
    read_support: ReadSupportView


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

    runner_up = (
        recommendation.candidates[1]
        if len(recommendation.candidates) > 1
        else None
    )

    if runner_up is None:
        score_gap = None
        runner_up_strength = None
    else:
        score_gap = selected.score - runner_up.score
        if score_gap < 0.05:
            runner_up_strength = "close"
        elif score_gap <= 0.15:
            runner_up_strength = "secondary"
        else:
            runner_up_strength = "weak"

    return RecommendationView(
        candidate_id=selected.candidate_id,
        score=selected.score,
        evidence=evidence,
        runner_up_id=runner_up.candidate_id if runner_up else None,
        runner_up_score=runner_up.score if runner_up else None,
        score_gap=score_gap,
        runner_up_strength=runner_up_strength,
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
            structural_score=candidate.analysis.containment.structural_score,
            status=candidate.analysis.containment.status,
            recommended=candidate.id == recommended_id,
            read_support=build_read_support_view(candidate),
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


def build_read_support_view(candidate: CandidateContig) -> ReadSupportView:
    """Build optional read-support data for dashboard presentation."""

    metrics = candidate.analysis.read_support
    if metrics is None:
        return ReadSupportView(
            available=False,
            mean_depth=None,
            median_depth=None,
            covered_fraction=None,
            uniformity=None,
            left_terminal_support=None,
            right_terminal_support=None,
            overall_support=None,
        )

    return ReadSupportView(
        available=True,
        mean_depth=metrics.mean_depth,
        median_depth=metrics.median_depth,
        covered_fraction=metrics.covered_fraction,
        uniformity=metrics.uniformity,
        left_terminal_support=metrics.left_terminal_support,
        right_terminal_support=metrics.right_terminal_support,
        overall_support=metrics.read_support,
    )
