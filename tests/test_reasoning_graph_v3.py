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
    rule_finding = next(item for item in graph.interpretations if item.rule_id == "junction_supported_structure")
    assert rule_finding.supporting_ids == (graph.observations[0].id,)
    assert graph.hypotheses == ()
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

    findings = {
        node.rule_id: node
        for node in candidate.analysis.reasoning_graph.interpretations
        if node.rule_id
    }
    assert findings["possible_repeated_sequence_architecture"].state == "supported"
    assert findings["possible_repeat_associated_assembly_artefact"].state == "challenged"


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

    node = next(
        item
        for item in candidate.analysis.reasoning_graph.interpretations
        if item.rule_id == "junction_supported_structure"
    )
    assert node.category == "assembly_structure"
    assert node.scope == "candidate"
    assert node.severity == "review"
    assert node.rule_source == "user:test-rules.yml"
    assert node.rule_description == "Tests preservation of declarative rule provenance."
    assert node.rule_references == ("doi:10.0000/example",)
    serialized = candidate.analysis.reasoning_graph.to_dict()
    rule_findings = [item for item in serialized["interpretations"] if item["rule_id"]]
    assert rule_findings[0]["rule_source"] == "user:test-rules.yml"
    assert serialized["hypotheses"] == []


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
    assert {item.hypothesis_type for item in graph.hypotheses} == {"biological"}
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


def test_biological_hypothesis_node_is_the_canonical_final_graph_class():
    from segpick.models import BiologicalHypothesisNode, HypothesisNode

    node = BiologicalHypothesisNode(
        id="hypothesis:genuine-tandem-duplication:1",
        title="Genuine tandem duplication",
        summary="The integrated evidence supports a duplicated biological structure.",
        confidence="moderate",
        supporting_ids=("scenario:duplication-pattern:1",),
    )

    assert isinstance(node, BiologicalHypothesisNode)
    assert HypothesisNode is BiologicalHypothesisNode
    assert node.hypothesis_type == "biological"


def test_rule_results_are_findings_and_only_scenario_results_are_final_hypotheses():
    from segpick.models import BiologicalScenario, ScenarioHypothesis
    from segpick.reasoning.graph import build_reasoning_graph

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
        severity="informational",
        base_confidence="moderate",
        summary="The proposed structure has direct junction support.",
        requires=(RuleCondition("observation", "junction_supported", "plugin:junction_support"),),
    )
    attach_biological_hypotheses(
        sample, candidate_rules=(rule,), gene_rules=(), plugin_registry=None
    )
    candidate.analysis.scenarios = (
        BiologicalScenario(
            scenario_id="junction_supported_pattern",
            title="Junction-supported evidence pattern",
            category="assembly_structure",
            scope="candidate",
            confidence="moderate",
            severity="informational",
            interpretation="The available evidence supports structural continuity.",
            candidate_ids=(candidate.id,),
            matched_required=("observation:junction_supported@plugin:junction_support",),
        ),
    )
    candidate.analysis.scenario_hypotheses = (
        ScenarioHypothesis(
            hypothesis_id="genuine_structure",
            title="Genuine biological structure",
            category="assembly_structure",
            scope="candidate",
            confidence="moderate",
            severity="informational",
            explanation="The evidence pattern supports a genuine structure.",
            candidate_ids=(candidate.id,),
            supporting_scenarios=("junction_supported_pattern",),
        ),
    )

    graph = build_reasoning_graph(candidate)

    assert any(item.rule_id == "junction_supported_structure" for item in graph.interpretations)
    assert len(graph.biological_hypotheses) == 1
    assert graph.biological_hypotheses is graph.hypotheses
    assert graph.biological_hypotheses[0].title == "Genuine biological structure"


def test_reasoning_graph_uses_canonical_collection_fields_with_legacy_aliases():
    from segpick.models import ReasoningGraph

    graph = ReasoningGraph()

    assert graph.interpretive_findings == ()
    assert graph.evidence_syntheses == ()
    assert graph.biological_hypotheses == ()
    assert graph.interpretations is graph.interpretive_findings
    assert graph.scenarios is graph.evidence_syntheses
    assert graph.hypotheses is graph.biological_hypotheses


def test_reasoning_graph_schema_v21_is_canonical_and_versioned():
    from segpick.models import ReasoningGraph

    graph = ReasoningGraph()
    payload = graph.to_dict(include_legacy_aliases=False)

    assert payload["schema_version"] == "2.1"
    assert set(payload) == {
        "schema_version",
        "measurements",
        "observations",
        "interpretive_findings",
        "evidence_syntheses",
        "biological_hypotheses",
        "edges",
    }



def test_reasoning_graph_can_emit_schema_v20_without_edges():
    from segpick.models import ReasoningGraph

    payload = ReasoningGraph().to_dict(schema_version="2.0")

    assert payload["schema_version"] == "2.0"
    assert set(payload) == {
        "schema_version",
        "measurements",
        "observations",
        "interpretive_findings",
        "evidence_syntheses",
        "biological_hypotheses",
    }


