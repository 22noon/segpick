from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from segpick.analysis.hypotheses import (
    candidate_biological_hypotheses,
    gene_biological_hypotheses,
)
from segpick.models import (
    BiologicalFinding,
    CandidateContig,
    ContigMetadata,
    EvidenceObservation,
    Gene,
)
from segpick.reasoning import HypothesisRule, RuleCondition, evaluate_rules


def make_candidate(candidate_id="contig_a"):
    return CandidateContig(
        id=candidate_id,
        record=SeqRecord(Seq("ATGAAATAA"), id=candidate_id),
        metadata=ContigMetadata(
            segment="1", score=1.0, confidence=1.0, cluster="c1"
        ),
    )


def finding(title, candidate_id="contig_a"):
    return BiologicalFinding(
        category="test",
        title=title,
        severity="informational",
        confidence="high",
        scope="candidate",
        summary=title,
        sources=("test",),
        candidate_ids=(candidate_id,),
    )


def observation(kind, source):
    return EvidenceObservation(
        observation_type=kind,
        source=source,
        description=kind,
    )


def test_generic_rule_requires_all_conditions_and_records_trace():
    rule = HypothesisRule(
        rule_id="example",
        title="Example hypothesis",
        category="test",
        scope="candidate",
        severity="review",
        base_confidence="moderate",
        summary="Example",
        requires=(
            RuleCondition("observation", "coverage_drop", "read_coverage"),
            RuleCondition("finding", "Internal protein differences"),
        ),
        supports=(RuleCondition("finding", "Local evidence convergence"),),
    )
    result = evaluate_rules(
        (rule,),
        (observation("coverage_drop", "read_coverage"),),
        (
            finding("Internal protein differences"),
            finding("Local evidence convergence"),
        ),
        candidate_ids=("contig_a",),
    )

    assert len(result) == 1
    assert result[0].confidence == "high"
    assert len(result[0].matched_required) == 2
    assert result[0].matched_supporting == (
        "finding:Local evidence convergence",
    )


def test_candidate_rule_emits_possible_assembly_interruption():
    candidate = make_candidate()
    candidate.analysis.observations = (
        observation("internal_deletion", "protein_alignment"),
        observation("coverage_drop", "read_coverage"),
        observation("partial_orf_end_boundary", "orf_structure"),
    )
    candidate.analysis.findings = (finding("Local evidence convergence"),)

    result = candidate_biological_hypotheses(candidate)

    assert result[0].rule_id == "possible_assembly_interruption"
    assert result[0].confidence == "high"
    assert "observation:partial_orf_end_boundary@orf_structure" in (
        result[0].matched_supporting
    )


def test_complete_protein_reduces_interruption_confidence():
    candidate = make_candidate()
    candidate.analysis.observations = (
        observation("internal_deletion", "protein_alignment"),
        observation("coverage_drop", "read_coverage"),
    )
    candidate.analysis.findings = (finding("Complete protein recovered"),)

    result = candidate_biological_hypotheses(candidate)

    assert result[0].confidence == "low"
    assert result[0].matched_conflicting == (
        "finding:Complete protein recovered",
    )


def test_gene_rule_wraps_split_assembly_finding():
    gene = Gene(name="VP1", segment="1", candidates=[make_candidate()])
    gene.findings = (
        BiologicalFinding(
            category="assembly",
            title="Possible split assembly",
            severity="warning",
            confidence="high",
            scope="gene",
            summary="Fragments complement one another.",
            sources=("protein_continuity",),
            candidate_ids=("contig_a",),
        ),
    )

    result = gene_biological_hypotheses(gene)

    assert len(result) == 1
    assert result[0].rule_id == "possible_split_assembly"
    assert result[0].scope == "gene"
