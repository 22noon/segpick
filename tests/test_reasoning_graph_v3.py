from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from segpick.analysis.hypotheses import attach_biological_hypotheses
from segpick.evidence_plugins import (
    EvidencePluginRegistry,
    EvidencePluginResult,
    PluginMeasurement,
)
from segpick.models import CandidateContig, ContigMetadata, EvidenceObservation, Gene, Sample
from segpick.reasoning.rules import HypothesisRule, RuleCondition


class JunctionEvidenceChannel:
    channel_id = "junction_support"

    def evaluate(self, candidate):
        return EvidencePluginResult(
            measurements=(
                PluginMeasurement(
                    name="junction_spanning_reads",
                    value=18,
                    unit="reads",
                    provenance="plugin-test.tsv",
                ),
            ),
            observations=(
                EvidenceObservation(
                    observation_type="junction_supported",
                    source="plugin:junction_support",
                    description="Reads span the candidate junction.",
                    attributes={"count": 18},
                ),
            ),
        )


def _sample():
    candidate = CandidateContig(
        id="contig_1",
        record=SeqRecord(Seq("A" * 100), id="contig_1"),
        metadata=ContigMetadata(segment="1", score=10.0, confidence=0.9, cluster="a"),
    )
    gene = Gene(name="VP1", segment="1", candidates=[candidate])
    return Sample(name="sample", genes={"VP1": gene}), candidate


def test_plugin_observation_can_trigger_hypothesis_and_enter_graph():
    sample, candidate = _sample()
    registry = EvidencePluginRegistry()
    registry.register(JunctionEvidenceChannel())
    rule = HypothesisRule(
        rule_id="junction_supported_structure",
        title="Junction-supported structure",
        category="assembly_structure",
        scope="candidate",
        severity="informational",
        base_confidence="moderate",
        summary="The proposed structure has direct junction support.",
        requires=(RuleCondition("observation", "junction_supported", "plugin:junction_support"),),
    )

    attach_biological_hypotheses(sample, candidate_rules=(rule,), gene_rules=(), plugin_registry=registry)

    assert candidate.analysis.hypotheses[0].rule_id == "junction_supported_structure"
    graph = candidate.analysis.reasoning_graph
    assert graph is not None
    assert graph.measurements[0].channel == "junction_support"
    assert graph.observations[0].source == "plugin:junction_support"
    assert graph.observations[0].measurement_ids == (graph.measurements[0].id,)
    assert graph.hypotheses[0].supporting_ids == (graph.observations[0].id,)
    graph.validate()


def test_registry_rejects_duplicate_channel_ids():
    registry = EvidencePluginRegistry()
    registry.register(JunctionEvidenceChannel())
    try:
        registry.register(JunctionEvidenceChannel())
    except ValueError as exc:
        assert "already registered" in str(exc)
    else:
        raise AssertionError("duplicate plugin channel should be rejected")


def test_hypothesis_state_is_preserved_in_reasoning_graph():
    sample, candidate = _sample()
    candidate.analysis.observations = (
        EvidenceObservation(
            observation_type="duplicated_reference_mapping",
            source="reference_compatibility",
            description="Repeated reference coordinates.",
        ),
        EvidenceObservation(
            observation_type="junction_supported",
            source="plugin:junction_support",
            description="Reads span the candidate junction.",
        ),
    )
    attach_biological_hypotheses(sample, plugin_registry=None)

    hypotheses = {node.rule_id: node for node in candidate.analysis.reasoning_graph.hypotheses}
    assert hypotheses["possible_repeated_sequence_architecture"].state == "supported"
    assert hypotheses["possible_repeat_associated_assembly_artefact"].state == "challenged"


def test_hypothesis_metadata_and_rule_provenance_enter_graph():
    sample, candidate = _sample()
    candidate.analysis.observations = (
        EvidenceObservation(
            observation_type="junction_supported",
            source="plugin:junction_support",
            description="Reads span the candidate junction.",
        ),
    )
    rule = HypothesisRule(
        rule_id="junction_supported_structure",
        title="Junction-supported structure",
        category="assembly_structure",
        scope="candidate",
        severity="review",
        base_confidence="moderate",
        summary="The proposed structure has direct junction support.",
        description="Tests preservation of declarative rule provenance.",
        references=("doi:10.0000/example",),
        source="user:test-rules.yml",
        requires=(RuleCondition("observation", "junction_supported", "plugin:junction_support"),),
    )

    attach_biological_hypotheses(
        sample, candidate_rules=(rule,), gene_rules=(), plugin_registry=None
    )

    node = candidate.analysis.reasoning_graph.hypotheses[0]
    assert node.category == "assembly_structure"
    assert node.scope == "candidate"
    assert node.severity == "review"
    assert node.rule_source == "user:test-rules.yml"
    assert node.rule_description == "Tests preservation of declarative rule provenance."
    assert node.rule_references == ("doi:10.0000/example",)
    assert candidate.analysis.reasoning_graph.to_dict()["hypotheses"][0]["rule_source"] == "user:test-rules.yml"


