from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from segpick.analysis.hypotheses import attach_biological_hypotheses
from segpick.evidence_plugins import (
    EvidencePluginRegistry,
    EvidencePluginResult,
    PluginMeasurement,
)
from segpick.models import CandidateContig, ContigMetadata, EvidenceObservation, Gene, ReasoningEdge, Sample
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
    assert ReasoningEdge(
        graph.observations[0].id, graph.measurements[0].id, "supported_by"
    ) in graph.edges
    rule_finding = next(item for item in graph.interpretive_findings if item.rule_id == "junction_supported_structure")
    assert ReasoningEdge(
        rule_finding.id, graph.observations[0].id, "supported_by"
    ) in graph.edges
    assert graph.biological_hypotheses == ()
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
        for node in candidate.analysis.reasoning_graph.interpretive_findings
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
        for item in candidate.analysis.reasoning_graph.interpretive_findings
        if item.rule_id == "junction_supported_structure"
    )
    assert node.category == "assembly_structure"
    assert node.scope == "candidate"
    assert node.severity == "review"
    assert node.rule_source == "user:test-rules.yml"
    assert node.rule_description == "Tests preservation of declarative rule provenance."
    assert node.rule_references == ("doi:10.0000/example",)
    serialized = candidate.analysis.reasoning_graph.to_dict()
    rule_findings = [item for item in serialized["interpretive_findings"] if item["rule_id"]]
    assert rule_findings[0]["rule_source"] == "user:test-rules.yml"
    assert serialized["biological_hypotheses"] == []


def test_biological_hypothesis_evaluations_enter_graph_through_pattern_nodes():
    from segpick.models import EvidencePatternEvaluation, HypothesisEvaluation
    from segpick.reasoning.graph import build_reasoning_graph

    _, candidate = _sample()
    candidate.analysis.observations = (
        EvidenceObservation(
            observation_type="fragmented_alignment",
            source="structural_alignment",
            description="The alignment is split across multiple blocks.",
        ),
    )
    candidate.analysis.evidence_patterns = (
        EvidencePatternEvaluation(
            pattern_id="fragmented_candidate_structure",
            title="Fragmented candidate structure",
            category="assembly_structure",
            scope="candidate",
            confidence="moderate",
            severity="review",
            interpretation="The candidate has fragmented structural support.",
            candidate_ids=(candidate.id,),
            matched_required=("observation:fragmented_alignment@structural_alignment",),
            source="builtin:test-patterns.yml",
        ),
    )
    candidate.analysis.biological_hypothesis_evaluations = tuple(
        HypothesisEvaluation(
            hypothesis_id=f"pattern_hypothesis_{index}",
            title=f"EvidencePattern hypothesis {index}",
            category="assembly_structure",
            scope="candidate",
            confidence="moderate",
            severity="review",
            explanation="A pattern-derived explanation.",
            candidate_ids=(candidate.id,),
            supporting_patterns=("fragmented_candidate_structure",),
            source="builtin:test-hypotheses.yml",
        )
        for index in range(1, 4)
    )

    graph = build_reasoning_graph(candidate)

    assert len(graph.evidence_patterns) == 1
    assert len(graph.biological_hypotheses) == 3
    assert {item.hypothesis_type for item in graph.biological_hypotheses} == {"biological"}
    pattern_node = graph.evidence_patterns[0]
    assert ReasoningEdge(
        pattern_node.id, graph.observations[0].id, "composed_from"
    ) in graph.edges
    assert all(
        ReasoningEdge(item.id, pattern_node.id, "supported_by") in graph.edges
        for item in graph.biological_hypotheses
    )
    assert len(graph.to_dict()["biological_hypotheses"]) == 3
    graph.validate()


def test_interpretive_finding_node_is_the_canonical_graph_class():
    from segpick.models import InterpretiveFindingNode

    node = InterpretiveFindingNode(
        id="finding:fragmented-architecture:1",
        title="Fragmented architecture",
        summary="The alignment pattern is consistent with fragmentation.",
    )

    assert isinstance(node, InterpretiveFindingNode)
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

    assert len(graph.interpretive_findings) == 1
    assert isinstance(graph.interpretive_findings[0], InterpretiveFindingNode)
    assert ReasoningEdge(
        graph.interpretive_findings[0].id, graph.observations[0].id, "derived_from"
    ) in graph.edges


def test_evidence_synthesis_node_is_the_canonical_graph_class():
    from segpick.models import EvidencePatternNode

    node = EvidencePatternNode(
        id="synthesis:fragmented-structure:1",
        pattern_id="fragmented_candidate_structure",
        title="Fragmented candidate structure",
        interpretation="Several findings form a fragmented-structure evidence pattern.",
        confidence="moderate",
    )

    assert isinstance(node, EvidencePatternNode)
    assert node.to_dict()["title"] == "Fragmented candidate structure"


