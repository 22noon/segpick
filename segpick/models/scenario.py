from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class EvidencePatternProvenance:
    """Trace one matched pattern condition back to observations or findings."""

    condition: str
    kind: str
    source: str | None = None
    descriptions: tuple[str, ...] = ()
    measurements: tuple[dict[str, Any], ...] = ()
    regions: tuple[dict[str, Any], ...] = ()
    visualisations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["descriptions"] = list(self.descriptions)
        data["measurements"] = [dict(item) for item in self.measurements]
        data["regions"] = [dict(item) for item in self.regions]
        data["visualisations"] = list(self.visualisations)
        return data


@dataclass(frozen=True, slots=True)
class EvidencePatternEvaluation:
    pattern_id: str
    title: str
    category: str
    scope: str
    confidence: str
    severity: str
    interpretation: str
    candidate_ids: tuple[str, ...] = ()
    matched_required: tuple[str, ...] = ()
    matched_supporting: tuple[str, ...] = ()
    matched_conflicting: tuple[str, ...] = ()
    suggested_actions: tuple[str, ...] = ()
    source: str = "builtin"
    references: tuple[str, ...] = ()
    evidence_provenance: tuple[EvidencePatternProvenance, ...] = ()
    state: str = "matched"
    missing_required: tuple[str, ...] = ()
    missing_supporting: tuple[str, ...] = ()
    unused_findings: tuple[str, ...] = ()

    @property
    def scenario_id(self) -> str:
        """Temporary compatibility accessor for pre-pattern consumers."""
        return self.pattern_id

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        for key in (
            "candidate_ids", "matched_required", "matched_supporting",
            "matched_conflicting", "suggested_actions", "references",
            "missing_required", "missing_supporting", "unused_findings",
        ):
            data[key] = list(data[key])
        data["evidence_provenance"] = [item.to_dict() for item in self.evidence_provenance]
        return data


# Temporary compatibility aliases during the analysis-layer migration.
ScenarioEvidenceProvenance = EvidencePatternProvenance
BiologicalScenario = EvidencePatternEvaluation
