from __future__ import annotations

from .rules import HypothesisRule, RuleCondition


CANDIDATE_RULES = (
    HypothesisRule(
        rule_id="possible_assembly_interruption",
        title="Possible assembly interruption",
        category="assembly",
        scope="candidate",
        severity="review",
        base_confidence="moderate",
        summary=(
            "Independent protein and read-coverage observations are consistent "
            "with a possible local assembly interruption."
        ),
        requires=(
            RuleCondition("observation", "internal_deletion", "protein_alignment"),
            RuleCondition("observation", "coverage_drop", "read_coverage"),
        ),
        supports=(
            RuleCondition("observation", "partial_orf_start_boundary", "orf_structure"),
            RuleCondition("observation", "partial_orf_end_boundary", "orf_structure"),
            RuleCondition("finding", "Local evidence convergence"),
        ),
        conflicts=(RuleCondition("finding", "Complete protein recovered"),),
    ),
    HypothesisRule(
        rule_id="divergent_structurally_supported_protein",
        title="Possible divergent lineage",
        category="homology",
        scope="candidate",
        severity="informational",
        base_confidence="moderate",
        summary=(
            "Low protein relatedness is accompanied by a structurally intact "
            "predicted protein, consistent with a potentially divergent lineage."
        ),
        requires=(
            RuleCondition("finding", "Divergent but structurally supported protein"),
            RuleCondition("finding", "Complete protein recovered"),
        ),
    ),
)


GENE_RULES = (
    HypothesisRule(
        rule_id="possible_split_assembly",
        title="Possible split assembly",
        category="assembly",
        scope="gene",
        severity="warning",
        base_confidence="high",
        summary=(
            "Complementary protein regions are distributed across multiple "
            "contigs, so selecting one contig may not recover the complete gene."
        ),
        requires=(RuleCondition("finding", "Possible split assembly"),),
    ),
)
