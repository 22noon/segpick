"""Explain recommendation builder skeleton."""
from ..explorer import ReasoningExplorer

class ExplainRecommendationBuilder:
    def __init__(self, explorer: ReasoningExplorer):
        self.explorer = explorer

    def build(self, candidate_id:str):
        raise NotImplementedError("Implemented in later phase")
