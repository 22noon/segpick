from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HypothesisDefinition:
    """Immutable biological knowledge used to evaluate a final hypothesis."""

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


# Compatibility name retained for existing knowledge loaders and extensions.
HypothesisModule = HypothesisDefinition