def test_reasoning_graph_exposes_canonical_evidence_patterns_accessor():
    from segpick.models import EvidencePatternEvaluation, EvidencePatternNode
    from segpick.reasoning.graph import build_reasoning_graph

    _, candidate = _sample()
    candidate.analysis.observations = (
        EvidenceObservation(
            observation_type="fragmented_alignment",
            source="structural_alignment",
            description="The alignment is split across multiple blocks.",
        ),
    )
    candidate.analysis.evidence_patterns = (
        EvidencePatternEvaluation(
            pattern_id="fragmented_candidate_structure",
            title="Fragmented candidate structure",
            category="assembly_structure",
            scope="candidate",
            confidence="moderate",
            severity="review",
            interpretation="The candidate has fragmented structural support.",
            candidate_ids=(candidate.id,),
            matched_required=("observation:fragmented_alignment@structural_alignment",),
            source="builtin:test-patterns.yml",
        ),
    )

    graph = build_reasoning_graph(candidate)

    assert isinstance(graph.evidence_patterns[0], EvidencePatternNode)
    assert graph.to_dict()["evidence_patterns"][0]["pattern_id"] == "fragmented_candidate_structure"


def test_biological_hypothesis_node_is_the_canonical_final_graph_class():
    from segpick.models import BiologicalHypothesisNode

    node = BiologicalHypothesisNode(
        id="hypothesis:genuine-tandem-duplication:1",
        title="Genuine tandem duplication",
        summary="The integrated evidence supports a duplicated biological structure.",
        confidence="moderate",
    )

    assert isinstance(node, BiologicalHypothesisNode)
    assert node.hypothesis_type == "biological"


