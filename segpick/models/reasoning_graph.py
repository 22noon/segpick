from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class MeasurementNode:
    id: str
    channel: str
    name: str
    value: Any
    unit: str | None = None
    provenance: str | None = None
    attributes: tuple[tuple[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["attributes"] = dict(self.attributes)
        return data


@dataclass(frozen=True, slots=True)
class ObservationNode:
    id: str
    observation_type: str
    source: str
    description: str
    measurement_ids: tuple[str, ...] = ()
    severity: str = "informational"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class InterpretiveFindingNode:
    id: str
    title: str
    summary: str
    observation_ids: tuple[str, ...] = ()
    supporting_ids: tuple[str, ...] = ()
    conflicting_ids: tuple[str, ...] = ()
    source: str = "finding"
    confidence: str = ""
    state: str = "provisional"
    category: str = ""
    scope: str = "candidate"
    severity: str = "informational"
    rule_id: str = ""
    rule_source: str = ""
    rule_description: str = ""
    rule_references: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# Backward-compatible alias during the terminology migration.
InterpretationNode = InterpretiveFindingNode


@dataclass(frozen=True, slots=True)
class EvidenceSynthesisNode:
    id: str
    scenario_id: str
    title: str
    interpretation: str
    confidence: str
    supporting_ids: tuple[str, ...] = ()
    conflicting_ids: tuple[str, ...] = ()
    category: str = ""
    scope: str = "candidate"
    severity: str = "informational"
    source: str = "builtin"
    references: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# Backward-compatible alias during the terminology migration.
ScenarioNode = EvidenceSynthesisNode


@dataclass(frozen=True, slots=True)
class BiologicalHypothesisNode:
    id: str
    title: str
    summary: str
    confidence: str
    supporting_ids: tuple[str, ...] = ()
    conflicting_ids: tuple[str, ...] = ()
    rule_id: str = ""
    state: str = "provisional"
    category: str = ""
    scope: str = "candidate"
    severity: str = "informational"
    rule_source: str = ""
    rule_description: str = ""
    rule_references: tuple[str, ...] = ()
    hypothesis_type: str = "biological"
    definition_id: str = ""
    definition_base_confidence: str = ""
    definition_supported_by: tuple[str, ...] = ()
    definition_contradicted_by: tuple[str, ...] = ()
    definition_minimum_support: int = 1
    evaluation_candidate_ids: tuple[str, ...] = ()
    evaluation_supporting_synthesis_ids: tuple[str, ...] = ()
    evaluation_conflicting_synthesis_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["definition"] = {
            "hypothesis_id": self.definition_id or self.rule_id,
            "base_confidence": self.definition_base_confidence,
            "supported_by": list(self.definition_supported_by),
            "contradicted_by": list(self.definition_contradicted_by),
            "minimum_support": self.definition_minimum_support,
            "source": self.rule_source,
            "description": self.rule_description,
            "references": list(self.rule_references),
        }
        data["evaluation"] = {
            "candidate_ids": list(self.evaluation_candidate_ids),
            "confidence": self.confidence,
            "state": self.state,
            "supporting_synthesis_ids": list(self.evaluation_supporting_synthesis_ids),
            "conflicting_synthesis_ids": list(self.evaluation_conflicting_synthesis_ids),
            "supporting_node_ids": list(self.supporting_ids),
            "conflicting_node_ids": list(self.conflicting_ids),
        }
        return data


# Backward-compatible alias during the final hypothesis-layer migration.
HypothesisNode = BiologicalHypothesisNode


@dataclass(frozen=True, slots=True)
class ReasoningEdge:
    source_id: str
    target_id: str
    relationship: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ReasoningGraph:
    measurements: tuple[MeasurementNode, ...] = ()
    observations: tuple[ObservationNode, ...] = ()
    interpretive_findings: tuple[InterpretiveFindingNode, ...] = ()
    evidence_syntheses: tuple[EvidenceSynthesisNode, ...] = ()
    biological_hypotheses: tuple[BiologicalHypothesisNode, ...] = ()
    edges: tuple[ReasoningEdge, ...] = ()

    SCHEMA_VERSION = "3.0"

    @property
    def interpretations(self) -> tuple[InterpretiveFindingNode, ...]:
        """Backward-compatible alias for ``interpretive_findings``."""
        return self.interpretive_findings

    @property
    def scenarios(self) -> tuple[EvidenceSynthesisNode, ...]:
        """Backward-compatible alias for ``evidence_syntheses``."""
        return self.evidence_syntheses

    @property
    def hypotheses(self) -> tuple[BiologicalHypothesisNode, ...]:
        """Backward-compatible alias for ``biological_hypotheses``."""
        return self.biological_hypotheses

    def provenance_edges(self) -> tuple[ReasoningEdge, ...]:
        """Return explicit edges, deriving them for schema-2.0 graphs if needed."""
        if self.edges:
            return self.edges
        edges: list[ReasoningEdge] = []
        for observation in self.observations:
            edges.extend(ReasoningEdge(observation.id, node_id, "supported_by") for node_id in observation.measurement_ids)
        for finding in self.interpretive_findings:
            edges.extend(ReasoningEdge(finding.id, node_id, "supported_by") for node_id in finding.supporting_ids)
            edges.extend(ReasoningEdge(finding.id, node_id, "contradicted_by") for node_id in finding.conflicting_ids)
            linked = set(finding.supporting_ids) | set(finding.conflicting_ids)
            edges.extend(ReasoningEdge(finding.id, node_id, "derived_from") for node_id in finding.observation_ids if node_id not in linked)
        for synthesis in self.evidence_syntheses:
            edges.extend(ReasoningEdge(synthesis.id, node_id, "composed_from") for node_id in synthesis.supporting_ids)
            edges.extend(ReasoningEdge(synthesis.id, node_id, "conflicted_by") for node_id in synthesis.conflicting_ids)
        for hypothesis in self.biological_hypotheses:
            edges.extend(ReasoningEdge(hypothesis.id, node_id, "supported_by") for node_id in hypothesis.supporting_ids)
            edges.extend(ReasoningEdge(hypothesis.id, node_id, "contradicted_by") for node_id in hypothesis.conflicting_ids)
        return tuple(edges)

    def validate(self) -> None:
        measurement_ids = {item.id for item in self.measurements}
        observation_ids = {item.id for item in self.observations}
        finding_ids = {item.id for item in self.interpretive_findings}
        synthesis_ids = {item.id for item in self.evidence_syntheses}
        hypothesis_ids = {item.id for item in self.biological_hypotheses}
        all_ids = measurement_ids | observation_ids | finding_ids | synthesis_ids | hypothesis_ids
        expected = sum(map(len, (measurement_ids, observation_ids, finding_ids, synthesis_ids, hypothesis_ids)))
        if len(all_ids) != expected:
            raise ValueError("Reasoning graph node IDs must be globally unique")
        for item in self.observations:
            missing = set(item.measurement_ids) - measurement_ids
            if missing:
                raise ValueError(f"Observation {item.id} references missing measurements: {sorted(missing)}")
        for item in self.interpretive_findings:
            missing_observations = set(item.observation_ids) - observation_ids
            if missing_observations:
                raise ValueError(
                    f"Interpretive finding {item.id} references missing observations: "
                    f"{sorted(missing_observations)}"
                )
            allowed_evidence_ids = observation_ids | (finding_ids - {item.id})
            missing_evidence = (set(item.supporting_ids) | set(item.conflicting_ids)) - allowed_evidence_ids
            if missing_evidence:
                raise ValueError(
                    f"Interpretive finding {item.id} references missing evidence nodes: "
                    f"{sorted(missing_evidence)}"
                )
        lower_ids = observation_ids | finding_ids
        for item in self.evidence_syntheses:
            missing = (set(item.supporting_ids) | set(item.conflicting_ids)) - lower_ids
            if missing:
                raise ValueError(f"Evidence synthesis {item.id} references missing evidence nodes: {sorted(missing)}")
        hypothesis_evidence_ids = lower_ids | synthesis_ids
        for item in self.biological_hypotheses:
            missing = (set(item.supporting_ids) | set(item.conflicting_ids)) - hypothesis_evidence_ids
            if missing:
                raise ValueError(f"Hypothesis {item.id} references missing evidence nodes: {sorted(missing)}")
        edge_keys: set[tuple[str, str, str]] = set()
        allowed_relationships = {
            "supported_by", "contradicted_by", "composed_from",
            "conflicted_by", "derived_from",
        }
        for edge in self.provenance_edges():
            if edge.source_id not in all_ids or edge.target_id not in all_ids:
                raise ValueError(
                    f"Reasoning edge references missing node: "
                    f"{edge.source_id} -[{edge.relationship}]-> {edge.target_id}"
                )
            if edge.relationship not in allowed_relationships:
                raise ValueError(f"Unsupported reasoning edge relationship: {edge.relationship}")
            key = (edge.source_id, edge.target_id, edge.relationship)
            if key in edge_keys:
                raise ValueError(f"Duplicate reasoning edge: {key}")
            edge_keys.add(key)

    def _canonical_payload(self) -> dict[str, Any]:
        return {
            "measurements": [item.to_dict() for item in self.measurements],
            "observations": [item.to_dict() for item in self.observations],
            "interpretive_findings": [item.to_dict() for item in self.interpretive_findings],
            "evidence_syntheses": [item.to_dict() for item in self.evidence_syntheses],
            "biological_hypotheses": [item.to_dict() for item in self.biological_hypotheses],
            "edges": [item.to_dict() for item in self.provenance_edges()],
        }

    def to_dict(self) -> dict[str, Any]:
        """Serialize the canonical reasoning graph schema.

        Graph exports intentionally provide one current contract only. The
        export contains the scientific collection names and explicit typed
        provenance edges; legacy collection aliases and historical schema
        variants are not emitted.
        """
        self.validate()
        return {"schema_version": self.SCHEMA_VERSION, **self._canonical_payload()}