def test_reasoning_graph_serializes_explicit_provenance_edges():
    from segpick.models import ReasoningEdge, ReasoningGraph

    graph = ReasoningGraph(edges=(
        ReasoningEdge("observation:a", "measurement:a", "supported_by"),
    ))
    # Validation correctly rejects edges until both endpoint nodes exist.
    import pytest
    with pytest.raises(ValueError, match="references missing node"):
        graph.to_dict(include_legacy_aliases=False)

def test_reasoning_graph_default_export_preserves_legacy_collection_aliases():
    from segpick.models import ReasoningGraph

    payload = ReasoningGraph().to_dict()

    assert payload["interpretations"] is payload["interpretive_findings"]
    assert payload["scenarios"] is payload["evidence_syntheses"]
    assert payload["hypotheses"] is payload["biological_hypotheses"]


def test_reasoning_graph_can_emit_explicit_schema_v1_payload():
    from segpick.models import ReasoningGraph

    payload = ReasoningGraph().to_legacy_dict()

    assert payload["schema_version"] == "1.0"
    assert set(payload) == {
        "schema_version",
        "measurements",
        "observations",
        "interpretations",
        "scenarios",
        "hypotheses",
    }


def test_reasoning_graph_rejects_unknown_schema_version():
    import pytest

    from segpick.models import ReasoningGraph

    with pytest.raises(ValueError, match="Unsupported reasoning graph schema version"):
        ReasoningGraph().to_dict(schema_version="99")


def test_biological_hypothesis_graph_node_separates_definition_and_evaluation():
    from segpick.models import BiologicalHypothesisNode

    node = BiologicalHypothesisNode(
        id="hypothesis:duplication:1",
        title="Genuine duplication",
        summary="Repeated structure retains coding continuity.",
        confidence="high",
        supporting_ids=("synthesis:repeat:1",),
        rule_id="duplication",
        rule_source="builtin:hypotheses.yml",
        definition_id="duplication",
        definition_base_confidence="moderate",
        definition_supported_by=("repeat_with_continuity",),
        definition_contradicted_by=("breakpoint_loss",),
        definition_minimum_support=1,
        evaluation_candidate_ids=("contig_a",),
        evaluation_supporting_synthesis_ids=("repeat_with_continuity",),
    )

    payload = node.to_dict()

    assert payload["definition"]["hypothesis_id"] == "duplication"
    assert payload["definition"]["base_confidence"] == "moderate"
    assert payload["definition"]["supported_by"] == ["repeat_with_continuity"]
    assert payload["evaluation"]["candidate_ids"] == ["contig_a"]
    assert payload["evaluation"]["confidence"] == "high"
    assert payload["evaluation"]["supporting_synthesis_ids"] == ["repeat_with_continuity"]


def test_graph_inspector_separates_hypothesis_definition_and_current_evaluation():
    from segpick.models import BiologicalHypothesisNode, EvidenceSynthesisNode, ReasoningGraph
    from segpick.reporting.view_models import build_reasoning_graph_inspector_view

    _, candidate = _sample()
    synthesis = EvidenceSynthesisNode(
        id="synthesis:repeat:1",
        scenario_id="repeat_with_continuity",
        title="Repeat with continuity",
        interpretation="Repeated structure retains coding continuity.",
        confidence="moderate",
    )
    hypothesis = BiologicalHypothesisNode(
        id="hypothesis:duplication:1",
        title="Genuine duplication",
        summary="Repeated structure retains coding continuity.",
        confidence="high",
        state="supported",
        supporting_ids=(synthesis.id,),
        rule_id="duplication",
        rule_source="builtin:hypotheses.yml",
        rule_description="A repeated structure with continuity supports duplication.",
        rule_references=("doi:10.0000/example",),
        definition_id="duplication",
        definition_base_confidence="moderate",
        definition_supported_by=("repeat_with_continuity",),
        definition_contradicted_by=("breakpoint_loss",),
        definition_minimum_support=1,
        evaluation_candidate_ids=(candidate.id,),
        evaluation_supporting_synthesis_ids=("repeat_with_continuity",),
    )
    candidate.analysis.reasoning_graph = ReasoningGraph(
        evidence_syntheses=(synthesis,),
        biological_hypotheses=(hypothesis,),
    )

    view = build_reasoning_graph_inspector_view(candidate)

    assert len(view.hypotheses) == 1
    item = view.hypotheses[0]
    assert item.definition_id == "duplication"
    assert item.definition_base_confidence == "moderate"
    assert item.definition_supported_by == ("repeat_with_continuity",)
    assert item.evaluation_candidate_ids == (candidate.id,)
    assert item.evaluation_confidence == "high"
    assert item.evaluation_state == "supported"
    assert item.evaluation_supporting_synthesis_ids == ("repeat_with_continuity",)


