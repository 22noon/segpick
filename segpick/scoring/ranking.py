from __future__ import annotations

from segpick.models import Gene

from .builder import build_gene_evidence
from .recommendation import (
    CandidateRecommendation,
    GeneRecommendation,
)
from .scorer import score_evidence
from .weights import ScoringWeights


def rank_gene(
    gene: Gene,
    weights: ScoringWeights,
) -> GeneRecommendation:
    """Rank all candidates for one gene.

    Ranking order is deterministic:

    1. higher weighted score
    2. higher raw protein confidence
    3. longer candidate
    4. alphabetical candidate id
    """

    if not gene.candidates:
        raise ValueError(f"Gene {gene.name!r} has no candidates to rank")

    evidence_by_id = build_gene_evidence(gene.candidates)

    recommendations = [
        CandidateRecommendation(
            candidate_id=candidate.id,
            length=candidate.length,
            protein_confidence_raw=float(candidate.metadata.confidence),
            evidence=evidence_by_id[candidate.id],
            scored=score_evidence(
                evidence_by_id[candidate.id],
                weights,
            ),
        )
        for candidate in gene.candidates
    ]

    ranked = tuple(
        sorted(
            recommendations,
            key=lambda item: (
                -item.score,
                -item.protein_confidence_raw,
                -item.length,
                item.candidate_id,
            ),
        )
    )

    return GeneRecommendation(
        gene=gene.name,
        recommended=ranked[0],
        candidates=ranked,
    )
