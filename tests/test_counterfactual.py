"""
Tests for query-time counterfactual evaluation.
"""

from __future__ import annotations

import pytest
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from segpick.explorer.counterfactual import evaluate_counterfactual
from segpick.models import (
    CandidateContig,
    ContigAnalysis,
    ContigMetadata,
)
from segpick.models.reasoning_graph import ReasoningGraph


def test_counterfactual_invalid_node_id():
    """Test that unknown node IDs raise KeyError."""
    candidate = CandidateContig(
        id='test_candidate',
        record=SeqRecord(Seq('A' * 100), id='test_candidate'),
        metadata=ContigMetadata(segment='1', score=1.0, confidence=100.0, cluster='A', z=0.0),
    )
    candidate.analysis = ContigAnalysis()
    candidate.analysis.reasoning_graph = ReasoningGraph()
    
    # Test invalid node ID with valid prefix but doesn't exist in graph
    with pytest.raises(KeyError, match="Unknown observation node"):
        evaluate_counterfactual(candidate, "observation:nonexistent:node")


def test_counterfactual_invalid_node_type():
    """Test that unsupported node types raise ValueError."""
    candidate = CandidateContig(
        id='test_candidate',
        record=SeqRecord(Seq('A' * 100), id='test_candidate'),
        metadata=ContigMetadata(segment='1', score=1.0, confidence=100.0, cluster='A', z=0.0),
    )
    candidate.analysis = ContigAnalysis()
    candidate.analysis.reasoning_graph = ReasoningGraph()
    
    with pytest.raises(ValueError, match="ObservationNode removal"):
        evaluate_counterfactual(candidate, "unsupported_type:foo")


