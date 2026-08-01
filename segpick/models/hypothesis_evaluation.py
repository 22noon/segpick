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
    supporting_patterns: tuple[str, ...] = ()
    supporting_pattern_titles: tuple[str, ...] = ()
    conflicting_patterns: tuple[str, ...] = ()
    conflicting_pattern_titles: tuple[str, ...] = ()
    recommended_actions: tuple[str, ...] = ()
    source: str = "builtin"
    references: tuple[str, ...] = ()

    @property
    def supporting_scenarios(self):
        return self.supporting_patterns

    @property
    def supporting_scenario_titles(self):
        return self.supporting_pattern_titles

    @property
    def conflicting_scenarios(self):
        return self.conflicting_patterns

    @property
    def conflicting_scenario_titles(self):
        return self.conflicting_pattern_titles

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        for key in (
            "definition_supported_by", "definition_contradicted_by",
            "candidate_ids", "supporting_patterns", "supporting_pattern_titles",
            "conflicting_patterns", "conflicting_pattern_titles",
            "recommended_actions", "references",
        ):
            data[key] = list(data[key])
        return data


# Compatibility name retained during the terminology migration.
ScenarioHypothesis = HypothesisEvaluation
