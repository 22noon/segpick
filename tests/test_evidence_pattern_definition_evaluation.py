from segpick.knowledge import EvidencePatternDefinition
from segpick.models import (
    EvidencePatternEvaluation,
    EvidencePatternProvenance,
)
from segpick.reasoning.rules import RuleCondition


def test_evidence_pattern_definition_is_canonical_knowledge_class():
    assert EvidencePatternDefinition is EvidencePatternDefinition

    definition = EvidencePatternDefinition(
        pattern_id="repeat_with_continuity",
        title="Repeated mapping with coding continuity",
        category="structure",
        scope="candidate",
        severity="moderate",
        base_confidence="moderate",
        interpretation="Repeated mapping occurs with preserved coding continuity.",
        requires=(RuleCondition(kind="observation", value="repeated_mapping"),),
    )

    assert definition.pattern_id == "repeat_with_continuity"


def test_evidence_pattern_evaluation_is_canonical_result_class():
    assert EvidencePatternEvaluation is EvidencePatternEvaluation
    assert EvidencePatternProvenance is EvidencePatternProvenance

    provenance = EvidencePatternProvenance(
        condition="Repeated mapping",
        kind="observation",
        source="structural_alignment",
    )
    evaluation = EvidencePatternEvaluation(
        pattern_id="repeat_with_continuity",
        title="Repeated mapping with coding continuity",
        category="structure",
        scope="candidate",
        confidence="moderate",
        severity="moderate",
        interpretation="Repeated mapping occurs with preserved coding continuity.",
        candidate_ids=("contig_a",),
        matched_required=("Repeated mapping",),
        evidence_provenance=(provenance,),
    )

    assert evaluation.pattern_id == "repeat_with_continuity"
    assert evaluation.candidate_ids == ("contig_a",)
    assert evaluation.evidence_provenance == (provenance,)


def test_evidence_pattern_evaluation_exposes_pattern_match_details():
    evaluation = EvidencePatternEvaluation(
        pattern_id="repeat_with_continuity",
        title="Repeated mapping with coding continuity",
        category="structure",
        scope="candidate",
        confidence="low",
        severity="moderate",
        interpretation="Repeated mapping occurs with preserved coding continuity.",
        state="contradicted",
        matched_required=("observation:repeated_mapping",),
        matched_supporting=("finding:Coding continuity preserved",),
        matched_conflicting=("observation:breakpoint_depletion",),
        missing_supporting=("observation:uniform_coverage",),
        unused_findings=("Protein similarity preserved",),
    )

    assert evaluation.pattern_id == "repeat_with_continuity"
    assert evaluation.state == "contradicted"
    assert evaluation.missing_required == ()
    assert evaluation.missing_supporting == ("observation:uniform_coverage",)
    payload = evaluation.to_dict()
    assert payload["state"] == "contradicted"
    assert payload["unused_findings"] == ["Protein similarity preserved"]


def test_analysis_collections_use_canonical_evidence_pattern_names():
    from segpick.models import ContigAnalysis, Gene

    analysis = ContigAnalysis()
    gene = Gene(name="VP1", segment="1")

    assert analysis.evidence_patterns == ()
    assert analysis.biological_hypothesis_evaluations == ()
    assert gene.evidence_patterns == ()
    assert gene.biological_hypothesis_evaluations == ()


def test_evidence_pattern_serialization_uses_pattern_id():
    evaluation = EvidencePatternEvaluation(
        pattern_id="repeat_with_continuity",
        title="Repeat with continuity",
        category="structure",
        scope="candidate",
        confidence="moderate",
        severity="review",
        interpretation="Pattern present.",
    )

    payload = evaluation.to_dict()
    assert payload["pattern_id"] == "repeat_with_continuity"
    assert set(payload) >= {"pattern_id", "state", "matched_required", "missing_required"}