def test_graph_inspector_template_labels_definition_and_current_evaluation():
    from pathlib import Path

    template = Path("segpick/reporting/templates/gene.html").read_text()

    assert "Biological hypothesis evaluations" in template
    assert "<h4>Definition</h4>" in template
    assert "<h4>Current evaluation</h4>" in template
    assert "Supporting evidence syntheses" in template
    assert "Conflicting evidence syntheses" in template


def test_graph_inspector_builds_typed_path_from_hypothesis_to_measurement():
    from segpick.models import (
        BiologicalHypothesisNode,
        EvidenceSynthesisNode,
        InterpretiveFindingNode,
        MeasurementNode,
        ObservationNode,
        ReasoningGraph,
    )
    from segpick.reporting.view_models import build_reasoning_graph_inspector_view

    _, candidate = _sample()
    measurement = MeasurementNode(
        id="measurement:block_count:1",
        channel="structural_alignment",
        name="alignment block count",
        value=4,
        unit="blocks",
    )
    observation = ObservationNode(
        id="observation:fragmented:1",
        observation_type="fragmented_architecture",
        source="structural_alignment",
        description="Several separated alignment blocks are present.",
        measurement_ids=(measurement.id,),
    )
    finding = InterpretiveFindingNode(
        id="finding:fragmentation:1",
        title="Fragmentation is plausible",
        summary="The alignment pattern is consistent with fragmentation.",
        observation_ids=(observation.id,),
        state="supported",
    )
    synthesis = EvidenceSynthesisNode(
        id="synthesis:partial:1",
        scenario_id="partial_assembly_pattern",
        title="Partial assembly evidence pattern",
        interpretation="The evidence is consistent with incomplete assembly.",
        confidence="moderate",
        supporting_ids=(finding.id,),
    )
    hypothesis = BiologicalHypothesisNode(
        id="hypothesis:partial:1",
        title="Partial assembly",
        summary="The candidate may be incomplete.",
        confidence="moderate",
        state="supported",
        supporting_ids=(synthesis.id,),
    )
    candidate.analysis.reasoning_graph = ReasoningGraph(
        measurements=(measurement,),
        observations=(observation,),
        interpretive_findings=(finding,),
        evidence_syntheses=(synthesis,),
        biological_hypotheses=(hypothesis,),
    )

    view = build_reasoning_graph_inspector_view(candidate)

    assert len(view.provenance_paths) == 1
    path = view.provenance_paths[0]
    assert tuple(step.node_type for step in path.steps) == (
        "biological hypothesis",
        "evidence synthesis",
        "interpretive finding",
        "observation",
        "measurement",
    )
    assert tuple(step.relationship for step in path.steps) == (
        "",
        "supported by",
        "composed from",
        "derived from",
        "supported by",
    )
    assert path.steps[-1].title == "alignment block count: 4 blocks"



def test_graph_inspector_consumes_explicit_reasoning_edges():
    from segpick.models import (
        BiologicalHypothesisNode, EvidenceSynthesisNode, InterpretiveFindingNode,
        MeasurementNode, ObservationNode, ReasoningEdge, ReasoningGraph,
    )
    from segpick.reporting.view_models import build_reasoning_graph_inspector_view

    _, candidate = _sample()
    measurement = MeasurementNode("measurement:m:1", "test", "metric", 1)
    observation = ObservationNode("observation:o:1", "observed", "test", "Observed evidence")
    finding = InterpretiveFindingNode("finding:f:1", "Finding", "Interpretation")
    synthesis = EvidenceSynthesisNode("synthesis:s:1", "s", "Synthesis", "Integrated", "high")
    hypothesis = BiologicalHypothesisNode("hypothesis:h:1", "Hypothesis", "Explanation", "high")
    edges = (
        ReasoningEdge(hypothesis.id, synthesis.id, "supported_by"),
        ReasoningEdge(synthesis.id, finding.id, "composed_from"),
        ReasoningEdge(finding.id, observation.id, "derived_from"),
        ReasoningEdge(observation.id, measurement.id, "supported_by"),
    )
    candidate.analysis.reasoning_graph = ReasoningGraph(
        measurements=(measurement,), observations=(observation,),
        interpretive_findings=(finding,), evidence_syntheses=(synthesis,),
        biological_hypotheses=(hypothesis,), edges=edges,
    )

    view = build_reasoning_graph_inspector_view(candidate)

    assert tuple(step.relationship for step in view.provenance_paths[0].steps) == (
        "", "supported by", "composed from", "derived from", "supported by",
    )
    payload = candidate.analysis.reasoning_graph.to_dict(include_legacy_aliases=False)
    assert payload["edges"] == [edge.to_dict() for edge in edges]

def test_graph_inspector_template_renders_typed_provenance_relationships():
    from pathlib import Path

    template = Path("segpick/reporting/templates/gene.html").read_text()

    assert "Typed hypothesis provenance" in template
    assert "graph-typed-path" in template
    assert "step.relationship" in template
    assert "step.node_type" in template
    assert "step.node_id" in template
