from __future__ import annotations

from segpick.models import BiologicalHypothesis, CandidateContig, Gene, Sample
from segpick.reasoning import CANDIDATE_RULES, GENE_RULES, HypothesisRule, evaluate_rules


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
) -> None:
    for gene in sample.genes.values():
        for candidate in gene.candidates:
            candidate.analysis.hypotheses = candidate_biological_hypotheses(
                candidate, candidate_rules
            )
        gene.hypotheses = gene_biological_hypotheses(gene, gene_rules)
