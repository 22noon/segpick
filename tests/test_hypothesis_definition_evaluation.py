from segpick.knowledge import HypothesisDefinition, HypothesisModule, evaluate_hypotheses
from segpick.models import (
    BiologicalScenario,
    HypothesisEvaluation,
    ScenarioHypothesis,
)


def _scenario(scenario_id: str, candidate_id: str) -> BiologicalScenario:
    return BiologicalScenario(
        scenario_id=scenario_id,
        title=scenario_id.replace("_", " ").title(),
        category="structure",
        scope="candidate",
        confidence="moderate",
        severity="info",
        interpretation="Matched evidence synthesis.",
        candidate_ids=(candidate_id,),
    )


def test_hypothesis_definition_is_canonical_knowledge_class():
    definition = HypothesisDefinition(
        hypothesis_id="tandem_duplication",
        title="Genuine tandem duplication",
        category="structure",
        scope="candidate",
        severity="info",
        base_confidence="moderate",
        explanation="Repeated architecture with preserved continuity.",
        supported_by=("duplication_pattern",),
    )

    assert HypothesisModule is HypothesisDefinition
    assert isinstance(definition, HypothesisDefinition)


def test_hypothesis_evaluation_is_canonical_result_class():
    definition = HypothesisDefinition(
        hypothesis_id="tandem_duplication",
        title="Genuine tandem duplication",
        category="structure",
        scope="candidate",
        severity="info",
        base_confidence="moderate",
        explanation="Repeated architecture with preserved continuity.",
        supported_by=("duplication_pattern",),
    )

    result = evaluate_hypotheses(
        (definition,),
        (_scenario("duplication_pattern", "contig_a"),),
    )[0]

    assert ScenarioHypothesis is HypothesisEvaluation
    assert isinstance(result, HypothesisEvaluation)
    assert result.hypothesis_id == definition.hypothesis_id
    assert result.candidate_ids == ("contig_a",)
    assert result.supporting_scenarios == ("duplication_pattern",)


def test_one_definition_produces_independent_candidate_evaluations():
    definition = HypothesisDefinition(
        hypothesis_id="partial_assembly",
        title="Partial assembly",
        category="assembly",
        scope="candidate",
        severity="warning",
        base_confidence="moderate",
        explanation="The evidence pattern is consistent with incomplete assembly.",
        supported_by=("fragmented_pattern",),
    )

    first = evaluate_hypotheses(
        (definition,),
        (_scenario("fragmented_pattern", "contig_a"),),
    )[0]
    second = evaluate_hypotheses(
        (definition,),
        (_scenario("fragmented_pattern", "contig_b"),),
    )[0]

    assert first.candidate_ids == ("contig_a",)
    assert second.candidate_ids == ("contig_b",)
    assert first is not second
    assert definition.supported_by == ("fragmented_pattern",)


def test_hypothesis_evaluation_preserves_definition_snapshot():
    definition = HypothesisDefinition(
        hypothesis_id="duplication",
        title="Genuine duplication",
        category="structure",
        scope="candidate",
        severity="informational",
        base_confidence="moderate",
        explanation="Repeated sequence may represent a genuine duplication.",
        supported_by=("repeat_with_continuity",),
        contradicted_by=("breakpoint_loss",),
        minimum_support=1,
    )
    scenario = BiologicalScenario(
        scenario_id="repeat_with_continuity",
        title="Repeat with continuity",
        category="structure",
        scope="candidate",
        severity="informational",
        confidence="moderate",
        interpretation="Repeated structure retains continuity.",
    )

    result = evaluate_hypotheses((definition,), (scenario,), candidate_ids=("contig_a",))[0]

    assert result.base_confidence == "moderate"
    assert result.definition_supported_by == ("repeat_with_continuity",)
    assert result.definition_contradicted_by == ("breakpoint_loss",)
    assert result.minimum_support == 1
