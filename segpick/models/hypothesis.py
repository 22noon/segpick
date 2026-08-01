from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class BiologicalHypothesis:
    """A traceable biological explanation supported by rules."""

    rule_id: str
    title: str
    category: str
    scope: str
    confidence: str
    severity: str
    summary: str
    candidate_ids: tuple[str, ...] = ()
    matched_required: tuple[str, ...] = ()
    matched_supporting: tuple[str, ...] = ()
    matched_conflicting: tuple[str, ...] = ()
    rule_source: str = "python"
    rule_description: str = ""
    rule_references: tuple[str, ...] = ()
    state: str = "provisional"

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["candidate_ids"] = list(self.candidate_ids)
        data["matched_required"] = list(self.matched_required)
        data["matched_supporting"] = list(self.matched_supporting)
        data["matched_conflicting"] = list(self.matched_conflicting)
        data["rule_references"] = list(self.rule_references)
        return data