def test_scenario_hypotheses_enter_graph_through_scenario_nodes():
    from segpick.models import BiologicalScenario, ScenarioHypothesis
    from segpick.reasoning.graph import build_reasoning_graph

    _, candidate = _sample()
    candidate.analysis.observations = (
        EvidenceObservation(
            observation_type="fragmented_alignment",
            source="structural_alignment",
            description="The alignment is split across multiple blocks.",
        ),
    )
    candidate.analysis.scenarios = (
        BiologicalScenario(
            scenario_id="fragmented_candidate_structure",
            title="Fragmented candidate structure",
            category="assembly_structure",
            scope="candidate",
            confidence="moderate",
            severity="review",
            interpretation="The candidate has fragmented structural support.",
            candidate_ids=(candidate.id,),
            matched_required=("observation:fragmented_alignment@structural_alignment",),
            source="builtin:test-scenarios.yml",
        ),
    )
    candidate.analysis.scenario_hypotheses = tuple(
        ScenarioHypothesis(
            hypothesis_id=f"scenario_hypothesis_{index}",
            title=f"Scenario hypothesis {index}",
            category="assembly_structure",
            scope="candidate",
            confidence="moderate",
            severity="review",
            explanation="A scenario-derived explanation.",
            candidate_ids=(candidate.id,),
            supporting_scenarios=("fragmented_candidate_structure",),
            source="builtin:test-hypotheses.yml",
        )
        for index in range(1, 4)
    )

    graph = build_reasoning_graph(candidate)

    assert len(graph.scenarios) == 1
    assert len(graph.hypotheses) == 3
    assert {item.hypothesis_type for item in graph.hypotheses} == {"scenario"}
    scenario_node = graph.scenarios[0]
    assert scenario_node.supporting_ids == (graph.observations[0].id,)
    assert all(item.supporting_ids == (scenario_node.id,) for item in graph.hypotheses)
    assert len(graph.to_dict()["hypotheses"]) == 3
    graph.validate()


def test_interpretive_finding_node_is_the_canonical_graph_class():
    from segpick.models import InterpretationNode, InterpretiveFindingNode

    node = InterpretiveFindingNode(
        id="finding:fragmented-architecture:1",
        title="Fragmented architecture",
        summary="The alignment pattern is consistent with fragmentation.",
        observation_ids=("observation:structural-alignment:fragmented-alignment:1",),
    )

    assert isinstance(node, InterpretiveFindingNode)
    assert InterpretationNode is InterpretiveFindingNode
    assert node.to_dict()["title"] == "Fragmented architecture"


def test_reasoning_graph_builds_interpretive_finding_instances():
    from segpick.models import BiologicalFinding, InterpretiveFindingNode
    from segpick.reasoning.graph import build_reasoning_graph

    _, candidate = _sample()
    candidate.analysis.observations = (
        EvidenceObservation(
            observation_type="fragmented_alignment",
            source="structural_alignment",
            description="The alignment is split across multiple blocks.",
        ),
    )
    candidate.analysis.findings = (
        BiologicalFinding(
            category="assembly_structure",
            title="Fragmented architecture",
            severity="review",
            confidence="moderate",
            scope="candidate",
            summary="The alignment pattern is consistent with fragmentation.",
            sources=("structural_alignment",),
        ),
    )

    graph = build_reasoning_graph(candidate)

    assert len(graph.interpretations) == 1
    assert isinstance(graph.interpretations[0], InterpretiveFindingNode)
    assert graph.interpretations[0].observation_ids == (graph.observations[0].id,)


def test_evidence_synthesis_node_is_the_canonical_graph_class():
    from segpick.models import EvidenceSynthesisNode, ScenarioNode

    node = EvidenceSynthesisNode(
        id="synthesis:fragmented-structure:1",
        scenario_id="fragmented_candidate_structure",
        title="Fragmented candidate structure",
        interpretation="Several findings form a fragmented-structure evidence pattern.",
        confidence="moderate",
        supporting_ids=("finding:fragmented-architecture:1",),
    )

    assert isinstance(node, EvidenceSynthesisNode)
    assert ScenarioNode is EvidenceSynthesisNode
    assert node.to_dict()["title"] == "Fragmented candidate structure"


def test_reasoning_graph_exposes_canonical_evidence_syntheses_accessor():
    from segpick.models import BiologicalScenario, EvidenceSynthesisNode
    from segpick.reasoning.graph import build_reasoning_graph

    _, candidate = _sample()
    candidate.analysis.observations = (
        EvidenceObservation(
            observation_type="fragmented_alignment",
            source="structural_alignment",
            description="The alignment is split across multiple blocks.",
        ),
    )
    candidate.analysis.scenarios = (
        BiologicalScenario(
            scenario_id="fragmented_candidate_structure",
            title="Fragmented candidate structure",
            category="assembly_structure",
            scope="candidate",
            confidence="moderate",
            severity="review",
            interpretation="The candidate has fragmented structural support.",
            candidate_ids=(candidate.id,),
            matched_required=("observation:fragmented_alignment@structural_alignment",),
            source="builtin:test-scenarios.yml",
        ),
    )

    graph = build_reasoning_graph(candidate)

    assert graph.evidence_syntheses is graph.scenarios
    assert isinstance(graph.evidence_syntheses[0], EvidenceSynthesisNode)
    # Keep the serialized key stable during the compatibility migration.
    assert graph.to_dict()["scenarios"][0]["scenario_id"] == "fragmented_candidate_structure"
