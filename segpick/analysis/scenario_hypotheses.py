from __future__ import annotations

from segpick.knowledge import HypothesisModule, evaluate_hypotheses
from segpick.models import Sample


def attach_scenario_hypotheses(
    sample: Sample,
    candidate_modules: tuple[HypothesisModule, ...],
    gene_modules: tuple[HypothesisModule, ...],
) -> None:
    for gene in sample.genes.values():
        for candidate in gene.candidates:
            candidate.analysis.scenario_hypotheses = evaluate_hypotheses(
                candidate_modules,
                candidate.analysis.scenarios,
                candidate_ids=(candidate.id,),
            )
        gene.scenario_hypotheses = evaluate_hypotheses(
            gene_modules,
            gene.scenarios,
            candidate_ids=tuple(candidate.id for candidate in gene.candidates),
        )
