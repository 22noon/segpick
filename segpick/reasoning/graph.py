from __future__ import annotations

import re

from segpick.models import (
    BiologicalFinding,
    BiologicalHypothesis,
    EvidenceObservation,
    EvidencePatternEvaluation,
    HypothesisEvaluation,
)
from segpick.models.reasoning_graph import (
    BiologicalHypothesisNode,
    EvidencePatternNode,
    InterpretiveFindingNode,
    MeasurementNode,
    ObservationNode,
    ReasoningEdge,
    ReasoningGraph,
)


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "node"


def _observation_nodes(
    observations: tuple[EvidenceObservation, ...],
    measurements: tuple[MeasurementNode, ...] = (),
) -> tuple[tuple[ObservationNode, ...], tuple[ReasoningEdge, ...]]:
    counts: dict[str, int] = {}
    nodes = []
    measurements_by_channel: dict[str, tuple[str, ...]] = {}
    for measurement in measurements:
        measurements_by_channel.setdefault(measurement.channel, ())
        measurements_by_channel[measurement.channel] += (measurement.id,)
    for observation in observations:
        base = f"observation:{_slug(observation.source_name)}:{_slug(observation.observation_type)}"
        counts[base] = counts.get(base, 0) + 1
        measurement_ids = (
            measurements_by_channel.get(observation.source_name.removeprefix("plugin:"), ())
            if observation.source_name.startswith("plugin:")
            else ()
        )
        node = ObservationNode(
            id=f"{base}:{counts[base]}",
            observation_type=observation.observation_type,
            source=observation.source_name,
            description=observation.description,
            severity=observation.severity,
        )
        nodes.append((node, measurement_ids))
    node_tuple = tuple(node for node, _ in nodes)
    edges = tuple(
        ReasoningEdge(node.id, measurement_id, "supported_by")
        for node, measurement_ids in nodes
        for measurement_id in measurement_ids
    )
    return node_tuple, edges


def _interpretation_nodes(
    findings: tuple[BiologicalFinding, ...],
    observations: tuple[ObservationNode, ...],
) -> tuple[tuple[InterpretiveFindingNode, ...], tuple[ReasoningEdge, ...]]:
    by_source: dict[str, list[str]] = {}
    for node in observations:
        by_source.setdefault(node.source, []).append(node.id)
    nodes = []
    for index, finding in enumerate(findings, 1):
        linked = tuple(dict.fromkeys(node_id for source in finding.sources for node_id in by_source.get(source, ())))
        node = InterpretiveFindingNode(
            id=f"interpretation:{_slug(finding.title)}:{index}",
            title=finding.title,
            summary=finding.summary,
        )
        nodes.append((node, linked))
    node_tuple = tuple(node for node, _ in nodes)
    edges = tuple(
        ReasoningEdge(node.id, observation_id, "derived_from")
        for node, linked in nodes
        for observation_id in linked
    )
    return node_tuple, edges


def _condition_targets(label: str, observations: tuple[ObservationNode, ...], interpretations: tuple[InterpretiveFindingNode, ...]) -> tuple[str, ...]:
    kind, _, remainder = label.partition(":")
    value, _, source = remainder.partition("@")
    if kind == "observation":
        return tuple(node.id for node in observations if node.observation_type == value and (not source or node.source == source))
    return tuple(node.id for node in interpretations if node.title == value)


def _rule_finding_nodes(
    hypotheses: tuple[BiologicalHypothesis, ...],
    observations: tuple[ObservationNode, ...],
    interpretations: tuple[InterpretiveFindingNode, ...],
) -> tuple[tuple[InterpretiveFindingNode, ...], tuple[ReasoningEdge, ...]]:
    """Represent legacy rule-generated hypotheses as interpretive findings.

    These rules interpret local observations/findings; final biological
    hypotheses are reserved for explanations aggregated from evidence syntheses.
    """

    nodes = []
    for index, hypothesis in enumerate(hypotheses, 1):
        support_labels = hypothesis.matched_required + hypothesis.matched_supporting
        supporting = tuple(dict.fromkeys(
            node_id
            for label in support_labels
            for node_id in _condition_targets(label, observations, interpretations)
        ))
        conflicting = tuple(dict.fromkeys(
            node_id
            for label in hypothesis.matched_conflicting
            for node_id in _condition_targets(label, observations, interpretations)
        ))
        direct_observations = tuple(
            node_id for node_id in supporting if node_id.startswith("observation:")
        )
        node = InterpretiveFindingNode(
            id=f"finding:rule:{_slug(hypothesis.rule_id)}:{index}",
            title=hypothesis.title,
            summary=hypothesis.summary,
            source="rule",
            confidence=hypothesis.confidence,
            state=hypothesis.state,
            category=hypothesis.category,
            scope=hypothesis.scope,
            severity=hypothesis.severity,
            rule_id=hypothesis.rule_id,
            rule_source=hypothesis.rule_source,
            rule_description=hypothesis.rule_description,
            rule_references=hypothesis.rule_references,
        )
        nodes.append((node, supporting, conflicting, direct_observations))
    node_tuple = tuple(node for node, *_ in nodes)
    edges: list[ReasoningEdge] = []
    for node, supporting, conflicting, direct_observations in nodes:
        edges.extend(ReasoningEdge(node.id, target_id, "supported_by") for target_id in supporting)
        edges.extend(ReasoningEdge(node.id, target_id, "contradicted_by") for target_id in conflicting)
        linked = set(supporting) | set(conflicting)
        edges.extend(
            ReasoningEdge(node.id, observation_id, "derived_from")
            for observation_id in direct_observations
            if observation_id not in linked
        )
    return node_tuple, tuple(edges)


