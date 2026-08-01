"""Read-only reasoning explorer.

This module defines the public API for traversing the immutable reasoning
graph in scientific terms. Methods are intentionally skeletal in this phase.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class ReasoningExplorer:
    graph: object

    def recommendation(self, candidate_id:str):
        raise NotImplementedError

    def primary_claim(self, recommendation):
        raise NotImplementedError

    def competing_claims(self, recommendation):
        raise NotImplementedError
