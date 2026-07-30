from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class RuleEvaluation:
    """Diagnostic evaluation of one hypothesis rule against available evidence."""

    rule_id: str
    title: str
    scope: str
    triggered: bool
    confidence: str | None
    severity: str
    rule_source: str
    rule_description: str = ""
    rule_references: tuple[str, ...] = ()
    matched_required: tuple[str, ...] = ()
    missing_required: tuple[str, ...] = ()
    matched_supporting: tuple[str, ...] = ()
    missing_supporting: tuple[str, ...] = ()
    matched_conflicting: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        for field_name in (
            "rule_references",
            "matched_required",
            "missing_required",
            "matched_supporting",
            "missing_supporting",
            "matched_conflicting",
        ):
            data[field_name] = list(data[field_name])
        return data
