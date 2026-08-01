from __future__ import annotations
from segpick.knowledge import KnowledgeModule, evaluate_scenarios
from segpick.models import Sample

def attach_biological_scenarios(sample: Sample, candidate_modules: tuple[KnowledgeModule, ...], gene_modules: tuple[KnowledgeModule, ...]) -> None:
    for gene in sample.genes.values():
        for candidate in gene.candidates:
            all_patterns = evaluate_scenarios(
                candidate_modules,
                candidate.analysis.observations,
                candidate.analysis.findings,
                candidate_ids=(candidate.id,),
                include_incomplete=True,
            )
            candidate.analysis.evidence_patterns = tuple(
                item for item in all_patterns if item.state in {"matched", "contradicted"}
            )
            candidate.analysis.unresolved_evidence_patterns = tuple(
                item for item in all_patterns if item.state in {"partially_matched", "not_evaluable"}
            )
        observations = tuple(o for c in gene.candidates for o in c.analysis.observations)
        gene.evidence_patterns = evaluate_scenarios(
            gene_modules,
            observations,
            gene.findings,
            candidate_ids=tuple(c.id for c in gene.candidates),
        )