def _evidence_pattern_nodes(
    patterns: tuple[EvidencePatternEvaluation, ...],
    observations: tuple[ObservationNode, ...],
    interpretations: tuple[InterpretiveFindingNode, ...],
) -> tuple[tuple[EvidencePatternNode, ...], tuple[ReasoningEdge, ...]]:
    nodes = []
    for index, pattern in enumerate(patterns, 1):
        support_labels = pattern.matched_required + pattern.matched_supporting
        supporting = tuple(dict.fromkeys(
            node_id
            for label in support_labels
            for node_id in _condition_targets(label, observations, interpretations)
        ))
        conflicting = tuple(dict.fromkeys(
            node_id
            for label in pattern.matched_conflicting
            for node_id in _condition_targets(label, observations, interpretations)
        ))
        node = EvidencePatternNode(
            id=f"pattern:{_slug(pattern.pattern_id)}:{index}",
            pattern_id=pattern.pattern_id,
            title=pattern.title,
            interpretation=pattern.interpretation,
            confidence=pattern.confidence,
            category=pattern.category,
            scope=pattern.scope,
            severity=pattern.severity,
            source=pattern.source,
            references=pattern.references,
        )
        nodes.append((node, supporting, conflicting))
    node_tuple = tuple(node for node, *_ in nodes)
    edges: list[ReasoningEdge] = []
    for node, supporting, conflicting in nodes:
        edges.extend(ReasoningEdge(node.id, target_id, "composed_from") for target_id in supporting)
        edges.extend(ReasoningEdge(node.id, target_id, "conflicted_by") for target_id in conflicting)
    return node_tuple, tuple(edges)


def _biological_hypothesis_nodes(
    hypotheses: tuple[HypothesisEvaluation, ...],
    patterns: tuple[EvidencePatternNode, ...],
) -> tuple[tuple[BiologicalHypothesisNode, ...], tuple[ReasoningEdge, ...]]:
    pattern_by_id = {node.pattern_id: node.id for node in patterns}
    nodes = []
    for index, hypothesis in enumerate(hypotheses, 1):
        supporting = tuple(
            pattern_by_id[item]
            for item in hypothesis.supporting_patterns
            if item in pattern_by_id
        )
        conflicting = tuple(
            pattern_by_id[item]
            for item in hypothesis.conflicting_patterns
            if item in pattern_by_id
        )
        node = BiologicalHypothesisNode(
            id=f"hypothesis:evidence-pattern:{_slug(hypothesis.hypothesis_id)}:{index}",
            rule_id=hypothesis.hypothesis_id,
            title=hypothesis.title,
            summary=hypothesis.explanation,
            confidence=hypothesis.confidence,
            state="challenged" if conflicting else "supported",
            category=hypothesis.category,
            scope=hypothesis.scope,
            severity=hypothesis.severity,
            rule_source=hypothesis.source,
            rule_references=hypothesis.references,
            hypothesis_type="biological",
            definition_id=hypothesis.hypothesis_id,
            definition_base_confidence=hypothesis.base_confidence,
            definition_supported_by=hypothesis.definition_supported_by,
            definition_contradicted_by=hypothesis.definition_contradicted_by,
            definition_minimum_support=hypothesis.minimum_support,
            evaluation_candidate_ids=hypothesis.candidate_ids,
            evaluation_supporting_synthesis_ids=hypothesis.supporting_patterns,
            evaluation_conflicting_synthesis_ids=hypothesis.conflicting_patterns,
        )
        nodes.append((node, supporting, conflicting))
    node_tuple = tuple(node for node, *_ in nodes)
    edges: list[ReasoningEdge] = []
    for node, supporting, conflicting in nodes:
        edges.extend(ReasoningEdge(node.id, target_id, "supported_by") for target_id in supporting)
        edges.extend(ReasoningEdge(node.id, target_id, "contradicted_by") for target_id in conflicting)
    return node_tuple, tuple(edges)