def test_rule_results_are_findings_and_only_pattern_results_are_final_hypotheses():
    from segpick.models import EvidencePatternEvaluation, HypothesisEvaluation
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
    candidate.analysis.evidence_patterns = (
        EvidencePatternEvaluation(
            pattern_id="junction_supported_pattern",
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
    candidate.analysis.biological_hypothesis_evaluations = (
        HypothesisEvaluation(
            hypothesis_id="genuine_structure",
            title="Genuine biological structure",
            category="assembly_structure",
            scope="candidate",
            confidence="moderate",
            severity="informational",
            explanation="The evidence pattern supports a genuine structure.",
            candidate_ids=(candidate.id,),
            supporting_patterns=("junction_supported_pattern",),
        ),
    )

    graph = build_reasoning_graph(candidate)

    assert any(item.rule_id == "junction_supported_structure" for item in graph.interpretive_findings)
    assert len(graph.biological_hypotheses) == 1
    assert graph.biological_hypotheses[0].title == "Genuine biological structure"


def test_reasoning_graph_exposes_only_canonical_collection_fields():
    from segpick.models import ReasoningGraph

    graph = ReasoningGraph()

    assert graph.interpretive_findings == ()
    assert graph.evidence_patterns == ()
    assert graph.biological_hypotheses == ()
    assert not hasattr(graph, "interpretations")
    assert not hasattr(graph, "patterns")
    assert not hasattr(graph, "hypotheses")


def test_reasoning_graph_export_uses_single_canonical_schema():
    from segpick.models import ReasoningGraph

    graph = ReasoningGraph()
    payload = graph.to_dict()

    assert payload["schema_version"] == "4.0"
    assert set(payload) == {
        "schema_version",
        "measurements",
        "observations",
        "interpretive_findings",
        "evidence_patterns",
        "biological_hypotheses",
        "scientific_conclusions",
        "edges",
    }



def test_reasoning_graph_serializes_explicit_provenance_edges():
    from segpick.models import ReasoningEdge, ReasoningGraph

    graph = ReasoningGraph(edges=(
        ReasoningEdge("observation:a", "measurement:a", "supported_by"),
    ))
    import pytest
    with pytest.raises(ValueError, match="references missing node"):
        graph.to_dict()



def test_biological_hypothesis_graph_node_separates_definition_and_evaluation():
    from segpick.models import BiologicalHypothesisNode

    node = BiologicalHypothesisNode(
        id="hypothesis:duplication:1",
        title="Genuine duplication",
        summary="Repeated structure retains coding continuity.",
        confidence="high",
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
    from segpick.models import BiologicalHypothesisNode, EvidencePatternNode, ReasoningGraph
    from segpick.reporting.view_models import build_reasoning_graph_inspector_view

    _, candidate = _sample()
    synthesis = EvidencePatternNode(
        id="synthesis:repeat:1",
        pattern_id="repeat_with_continuity",
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
        evidence_patterns=(synthesis,),
        biological_hypotheses=(hypothesis,),
        edges=(ReasoningEdge(hypothesis.id, synthesis.id, "supported_by"),),
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
    assert "Supporting evidence patterns" in template
    assert "Conflicting evidence patterns" in template


def test_graph_inspector_builds_typed_path_from_hypothesis_to_measurement():
    from segpick.models import (
        BiologicalHypothesisNode,
        EvidencePatternNode,
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
    )
    finding = InterpretiveFindingNode(
        id="finding:fragmentation:1",
        title="Fragmentation is plausible",
        summary="The alignment pattern is consistent with fragmentation.",
        state="supported",
    )
    synthesis = EvidencePatternNode(
        id="synthesis:partial:1",
        pattern_id="partial_assembly_pattern",
        title="Partial assembly evidence pattern",
        interpretation="The evidence is consistent with incomplete assembly.",
        confidence="moderate",
    )
    hypothesis = BiologicalHypothesisNode(
        id="hypothesis:partial:1",
        title="Partial assembly",
        summary="The candidate may be incomplete.",
        confidence="moderate",
        state="supported",
    )
    from segpick.models import ReasoningEdge

    candidate.analysis.reasoning_graph = ReasoningGraph(
        measurements=(measurement,),
        observations=(observation,),
        interpretive_findings=(finding,),
        evidence_patterns=(synthesis,),
        biological_hypotheses=(hypothesis,),
        edges=(
            ReasoningEdge(hypothesis.id, synthesis.id, "supported_by"),
            ReasoningEdge(synthesis.id, finding.id, "composed_from"),
            ReasoningEdge(finding.id, observation.id, "derived_from"),
            ReasoningEdge(observation.id, measurement.id, "supported_by"),
        ),
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
        BiologicalHypothesisNode,
        EvidencePatternNode,
        InterpretiveFindingNode,
        MeasurementNode,
        ObservationNode,
        ReasoningEdge,
        ReasoningGraph,
    )
    from segpick.reporting.view_models import build_reasoning_graph_inspector_view

    _, candidate = _sample()
    measurement = MeasurementNode("measurement:m:1", "test", "metric", 1)
    observation = ObservationNode("observation:o:1", "observed", "test", "Observed evidence")
    finding = InterpretiveFindingNode("finding:f:1", "Finding", "Interpretation")
    synthesis = EvidencePatternNode("synthesis:s:1", "s", "Synthesis", "Integrated", "high")
    hypothesis = BiologicalHypothesisNode("hypothesis:h:1", "Hypothesis", "Explanation", "high")
    edges = (
        ReasoningEdge(hypothesis.id, synthesis.id, "supported_by"),
        ReasoningEdge(synthesis.id, finding.id, "composed_from"),
        ReasoningEdge(finding.id, observation.id, "derived_from"),
        ReasoningEdge(observation.id, measurement.id, "supported_by"),
    )
    candidate.analysis.reasoning_graph = ReasoningGraph(
        measurements=(measurement,), observations=(observation,),
        interpretive_findings=(finding,), evidence_patterns=(synthesis,),
        biological_hypotheses=(hypothesis,), edges=edges,
    )

    view = build_reasoning_graph_inspector_view(candidate)

    assert tuple(step.relationship for step in view.provenance_paths[0].steps) == (
        "", "supported by", "composed from", "derived from", "supported by",
    )
    payload = candidate.analysis.reasoning_graph.to_dict()
    assert payload["edges"] == [edge.to_dict() for edge in edges]

def test_graph_inspector_template_renders_typed_provenance_relationships():
    from pathlib import Path

    template = Path("segpick/reporting/templates/gene.html").read_text()

    assert "Typed hypothesis provenance" in template
    assert "graph-typed-path" in template
    assert "step.relationship" in template
    assert "step.node_type" in template
    assert "step.node_id" in template


def test_reasoning_graph_does_not_infer_missing_edges():
    from segpick.models import MeasurementNode, ObservationNode, ReasoningGraph

    measurement = MeasurementNode("measurement:m:1", "test", "metric", 1)
    observation = ObservationNode(
        "observation:o:1", "observed", "test", "Observed evidence"
    )
    graph = ReasoningGraph(measurements=(measurement,), observations=(observation,))

    assert graph.provenance_edges() == ()
    assert graph.to_dict()["edges"] == []


def test_graph_export_keeps_relationships_only_in_edges():
    from segpick.models import MeasurementNode, ObservationNode, ReasoningEdge, ReasoningGraph

    measurement = MeasurementNode("measurement:m:1", "test", "metric", 1)
    observation = ObservationNode("observation:o:1", "observed", "test", "Observed evidence")
    graph = ReasoningGraph(
        measurements=(measurement,),
        observations=(observation,),
        edges=(ReasoningEdge(observation.id, measurement.id, "supported_by"),),
    )

    payload = graph.to_dict()
    assert "measurement_ids" not in payload["observations"][0]
    assert payload["edges"] == [{
        "source_id": observation.id,
        "target_id": measurement.id,
        "relationship": "supported_by",
    }]
