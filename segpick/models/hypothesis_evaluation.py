from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class HypothesisEvaluation:
    """Candidate- or gene-specific evaluation of a biological hypothesis definition."""

    hypothesis_id: str
    title: str
    category: str
    scope: str
    confidence: str
    severity: str
    explanation: str
    base_confidence: str = ""
    definition_supported_by: tuple[str, ...] = ()
    definition_contradicted_by: tuple[str, ...] = ()
    minimum_support: int = 1
    candidate_ids: tuple[str, ...] = ()
    supporting_scenarios: tuple[str, ...] = ()
    supporting_scenario_titles: tuple[str, ...] = ()
    conflicting_scenarios: tuple[str, ...] = ()
    conflicting_scenario_titles: tuple[str, ...] = ()
    recommended_actions: tuple[str, ...] = ()
    source: str = "builtin"
    references: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        for key in (
            "definition_supported_by", "definition_contradicted_by",
            "candidate_ids", "supporting_scenarios", "supporting_scenario_titles",
            "conflicting_scenarios", "conflicting_scenario_titles",
            "recommended_actions", "references",
        ):
            data[key] = list(data[key])
        return data


# Compatibility name retained during the terminology migration.
ScenarioHypothesis = HypothesisEvaluation
