"""
Tests for the reasoning graph query engine (extract_provenance).
"""

from __future__ import annotations

from segpick.explorer.queries import extract_provenance
from segpick.models import (
    BiologicalHypothesisNode,
    EvidencePatternNode,
    InterpretiveFindingNode,
    MeasurementNode,
    ObservationNode,
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


def test_linear_chain():
    """Test provenance extraction for a linear hypothesis -> pattern -> finding -> observation -> measurement chain."""
    graph = _linear_chain_graph()
    prov = extract_provenance(graph, "h1")

    assert prov.claim.id == "h1"
    assert len(prov.nodes) == 5
    assert {n.id for n in prov.nodes} == {"h1", "s1", "f1", "o1", "m1"}
    assert len(prov.edges) == 4
    edge_tuples = {(e.source_id, e.target_id, e.relationship) for e in prov.edges}
    assert edge_tuples == {
        ("h1", "s1", "supported_by"),
        ("s1", "f1", "composed_from"),
        ("f1", "o1", "derived_from"),
        ("o1", "m1", "supported_by"),
    }


def _branching_graph():
    """Build a graph with branching: hypothesis supported by two patterns, each with their own findings."""
    m1 = MeasurementNode("m1", "ch1", "metric1", 1.0)
    m2 = MeasurementNode("m2", "ch2", "metric2", 2.0)
    o1 = ObservationNode("o1", "type1", "src1", "Obs 1")
    o2 = ObservationNode("o2", "type2", "src2", "Obs 2")
    f1 = InterpretiveFindingNode("f1", "Finding 1", "Interpretation 1")
    f2 = InterpretiveFindingNode("f2", "Finding 2", "Interpretation 2")
    s1 = EvidencePatternNode("s1", "p1", "Pattern 1", "Interp 1", "high")
    s2 = EvidencePatternNode("s2", "p2", "Pattern 2", "Interp 2", "high")
    h = BiologicalHypothesisNode("h1", "Hypothesis", "Explanation", "high")

    edges = (
        # h supported by both s1 and s2
        ReasoningEdge(h.id, s1.id, "supported_by"),
        ReasoningEdge(h.id, s2.id, "supported_by"),
        # s1 composed from f1
        ReasoningEdge(s1.id, f1.id, "composed_from"),
        # s2 composed from f2
        ReasoningEdge(s2.id, f2.id, "composed_from"),
        # f1 derived from o1
        ReasoningEdge(f1.id, o1.id, "derived_from"),
        # f2 derived from o2
        ReasoningEdge(f2.id, o2.id, "derived_from"),
        # o1 supported by m1
        ReasoningEdge(o1.id, m1.id, "supported_by"),
        # o2 supported by m2
        ReasoningEdge(o2.id, m2.id, "supported_by"),
    )

    return ReasoningGraph(
        measurements=(m1, m2),
        observations=(o1, o2),
        interpretive_findings=(f1, f2),
        evidence_patterns=(s1, s2),
        biological_hypotheses=(h,),
        edges=edges,
    )


def test_branching_evidence():
    """Test provenance extraction with branching evidence (multiple supporting patterns)."""
    graph = _branching_graph()
    prov = extract_provenance(graph, "h1")

    assert prov.claim.id == "h1"
    assert len(prov.nodes) == 9  # h1, s1, s2, f1, f2, o1, o2, m1, m2
    assert {n.id for n in prov.nodes} == {"h1", "s1", "s2", "f1", "f2", "o1", "o2", "m1", "m2"}
    assert len(prov.edges) == 8
    edge_tuples = {(e.source_id, e.target_id, e.relationship) for e in prov.edges}
    assert edge_tuples == {
        ("h1", "s1", "supported_by"),
        ("h1", "s2", "supported_by"),
        ("s1", "f1", "composed_from"),
        ("s2", "f2", "composed_from"),
        ("f1", "o1", "derived_from"),
        ("f2", "o2", "derived_from"),
        ("o1", "m1", "supported_by"),
        ("o2", "m2", "supported_by"),
    }


def _shared_downstream_graph():
    """Build a graph with shared downstream evidence: two hypotheses share a pattern."""
    m = MeasurementNode("m1", "ch1", "metric", 1.0)
    o = ObservationNode("o1", "type1", "src1", "Shared observation")
    f = InterpretiveFindingNode("f1", "Shared Finding", "Shared interpretation")
    s = EvidencePatternNode("s1", "shared_pattern", "Shared Pattern", "Shared", "high")
    h1 = BiologicalHypothesisNode("h1", "Hypothesis 1", "Exp 1", "high")
    h2 = BiologicalHypothesisNode("h2", "Hypothesis 2", "Exp 2", "high")

    edges = (
        # Both hypotheses supported by the same pattern
        ReasoningEdge(h1.id, s.id, "supported_by"),
        ReasoningEdge(h2.id, s.id, "supported_by"),
        # Pattern composed from shared finding
        ReasoningEdge(s.id, f.id, "composed_from"),
        # Finding derived from shared observation
        ReasoningEdge(f.id, o.id, "derived_from"),
        # Observation supported by shared measurement
        ReasoningEdge(o.id, m.id, "supported_by"),
    )

    return ReasoningGraph(
        measurements=(m,),
        observations=(o,),
        interpretive_findings=(f,),
        evidence_patterns=(s,),
        biological_hypotheses=(h1, h2),
        edges=edges,
    )


def test_shared_downstream_evidence():
    """Test provenance extraction when multiple hypotheses share downstream evidence."""
    graph = _shared_downstream_graph()

    # Extract for h1
    prov1 = extract_provenance(graph, "h1")
    assert prov1.claim.id == "h1"
    assert len(prov1.nodes) == 5
    assert {n.id for n in prov1.nodes} == {"h1", "s1", "f1", "o1", "m1"}
    assert len(prov1.edges) == 4

    # Extract for h2
    prov2 = extract_provenance(graph, "h2")
    assert prov2.claim.id == "h2"
    assert len(prov2.nodes) == 5
    assert {n.id for n in prov2.nodes} == {"h2", "s1", "f1", "o1", "m1"}
    assert len(prov2.edges) == 4


def test_unknown_node_id():
    """Test that extracting provenance for an unknown node raises KeyError."""
    graph = _linear_chain_graph()

    try:
        extract_provenance(graph, "nonexistent")
        raise AssertionError("Expected KeyError for unknown node")
    except KeyError as exc:
        assert "Unknown reasoning node 'nonexistent'" in str(exc)


def test_contradicted_by_relationship():
    """Test that contradicted_by edges are included in provenance."""
    m = MeasurementNode("m1", "ch1", "metric", 1.0)
    o = ObservationNode("o1", "type1", "src1", "Obs")
    f = InterpretiveFindingNode("f1", "Finding", "Interp")
    s = EvidencePatternNode("s1", "p1", "Pattern", "Interp", "high")
    h = BiologicalHypothesisNode("h1", "Hypothesis", "Exp", "high")

    edges = (
        ReasoningEdge(h.id, s.id, "supported_by"),
        ReasoningEdge(s.id, f.id, "composed_from"),
        ReasoningEdge(f.id, o.id, "derived_from"),
        ReasoningEdge(o.id, m.id, "supported_by"),
        # Also contradicted by another pattern
        ReasoningEdge(h.id, "s2", "contradicted_by"),
    )

    # Add the contradicting pattern
    s2 = EvidencePatternNode("s2", "p2", "Contradicting Pattern", "Contradicts", "high")
    edges_with_contradiction = edges + (ReasoningEdge(s2.id, f.id, "conflicted_by"),)

    graph = ReasoningGraph(
        measurements=(m,),
        observations=(o,),
        interpretive_findings=(f,),
        evidence_patterns=(s, s2),
        biological_hypotheses=(h,),
        edges=edges_with_contradiction,
    )

    prov = extract_provenance(graph, "h1")
    assert len(prov.nodes) == 6  # h1, s1, s2, f1, o1, m1
    assert {n.id for n in prov.nodes} == {"h1", "s1", "s2", "f1", "o1", "m1"}
    edge_tuples = {(e.source_id, e.target_id, e.relationship) for e in prov.edges}
    assert ("h1", "s1", "supported_by") in edge_tuples
    assert ("h1", "s2", "contradicted_by") in edge_tuples
    assert ("s1", "f1", "composed_from") in edge_tuples
    assert ("s2", "f1", "conflicted_by") in edge_tuples
    assert ("f1", "o1", "derived_from") in edge_tuples
    assert ("o1", "m1", "supported_by") in edge_tuples
