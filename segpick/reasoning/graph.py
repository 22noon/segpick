from __future__ import annotations

import re
from typing import Iterable

from segpick.models import BiologicalFinding, BiologicalHypothesis, EvidenceObservation
from segpick.models.reasoning_graph import (
    HypothesisNode,
    InterpretationNode,
    MeasurementNode,
    ObservationNode,
    ReasoningGraph,
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


def _interpretation_nodes(findings: tuple[BiologicalFinding, ...], observations: tuple[ObservationNode, ...]) -> tuple[InterpretationNode, ...]:
    by_source: dict[str, list[str]] = {}
    for node in observations:
        by_source.setdefault(node.source, []).append(node.id)
    nodes = []
    for index, finding in enumerate(findings, 1):
        linked = tuple(dict.fromkeys(node_id for source in finding.sources for node_id in by_source.get(source, ())))
        nodes.append(InterpretationNode(
            id=f"interpretation:{_slug(finding.title)}:{index}",
            title=finding.title,
            summary=finding.summary,
            observation_ids=linked,
        ))
    return tuple(nodes)


def _condition_targets(label: str, observations: tuple[ObservationNode, ...], interpretations: tuple[InterpretationNode, ...]) -> tuple[str, ...]:
    kind, _, remainder = label.partition(":")
    value, _, source = remainder.partition("@")
    if kind == "observation":
        return tuple(node.id for node in observations if node.observation_type == value and (not source or node.source == source))
    return tuple(node.id for node in interpretations if node.title == value)


def _hypothesis_nodes(hypotheses: tuple[BiologicalHypothesis, ...], observations: tuple[ObservationNode, ...], interpretations: tuple[InterpretationNode, ...]) -> tuple[HypothesisNode, ...]:
    nodes = []
    for index, hypothesis in enumerate(hypotheses, 1):
        support_labels = hypothesis.matched_required + hypothesis.matched_supporting
        supporting = tuple(dict.fromkeys(node_id for label in support_labels for node_id in _condition_targets(label, observations, interpretations)))
        conflicting = tuple(dict.fromkeys(node_id for label in hypothesis.matched_conflicting for node_id in _condition_targets(label, observations, interpretations)))
        nodes.append(HypothesisNode(
            id=f"hypothesis:{_slug(hypothesis.rule_id)}:{index}",
            rule_id=hypothesis.rule_id,
            title=hypothesis.title,
            summary=hypothesis.summary,
            confidence=hypothesis.confidence,
            supporting_ids=supporting,
            conflicting_ids=conflicting,
            state=hypothesis.state,
        ))
    return tuple(nodes)


def build_reasoning_graph(candidate) -> ReasoningGraph:
    measurements = tuple(candidate.analysis.plugin_measurements)
    observation_nodes = _observation_nodes(candidate.analysis.observations, measurements)
    interpretation_nodes = _interpretation_nodes(candidate.analysis.findings, observation_nodes)
    hypothesis_nodes = _hypothesis_nodes(candidate.analysis.hypotheses, observation_nodes, interpretation_nodes)
    graph = ReasoningGraph(
        measurements=measurements,
        observations=observation_nodes,
        interpretations=interpretation_nodes,
        hypotheses=hypothesis_nodes,
    )
    graph.validate()
    return graph
