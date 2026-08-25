from __future__ import annotations

from segpick.evidence_plugins import EvidencePluginRegistry
from segpick.models import BiologicalHypothesis, CandidateContig, Gene, MeasurementNode, Sample
from segpick.reasoning import CANDIDATE_RULES, GENE_RULES, HypothesisRule, evaluate_rule_set, evaluate_rules
from segpick.reasoning.graph import build_reasoning_graph


def candidate_biological_hypotheses(
    candidate: CandidateContig,
    rules: tuple[HypothesisRule, ...] = CANDIDATE_RULES,
) -> tuple[BiologicalHypothesis, ...]:
    return evaluate_rules(
        rules,
        candidate.analysis.observations,
        candidate.analysis.findings,
        candidate_ids=(candidate.id,),
    )


def gene_biological_hypotheses(
    gene: Gene,
    rules: tuple[HypothesisRule, ...] = GENE_RULES,
) -> tuple[BiologicalHypothesis, ...]:
    observations = tuple(
        observation
        for candidate in gene.candidates
        for observation in candidate.analysis.observations
    )
    candidate_ids = tuple(candidate.id for candidate in gene.candidates)
    return evaluate_rules(
        rules,
        observations,
        gene.findings,
        candidate_ids=candidate_ids,
    )


def attach_biological_hypotheses(
    sample: Sample,
    candidate_rules: tuple[HypothesisRule, ...] = CANDIDATE_RULES,
    gene_rules: tuple[HypothesisRule, ...] = GENE_RULES,
    plugin_registry: EvidencePluginRegistry | None = None,
) -> None:
    for gene in sample.genes.values():
        for candidate in gene.candidates:
            if plugin_registry is not None:
                plugin_observations = []
                plugin_measurements = []
                for channel_id, result in plugin_registry.evaluate(candidate):
                    for index, item in enumerate(result.measurements, 1):
                        plugin_measurements.append(MeasurementNode(
                            id=f"measurement:plugin-{channel_id}:{item.name}:{index}",
                            channel=channel_id,
                            name=item.name,
                            value=item.value,
                            unit=item.unit,
                            provenance=item.provenance,
                            attributes=item.attributes,
                        ))
                    plugin_observations.extend(result.observations)
                candidate.analysis.plugin_measurements = tuple(plugin_measurements)
                candidate.analysis.observations = candidate.analysis.observations + tuple(plugin_observations)
            candidate.analysis.hypotheses = candidate_biological_hypotheses(candidate, candidate_rules)
            candidate.analysis.rule_evaluations = evaluate_rule_set(candidate_rules, candidate.analysis.observations, candidate.analysis.findings)
            candidate.analysis.reasoning_graph = build_reasoning_graph(candidate)
        gene.hypotheses = gene_biological_hypotheses(gene, gene_rules)
        observations = tuple(o for c in gene.candidates for o in c.analysis.observations)
        gene.rule_evaluations = evaluate_rule_set(gene_rules, observations, gene.findings)
