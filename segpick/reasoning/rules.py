from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from segpick.models import BiologicalFinding, EvidenceObservation

ConditionKind = Literal["observation", "finding"]


@dataclass(frozen=True, slots=True)
class RuleCondition:
    """One factual condition used by a hypothesis rule."""

    kind: ConditionKind
    value: str
    source: str | None = None

    @property
    def label(self) -> str:
        if self.source is None:
            return f"{self.kind}:{self.value}"
        return f"{self.kind}:{self.value}@{self.source}"

    def matches(
        self,
        observations: tuple[EvidenceObservation, ...],
        findings: tuple[BiologicalFinding, ...],
    ) -> bool:
        if self.kind == "observation":
            return any(
                item.observation_type == self.value
                and (self.source is None or item.source.value == self.source)
                for item in observations
            )
        return any(
            item.title == self.value
            and (self.source is None or self.source in item.sources)
            for item in findings
        )


@dataclass(frozen=True, slots=True)
class HypothesisRule:
    """Declarative rule for creating one biological hypothesis."""

    rule_id: str
    title: str
    category: str
    scope: str
    severity: str
    base_confidence: str
    summary: str
    requires: tuple[RuleCondition, ...]
    description: str = ""
    references: tuple[str, ...] = ()
    source: str = "python"
    supports: tuple[RuleCondition, ...] = ()
    conflicts: tuple[RuleCondition, ...] = ()
