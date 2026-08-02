"""
Reasoning provenance.

A Provenance object is the minimal immutable justification graph for a
single reasoning claim. It is the canonical intermediate representation
returned by reasoning queries and consumed by higher-level projectors.

This class intentionally contains no traversal, rendering or interpretation
logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Provenance:
    """Minimal immutable justification graph for a single claim."""

    claim: Any
    nodes: tuple[Any, ...]
    edges: tuple[Any, ...]
