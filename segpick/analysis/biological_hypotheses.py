from __future__ import annotations

from segpick.knowledge import HypothesisModule, evaluate_hypotheses
from segpick.models import Sample
from segpick.reasoning.graph import build_reasoning_graph


def attach_biological_hypotheses(
    sample: Sample,
    candidate_definitions: tuple[HypothesisModule, ...],
    gene_definitions: tuple[HypothesisModule, ...],
) -> None:
    for gene in sample.genes.values():
        for candidate in gene.candidates:
            candidate.analysis.biological_hypothesis_evaluations = evaluate_hypotheses(
                candidate_definitions,
                candidate.analysis.evidence_patterns,
                candidate_ids=(candidate.id,),
            )
            candidate.analysis.reasoning_graph = build_reasoning_graph(candidate)
        gene.biological_hypothesis_evaluations = evaluate_hypotheses(
            gene_definitions,
            gene.evidence_patterns,
            candidate_ids=tuple(candidate.id for candidate in gene.candidates),
        )
