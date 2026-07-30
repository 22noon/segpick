from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class ScenarioHypothesis:
    """A biological explanation aggregated from one or more matched scenarios."""

    hypothesis_id: str
    title: str
    category: str
    scope: str
    confidence: str
    severity: str
    explanation: str
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
            "candidate_ids", "supporting_scenarios", "supporting_scenario_titles",
            "conflicting_scenarios", "conflicting_scenario_titles",
            "recommended_actions", "references",
        ):
            data[key] = list(data[key])
        return data
