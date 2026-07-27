from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class BiologicalScenario:
    scenario_id: str
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

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        for key in (
            "candidate_ids", "matched_required", "matched_supporting",
            "matched_conflicting", "suggested_actions", "references",
        ):
            data[key] = list(data[key])
        return data
