from __future__ import annotations

from segpick.knowledge import HypothesisModule, evaluate_hypotheses
from segpick.models import Sample
from segpick.reasoning import load_active_conclusion_rules
from segpick.reasoning.conclusion_rules import evaluate_conclusions
from segpick.reasoning.graph import build_reasoning_graph


def attach_biological_hypotheses(
    sample: Sample,
    candidate_definitions: tuple[HypothesisModule, ...],
    gene_definitions: tuple[HypothesisModule, ...],
) -> None:
    candidate_conclusion_rules, gene_conclusion_rules = load_active_conclusion_rules()
    all_conclusion_rules = candidate_conclusion_rules + gene_conclusion_rules
    
    for gene in sample.genes.values():
        for candidate in gene.candidates:
            candidate.analysis.biological_hypothesis_evaluations = evaluate_hypotheses(
                candidate_definitions,
                candidate.analysis.evidence_patterns,
                candidate_ids=(candidate.id,),
            )
            candidate.analysis.reasoning_graph = build_reasoning_graph(candidate)
            
            # Store scientific conclusion evaluations in analysis (for view models)
            if candidate.analysis.reasoning_graph is not None:
                # Re-evaluate to get the full evaluation objects
                candidate.analysis.scientific_conclusions = evaluate_conclusions(
                    all_conclusion_rules,
                    candidate.analysis.biological_hypothesis_evaluations,
                    candidate_ids=(candidate.id,),
                )
        gene.biological_hypothesis_evaluations = evaluate_hypotheses(
            gene_definitions,
            gene.evidence_patterns,
            candidate_ids=tuple(candidate.id for candidate in gene.candidates),
        )
