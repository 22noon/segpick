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

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# Backward-compatible alias during the final hypothesis-layer migration.
HypothesisNode = BiologicalHypothesisNode


@dataclass(frozen=True, slots=True)
class ReasoningGraph:
    measurements: tuple[MeasurementNode, ...] = ()
    observations: tuple[ObservationNode, ...] = ()
    interpretive_findings: tuple[InterpretiveFindingNode, ...] = ()
    evidence_syntheses: tuple[EvidenceSynthesisNode, ...] = ()
    biological_hypotheses: tuple[BiologicalHypothesisNode, ...] = ()

    SCHEMA_VERSION = "2.0"
    LEGACY_SCHEMA_VERSION = "1.0"

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

    def _canonical_payload(self) -> dict[str, Any]:
        return {
            "measurements": [item.to_dict() for item in self.measurements],
            "observations": [item.to_dict() for item in self.observations],
            "interpretive_findings": [item.to_dict() for item in self.interpretive_findings],
            "evidence_syntheses": [item.to_dict() for item in self.evidence_syntheses],
            "biological_hypotheses": [item.to_dict() for item in self.biological_hypotheses],
        }

    def to_dict(
        self,
        *,
        schema_version: str = SCHEMA_VERSION,
        include_legacy_aliases: bool = True,
    ) -> dict[str, Any]:
        """Serialize the graph using a versioned compatibility schema.

        Schema 2 uses the canonical scientific terminology. During migration,
        legacy aliases are included by default so existing consumers of
        ``interpretations``, ``scenarios`` and ``hypotheses`` continue to work.
        Pass ``include_legacy_aliases=False`` for a canonical-only payload.
        Schema 1 returns only the legacy collection names.
        """
        self.validate()
        canonical = self._canonical_payload()
        if schema_version in {"1", self.LEGACY_SCHEMA_VERSION}:
            return {
                "schema_version": self.LEGACY_SCHEMA_VERSION,
                "measurements": canonical["measurements"],
                "observations": canonical["observations"],
                "interpretations": canonical["interpretive_findings"],
                "scenarios": canonical["evidence_syntheses"],
                "hypotheses": canonical["biological_hypotheses"],
            }
        if schema_version not in {"2", self.SCHEMA_VERSION}:
            raise ValueError(f"Unsupported reasoning graph schema version: {schema_version}")
        payload = {"schema_version": self.SCHEMA_VERSION, **canonical}
        if include_legacy_aliases:
            payload.update({
                "interpretations": canonical["interpretive_findings"],
                "scenarios": canonical["evidence_syntheses"],
                "hypotheses": canonical["biological_hypotheses"],
            })
        return payload

    def to_legacy_dict(self) -> dict[str, Any]:
        """Return the explicit schema-v1 compatibility representation."""
        return self.to_dict(schema_version=self.LEGACY_SCHEMA_VERSION)

