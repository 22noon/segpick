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
    severity: str = "informational"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class InterpretiveFindingNode:
    id: str
    title: str
    summary: str
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


@dataclass(frozen=True, slots=True)
class EvidencePatternNode:
    id: str
    pattern_id: str
    title: str
    interpretation: str
    confidence: str
    category: str = ""
    scope: str = "candidate"
    severity: str = "informational"
    source: str = "builtin"
    references: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class BiologicalHypothesisNode:
    id: str
    title: str
    summary: str
    confidence: str
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
        }
        return data


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
    evidence_patterns: tuple[EvidencePatternNode, ...] = ()
    biological_hypotheses: tuple[BiologicalHypothesisNode, ...] = ()
    edges: tuple[ReasoningEdge, ...] = ()

    SCHEMA_VERSION = "4.0"

    def provenance_edges(self) -> tuple[ReasoningEdge, ...]:
        """Return the graph's explicit immutable provenance edges."""
        return self.edges

    def validate(self) -> None:
        node_groups = {
            "measurement": self.measurements,
            "observation": self.observations,
            "interpretive_finding": self.interpretive_findings,
            "evidence_synthesis": self.evidence_patterns,
            "biological_hypothesis": self.biological_hypotheses,
        }
        node_types = {item.id: node_type for node_type, items in node_groups.items() for item in items}
        expected = sum(len(items) for items in node_groups.values())
        if len(node_types) != expected:
            raise ValueError("Reasoning graph node IDs must be globally unique")

        allowed_transitions = {
            ("observation", "measurement", "supported_by"),
            ("interpretive_finding", "observation", "derived_from"),
            ("interpretive_finding", "observation", "supported_by"),
            ("interpretive_finding", "observation", "contradicted_by"),
            ("interpretive_finding", "interpretive_finding", "supported_by"),
            ("interpretive_finding", "interpretive_finding", "contradicted_by"),
            ("evidence_synthesis", "observation", "composed_from"),
            ("evidence_synthesis", "interpretive_finding", "composed_from"),
            ("evidence_synthesis", "observation", "conflicted_by"),
            ("evidence_synthesis", "interpretive_finding", "conflicted_by"),
            ("biological_hypothesis", "evidence_synthesis", "supported_by"),
            ("biological_hypothesis", "evidence_synthesis", "contradicted_by"),
        }
        edge_keys: set[tuple[str, str, str]] = set()
        for edge in self.edges:
            source_type = node_types.get(edge.source_id)
            target_type = node_types.get(edge.target_id)
            if source_type is None or target_type is None:
                raise ValueError(
                    "Reasoning edge references missing node: "
                    f"{edge.source_id} -[{edge.relationship}]-> {edge.target_id}"
                )
            transition = (source_type, target_type, edge.relationship)
            if transition not in allowed_transitions:
                raise ValueError(
                    "Unsupported reasoning edge transition: "
                    f"{source_type} -[{edge.relationship}]-> {target_type}"
                )
            key = (edge.source_id, edge.target_id, edge.relationship)
            if key in edge_keys:
                raise ValueError(f"Duplicate reasoning edge: {key}")
            edge_keys.add(key)

    def _canonical_payload(self) -> dict[str, Any]:
        return {
            "measurements": [item.to_dict() for item in self.measurements],
            "observations": [item.to_dict() for item in self.observations],
            "interpretive_findings": [item.to_dict() for item in self.interpretive_findings],
            "evidence_patterns": [item.to_dict() for item in self.evidence_patterns],
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

