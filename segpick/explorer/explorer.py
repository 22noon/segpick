"""
Reasoning Explorer service.

This is the stable façade between consumers and the internal reasoning graph.

The implementation is intentionally deferred. Subsequent pull requests will
delegate these methods to provenance queries and project the results into
scientific arguments.
"""

from __future__ import annotations


class ReasoningExplorer:
    """Public service for interrogating the reasoning graph."""

    def __init__(self, graph):
        self._graph = graph

    def explain(self, node):
        """Return the scientific justification for a reasoning node."""
        raise NotImplementedError("Implemented in PR003.")

    def compare(self, *nodes):
        """Compare reasoning supporting multiple nodes."""
        raise NotImplementedError("Implemented in a later PR.")

    def impact(self, node):
        """Return downstream consequences of a reasoning node."""
        raise NotImplementedError("Implemented in a later PR.")

    def next_evidence(self, node):
        """Return evidence that would most reduce uncertainty."""
        raise NotImplementedError("Implemented in a later PR.")
