from __future__ import annotations
from dataclasses import dataclass
from segpick.reasoning.rules import RuleCondition

@dataclass(frozen=True, slots=True)
class KnowledgeModule:
    scenario_id: str
    title: str
    category: str
    scope: str
    severity: str
    base_confidence: str
    interpretation: str
    requires: tuple[RuleCondition, ...]
    supports: tuple[RuleCondition, ...] = ()
    conflicts: tuple[RuleCondition, ...] = ()
    suggested_actions: tuple[str, ...] = ()
    references: tuple[str, ...] = ()
    source: str = "builtin"
