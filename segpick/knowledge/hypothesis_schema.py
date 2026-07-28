from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HypothesisModule:
    hypothesis_id: str
    title: str
    category: str
    scope: str
    severity: str
    base_confidence: str
    explanation: str
    supported_by: tuple[str, ...]
    contradicted_by: tuple[str, ...] = ()
    minimum_support: int = 1
    recommended_actions: tuple[str, ...] = ()
    references: tuple[str, ...] = ()
    source: str = "builtin"
