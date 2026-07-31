from __future__ import annotations

import re
from typing import Iterable

from segpick.models import (
    BiologicalFinding, BiologicalHypothesis, BiologicalScenario,
    EvidenceObservation, ScenarioHypothesis,
)
from segpick.models.reasoning_graph import (
    BiologicalHypothesisNode,
    InterpretiveFindingNode,
    MeasurementNode,
    ObservationNode,
    ReasoningGraph,
    EvidenceSynthesisNode,
)


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "node"


def _observation_nodes(
    observations: tuple[EvidenceObservation, ...],
    measurements: tuple[MeasurementNode, ...] = (),
) -> tuple[ObservationNode, ...]:
    counts: dict[str, int] = {}
    nodes = []
    measurements_by_channel: dict[str, tuple[str, ...]] = {}
    for measurement in measurements:
        measurements_by_channel.setdefault(measurement.channel, ())
        measurements_by_channel[measurement.channel] += (measurement.id,)
    for observation in observations:
        base = f"observation:{_slug(observation.source_name)}:{_slug(observation.observation_type)}"
        counts[base] = counts.get(base, 0) + 1
        nodes.append(ObservationNode(
            id=f"{base}:{counts[base]}",
            observation_type=observation.observation_type,
            source=observation.source_name,
            description=observation.description,
            measurement_ids=measurements_by_channel.get(
                observation.source_name.removeprefix("plugin:"), ()
            ) if observation.source_name.startswith("plugin:") else (),
            severity=observation.severity,
        ))
    return tuple(nodes)


def _interpretation_nodes(findings: tuple[BiologicalFinding, ...], observations: tuple[ObservationNode, ...]) -> tuple[InterpretiveFindingNode, ...]:
    by_source: dict[str, list[str]] = {}
    for node in observations:
        by_source.setdefault(node.source, []).append(node.id)
    nodes = []
    for index, finding in enumerate(findings, 1):
        linked = tuple(dict.fromkeys(node_id for source in finding.sources for node_id in by_source.get(source, ())))
        nodes.append(InterpretiveFindingNode(
            id=f"interpretation:{_slug(finding.title)}:{index}",
            title=finding.title,
            summary=finding.summary,
            observation_ids=linked,
        ))
    return tuple(nodes)


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
) -> tuple[InterpretiveFindingNode, ...]:
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
        nodes.append(InterpretiveFindingNode(
            id=f"finding:rule:{_slug(hypothesis.rule_id)}:{index}",
            title=hypothesis.title,
            summary=hypothesis.summary,
            observation_ids=direct_observations,
            supporting_ids=supporting,
            conflicting_ids=conflicting,
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
        ))
    return tuple(nodes)


def _scenario_nodes(
    scenarios: tuple[BiologicalScenario, ...],
    observations: tuple[ObservationNode, ...],
    interpretations: tuple[InterpretiveFindingNode, ...],
) -> tuple[EvidenceSynthesisNode, ...]:
    nodes = []
    for index, scenario in enumerate(scenarios, 1):
        support_labels = scenario.matched_required + scenario.matched_supporting
        supporting = tuple(dict.fromkeys(
            node_id
            for label in support_labels
            for node_id in _condition_targets(label, observations, interpretations)
        ))
        conflicting = tuple(dict.fromkeys(
            node_id
            for label in scenario.matched_conflicting
            for node_id in _condition_targets(label, observations, interpretations)
        ))
        nodes.append(EvidenceSynthesisNode(
            id=f"scenario:{_slug(scenario.scenario_id)}:{index}",
            scenario_id=scenario.scenario_id,
            title=scenario.title,
            interpretation=scenario.interpretation,
            confidence=scenario.confidence,
            supporting_ids=supporting,
            conflicting_ids=conflicting,
            category=scenario.category,
            scope=scenario.scope,
            severity=scenario.severity,
            source=scenario.source,
            references=scenario.references,
        ))
    return tuple(nodes)


def _scenario_hypothesis_nodes(
    hypotheses: tuple[ScenarioHypothesis, ...],
    scenarios: tuple[EvidenceSynthesisNode, ...],
) -> tuple[BiologicalHypothesisNode, ...]:
    scenario_by_rule_id = {node.scenario_id: node.id for node in scenarios}
    nodes = []
    for index, hypothesis in enumerate(hypotheses, 1):
        supporting = tuple(
            scenario_by_rule_id[item]
            for item in hypothesis.supporting_scenarios
            if item in scenario_by_rule_id
        )
        conflicting = tuple(
            scenario_by_rule_id[item]
            for item in hypothesis.conflicting_scenarios
            if item in scenario_by_rule_id
        )
        nodes.append(BiologicalHypothesisNode(
            id=f"hypothesis:scenario:{_slug(hypothesis.hypothesis_id)}:{index}",
            rule_id=hypothesis.hypothesis_id,
            title=hypothesis.title,
            summary=hypothesis.explanation,
            confidence=hypothesis.confidence,
            supporting_ids=supporting,
            conflicting_ids=conflicting,
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
            evaluation_supporting_synthesis_ids=hypothesis.supporting_scenarios,
            evaluation_conflicting_synthesis_ids=hypothesis.conflicting_scenarios,
        ))
    return tuple(nodes)


def build_reasoning_graph(candidate) -> ReasoningGraph:
    measurements = tuple(candidate.analysis.plugin_measurements)
    observation_nodes = _observation_nodes(candidate.analysis.observations, measurements)
    base_finding_nodes = _interpretation_nodes(candidate.analysis.findings, observation_nodes)
    rule_finding_nodes = _rule_finding_nodes(
        candidate.analysis.hypotheses, observation_nodes, base_finding_nodes
    )
    interpretation_nodes = base_finding_nodes + rule_finding_nodes
    scenario_nodes = _scenario_nodes(
        candidate.analysis.scenarios, observation_nodes, interpretation_nodes
    )
    scenario_hypothesis_nodes = _scenario_hypothesis_nodes(
        candidate.analysis.scenario_hypotheses, scenario_nodes
    )
    graph = ReasoningGraph(
        measurements=measurements,
        observations=observation_nodes,
        interpretive_findings=interpretation_nodes,
        evidence_syntheses=scenario_nodes,
        biological_hypotheses=scenario_hypothesis_nodes,
    )
    graph.validate()
    return graph
