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
class InterpretationNode:
    id: str
    title: str
    summary: str
    observation_ids: tuple[str, ...] = ()
    source: str = "finding"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ScenarioNode:
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


@dataclass(frozen=True, slots=True)
class HypothesisNode:
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
    hypothesis_type: str = "rule"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ReasoningGraph:
    measurements: tuple[MeasurementNode, ...] = ()
    observations: tuple[ObservationNode, ...] = ()
    interpretations: tuple[InterpretationNode, ...] = ()
    scenarios: tuple[ScenarioNode, ...] = ()
    hypotheses: tuple[HypothesisNode, ...] = ()

    def validate(self) -> None:
        measurement_ids = {item.id for item in self.measurements}
        observation_ids = {item.id for item in self.observations}
        interpretation_ids = {item.id for item in self.interpretations}
        scenario_ids = {item.id for item in self.scenarios}
        hypothesis_ids = {item.id for item in self.hypotheses}
        all_ids = measurement_ids | observation_ids | interpretation_ids | scenario_ids | hypothesis_ids
        expected = sum(map(len, (measurement_ids, observation_ids, interpretation_ids, scenario_ids, hypothesis_ids)))
        if len(all_ids) != expected:
            raise ValueError("Reasoning graph node IDs must be globally unique")
        for item in self.observations:
            missing = set(item.measurement_ids) - measurement_ids
            if missing:
                raise ValueError(f"Observation {item.id} references missing measurements: {sorted(missing)}")
        for item in self.interpretations:
            missing = set(item.observation_ids) - observation_ids
            if missing:
                raise ValueError(f"Interpretation {item.id} references missing observations: {sorted(missing)}")
        lower_ids = observation_ids | interpretation_ids
        for item in self.scenarios:
            missing = (set(item.supporting_ids) | set(item.conflicting_ids)) - lower_ids
            if missing:
                raise ValueError(f"Scenario {item.id} references missing evidence nodes: {sorted(missing)}")
        hypothesis_evidence_ids = lower_ids | scenario_ids
        for item in self.hypotheses:
            missing = (set(item.supporting_ids) | set(item.conflicting_ids)) - hypothesis_evidence_ids
            if missing:
                raise ValueError(f"Hypothesis {item.id} references missing evidence nodes: {sorted(missing)}")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "measurements": [item.to_dict() for item in self.measurements],
            "observations": [item.to_dict() for item in self.observations],
            "interpretations": [item.to_dict() for item in self.interpretations],
            "scenarios": [item.to_dict() for item in self.scenarios],
            "hypotheses": [item.to_dict() for item in self.hypotheses],
        }