def _scientific_conclusion_nodes(
    conclusions: tuple,
    hypotheses: tuple,
) -> tuple[tuple, tuple[ReasoningEdge, ...]]:

    """Build scientific conclusion nodes and their edges to supporting hypotheses."""

    from segpick.models.reasoning_graph import ScientificConclusionNode

    # Build lookup of hypothesis rule_id to node id
    hyp_by_rule_id = {h.rule_id: h.id for h in hypotheses}

    nodes = []
    edges = []

    for index, conclusion in enumerate(conclusions, 1):
        # Get the supporting hypothesis node IDs
        supporting_hyp_node_ids = tuple(
            hyp_by_rule_id.get(hid)
            for hid in conclusion.supporting_hypotheses
            if hid in hyp_by_rule_id
        )

        conflicting_hyp_node_ids = tuple(
            hyp_by_rule_id.get(hid)
            for hid in conclusion.conflicting_hypotheses
            if hid in hyp_by_rule_id
        )

        # Get generating relationship from conclusion evaluation
        generating_rel = getattr(conclusion, "generating_relationship", "")
        generating_hyps = getattr(conclusion, "generating_hypotheses", ())

        node = ScientificConclusionNode(
            id=f"conclusion:{conclusion.rule_id}:{index}",
            rule_id=conclusion.rule_id,
            title=conclusion.title,
            summary=conclusion.explanation,
            state=conclusion.state,
            confidence=conclusion.confidence,
            category=conclusion.category,
            scope=conclusion.scope,
            severity=conclusion.severity,
            rule_source=conclusion.source,
            rule_description=conclusion.explanation,
            rule_references=conclusion.references,
            conclusion_id=conclusion.conclusion_id,
            supporting_hypotheses=conclusion.supporting_hypotheses,
            conflicting_hypotheses=conclusion.conflicting_hypotheses,
            generating_relationship=generating_rel,
            generating_hypotheses=generating_hyps,
        )

        nodes.append((node, supporting_hyp_node_ids, conflicting_hyp_node_ids))

    node_tuple = tuple(node for node, *_ in nodes)

    for node, supporting, conflicting in nodes:
        # Add edges from conclusion to supporting hypotheses
        for target_id in supporting:
            edges.append(ReasoningEdge(node.id, target_id, "supported_by"))
        # Add edges from conclusion to conflicting hypotheses
        for target_id in conflicting:
            edges.append(ReasoningEdge(node.id, target_id, "contradicted_by"))

    return node_tuple, tuple(edges)




def build_reasoning_graph(candidate) -> ReasoningGraph:
    measurements = tuple(candidate.analysis.plugin_measurements)
    observation_nodes, observation_edges = _observation_nodes(
        candidate.analysis.observations, measurements
    )
    base_finding_nodes, base_finding_edges = _interpretation_nodes(
        candidate.analysis.findings, observation_nodes
    )
    rule_finding_nodes, rule_finding_edges = _rule_finding_nodes(
        candidate.analysis.hypotheses, observation_nodes, base_finding_nodes
    )
    interpretation_nodes = base_finding_nodes + rule_finding_nodes
    pattern_nodes, pattern_edges = _evidence_pattern_nodes(
        candidate.analysis.evidence_patterns, observation_nodes, interpretation_nodes
    )
    biological_hypothesis_nodes, hypothesis_edges = _biological_hypothesis_nodes(
        candidate.analysis.biological_hypothesis_evaluations, pattern_nodes
    )
    # Evaluate and add scientific conclusions
    from segpick.reasoning.conclusion_rules import evaluate_conclusions, load_active_conclusion_rules
    
    candidate_rules, gene_rules = load_active_conclusion_rules()
    all_rules = candidate_rules + gene_rules
    
    scientific_conclusions = evaluate_conclusions(
        all_rules,
        candidate.analysis.biological_hypothesis_evaluations,
        candidate_ids=(candidate.id,),
    )
    
    conclusion_nodes, conclusion_edges = _scientific_conclusion_nodes(
        scientific_conclusions, biological_hypothesis_nodes
    )
    
    graph = ReasoningGraph(
        measurements=measurements,
        observations=observation_nodes,
        interpretive_findings=interpretation_nodes,
        evidence_patterns=pattern_nodes,
        biological_hypotheses=biological_hypothesis_nodes,
        scientific_conclusions=conclusion_nodes,
        edges=(
            observation_edges
            + base_finding_edges
            + rule_finding_edges
            + pattern_edges
            + hypothesis_edges
            + conclusion_edges
        ),
    )
    graph.validate()
    return graph
