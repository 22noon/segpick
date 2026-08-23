"""
Tests for the ReasoningExplorer façade.
"""

from __future__ import annotations

from segpick.explorer import ReasoningExplorer
from segpick.explorer.provenance import Provenance
from segpick.models import (
    MeasurementNode,
    ObservationNode,
    InterpretiveFindingNode,
    EvidencePatternNode,
    BiologicalHypothesisNode,
    ReasoningEdge,
    ReasoningGraph,
)


def _linear_chain_graph():
    """Build a linear chain: hypothesis -> pattern -> finding -> observation -> measurement"""
    m = MeasurementNode("m1", "channel1", "metric", 42.0)
    o = ObservationNode("o1", "type1", "source1", "Observed something")
    f = InterpretiveFindingNode("f1", "Finding A", "This suggests something")
    s = EvidencePatternNode("s1", "pattern_a", "Pattern A", "Several findings compose this", "high")
    h = BiologicalHypothesisNode("h1", "Hypothesis A", "The best explanation", "high")

    edges = (
        ReasoningEdge(h.id, s.id, "supported_by"),
        ReasoningEdge(s.id, f.id, "composed_from"),
        ReasoningEdge(f.id, o.id, "derived_from"),
        ReasoningEdge(o.id, m.id, "supported_by"),
    )

    return ReasoningGraph(
        measurements=(m,),
        observations=(o,),
        interpretive_findings=(f,),
        evidence_patterns=(s,),
        biological_hypotheses=(h,),
        edges=edges,
    )


def test_explainer_delegates_to_extract_provenance():
    """ReasoningExplorer.explain() returns a Provenance from extract_provenance()."""
    graph = _linear_chain_graph()
    explorer = ReasoningExplorer(graph)

    prov = explorer.explain("h1")

    assert isinstance(prov, Provenance)
    assert prov.claim.id == "h1"
    assert len(prov.nodes) == 5
    assert {n.id for n in prov.nodes} == {"h1", "s1", "f1", "o1", "m1"}
    assert len(prov.edges) == 4


def test_explainer_raises_for_unknown_node():
    """ReasoningExplorer.explain() raises KeyError for unknown node IDs."""
    graph = _linear_chain_graph()
    explorer = ReasoningExplorer(graph)

    try:
        explorer.explain("nonexistent")
        raise AssertionError("Expected KeyError")
    except KeyError as exc:
        assert "Unknown reasoning node 'nonexistent'" in str(exc)


def test_explainer_returns_correct_claim():
    """The Provenance.claim is the node that was queried."""
    graph = _linear_chain_graph()
    explorer = ReasoningExplorer(graph)

    # Query for the pattern node
    prov = explorer.explain("s1")

    assert prov.claim.id == "s1"
    assert len(prov.nodes) == 4  # s1, f1, o1, m1
    assert {n.id for n in prov.nodes} == {"s1", "f1", "o1", "m1"}


def test_explainer_returns_correct_edges():
    """The Provenance edges match the reasoning graph's provenance edges."""
    graph = _linear_chain_graph()
    explorer = ReasoningExplorer(graph)

    prov = explorer.explain("h1")

    edge_tuples = {(e.source_id, e.target_id, e.relationship) for e in prov.edges}
    assert edge_tuples == {
        ("h1", "s1", "supported_by"),
        ("s1", "f1", "composed_from"),
        ("f1", "o1", "derived_from"),
        ("o1", "m1", "supported_by"),
    }


def test_explainer_accepts_reasoning_graph_only():
    """ReasoningExplorer only accepts ReasoningGraph instances."""
    graph = _linear_chain_graph()
    explorer = ReasoningExplorer(graph)
    assert explorer._graph is graph
