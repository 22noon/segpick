from __future__ import annotations
from segpick.knowledge import KnowledgeModule, evaluate_scenarios
from segpick.models import Sample

def attach_biological_scenarios(sample: Sample, candidate_modules: tuple[KnowledgeModule, ...], gene_modules: tuple[KnowledgeModule, ...]) -> None:
    for gene in sample.genes.values():
        for candidate in gene.candidates:
            candidate.analysis.scenarios = evaluate_scenarios(
                candidate_modules,
                candidate.analysis.observations,
                candidate.analysis.findings,
                candidate_ids=(candidate.id,),
            )
        observations = tuple(o for c in gene.candidates for o in c.analysis.observations)
        gene.scenarios = evaluate_scenarios(
            gene_modules,
            observations,
            gene.findings,
            candidate_ids=tuple(c.id for c in gene.candidates),
        )
