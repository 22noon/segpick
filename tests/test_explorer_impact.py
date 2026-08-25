"""
Tests for ReasoningExplorer.impact() reverse-provenance traversal.
"""

from __future__ import annotations

from segpick.explorer import ReasoningExplorer
from segpick.models import (
    BiologicalHypothesisNode,
    EvidencePatternNode,
    InterpretiveFindingNode,
    MeasurementNode,
    ObservationNode,
    ReasoningEdge,
    ReasoningGraph,
)


def _simple_chain_graph():
    """Simple linear chain: observation -> finding -> pattern -> hypothesis."""
    m = MeasurementNode("m1", "ch1", "metric", 1.0)
    o = ObservationNode("o1", "type1", "src1", "Observation")
    f = InterpretiveFindingNode("f1", "Finding", "Interpretation")
    s = EvidencePatternNode("s1", "p1", "Pattern", "Interpretation", "high")
    h = BiologicalHypothesisNode("h1", "Hypothesis", "Explanation", "high")

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


def _multiple_hypotheses_graph():
    """One observation affecting multiple hypotheses via shared downstream."""
    m = MeasurementNode("m1", "ch1", "metric", 1.0)
    o = ObservationNode("o1", "type1", "src1", "Shared Observation")
    f = InterpretiveFindingNode("f1", "Shared Finding", "Shared Interpretation")
    s = EvidencePatternNode("s1", "shared_pattern", "Shared Pattern", "Shared", "high")
    h1 = BiologicalHypothesisNode("h1", "Hypothesis A", "Explanation A", "high")
    h2 = BiologicalHypothesisNode("h2", "Hypothesis B", "Explanation B", "high")

    edges = (
        ReasoningEdge(h1.id, s.id, "supported_by"),
        ReasoningEdge(h2.id, s.id, "supported_by"),
        ReasoningEdge(s.id, f.id, "composed_from"),
        ReasoningEdge(f.id, o.id, "derived_from"),
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


def _branching_paths_graph():
    """Observation with branching paths to multiple hypotheses."""
    m = MeasurementNode("m1", "ch1", "metric", 1.0)
    o = ObservationNode("o1", "type1", "src1", "Observation")
    f1 = InterpretiveFindingNode("f1", "Finding 1", "Interp 1")
    f2 = InterpretiveFindingNode("f2", "Finding 2", "Interp 2")
    s1 = EvidencePatternNode("s1", "p1", "Pattern 1", "Interp 1", "high")
    s2 = EvidencePatternNode("s2", "p2", "Pattern 2", "Interp 2", "high")
    h1 = BiologicalHypothesisNode("h1", "Hypothesis A", "Exp A", "high")
    h2 = BiologicalHypothesisNode("h2", "Hypothesis B", "Exp B", "high")

    edges = (
        # Path 1: h1 -> s1 -> f1 -> o1 -> m1
        ReasoningEdge(h1.id, s1.id, "supported_by"),
        ReasoningEdge(s1.id, f1.id, "composed_from"),
        ReasoningEdge(f1.id, o.id, "derived_from"),
        # Path 2: h2 -> s2 -> f2 -> o1 -> m1
        ReasoningEdge(h2.id, s2.id, "supported_by"),
        ReasoningEdge(s2.id, f2.id, "composed_from"),
        ReasoningEdge(f2.id, o.id, "derived_from"),
        # Shared: o1 -> m1
        ReasoningEdge(o.id, m.id, "supported_by"),
    )

    return ReasoningGraph(
        measurements=(m,),
        observations=(o,),
        interpretive_findings=(f1, f2),
        evidence_patterns=(s1, s2),
        biological_hypotheses=(h1, h2),
        edges=edges,
    )


def _shared_intermediate_graph():
    """Multiple paths sharing intermediate nodes before diverging."""
    m = MeasurementNode("m1", "ch1", "metric", 1.0)
    o = ObservationNode("o1", "type1", "src1", "Observation")
    f = InterpretiveFindingNode("f1", "Finding", "Interpretation")
    s1 = EvidencePatternNode("s1", "p1", "Pattern 1", "Interp 1", "high")
    s2 = EvidencePatternNode("s2", "p2", "Pattern 2", "Interp 2", "high")
    h1 = BiologicalHypothesisNode("h1", "Hypothesis A", "Exp A", "high")
    h2 = BiologicalHypothesisNode("h2", "Hypothesis B", "Exp B", "high")

    edges = (
        # Both hypotheses share finding and observation
        ReasoningEdge(h1.id, s1.id, "supported_by"),
        ReasoningEdge(h2.id, s2.id, "supported_by"),
        ReasoningEdge(s1.id, f.id, "composed_from"),
        ReasoningEdge(s2.id, f.id, "composed_from"),
        ReasoningEdge(f.id, o.id, "derived_from"),
        ReasoningEdge(o.id, m.id, "supported_by"),
    )

    return ReasoningGraph(
        measurements=(m,),
        observations=(o,),
        interpretive_findings=(f,),
        evidence_patterns=(s1, s2),
        biological_hypotheses=(h1, h2),
        edges=edges,
    )


def _no_downstream_graph():
    """Observation with no downstream impact (no higher-level nodes depend on it)."""
    m = MeasurementNode("m1", "ch1", "metric", 1.0)
    o = ObservationNode("o1", "type1", "src1", "Isolated Observation")
    f = InterpretiveFindingNode("f1", "Finding", "Interpretation")
    s = EvidencePatternNode("s1", "p1", "Pattern", "Interp", "high")
    h = BiologicalHypothesisNode("h1", "Hypothesis", "Explanation", "high")

    edges = (
        # h -> s -> f (but f does NOT derive from o)
        ReasoningEdge(h.id, s.id, "supported_by"),
        ReasoningEdge(s.id, f.id, "composed_from"),
        # o is isolated, only connected to m
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


def _mixed_relationships_graph():
    """One hypothesis supported, one contradicted by shared finding."""
    m = MeasurementNode("m1", "ch1", "metric", 1.0)
    o = ObservationNode("o1", "type1", "src1", "Observation")
    f = InterpretiveFindingNode("f1", "Finding", "Interpretation")
    s1 = EvidencePatternNode("s1", "p1", "Supporting Pattern", "Supports", "high")
    s2 = EvidencePatternNode("s2", "p2", "Contradicting Pattern", "Contradicts", "high")
    h1 = BiologicalHypothesisNode("h1", "Supported Hypothesis", "Exp 1", "high")
    h2 = BiologicalHypothesisNode("h2", "Contradicted Hypothesis", "Exp 2", "high")

    edges = (
        # h1 supported_by s1
        ReasoningEdge(h1.id, s1.id, "supported_by"),
        # h2 contradicted_by s2
        ReasoningEdge(h2.id, s2.id, "contradicted_by"),
        # Both patterns from same finding
        ReasoningEdge(s1.id, f.id, "composed_from"),
        ReasoningEdge(s2.id, f.id, "conflicted_by"),
        ReasoningEdge(f.id, o.id, "derived_from"),
        ReasoningEdge(o.id, m.id, "supported_by"),
    )

    return ReasoningGraph(
        measurements=(m,),
        observations=(o,),
        interpretive_findings=(f,),
        evidence_patterns=(s1, s2),
        biological_hypotheses=(h1, h2),
        edges=edges,
    )


def test_simple_chain():
    """Impact from observation traverses up to hypothesis through finding and pattern."""
    graph = _simple_chain_graph()
    explorer = ReasoningExplorer(graph)

    result = explorer.impact("o1")

    assert result.source.id == "o1"
    assert len(result.paths) == 1
    path = result.paths[0]
    assert path.claim.id == "h1"
    # Path: o1 -> f1 -> s1 -> h1
    assert [n.id for n in path.nodes] == ["o1", "f1", "s1", "h1"]
    assert len(path.edges) == 3
    edge_rels = [e.relationship for e in path.edges]
    assert edge_rels == ["derived_from", "composed_from", "supported_by"]


def test_one_observation_multiple_hypotheses():
    """Single observation affects multiple hypotheses through shared downstream."""
    graph = _multiple_hypotheses_graph()
    explorer = ReasoningExplorer(graph)

    result = explorer.impact("o1")

    assert result.source.id == "o1"
    assert len(result.paths) == 2
    claim_ids = {p.claim.id for p in result.paths}
    assert claim_ids == {"h1", "h2"}
    # Both paths share o1->f1->s1 then diverge to h1/h2
    for path in result.paths:
        assert [n.id for n in path.nodes[:3]] == ["o1", "f1", "s1"]


def test_branching_paths():
    """Observation has multiple distinct paths to different hypotheses."""
    graph = _branching_paths_graph()
    explorer = ReasoningExplorer(graph)

    result = explorer.impact("o1")

    assert result.source.id == "o1"
    assert len(result.paths) == 2
    claim_ids = {p.claim.id for p in result.paths}
    assert claim_ids == {"h1", "h2"}
    # Path 1: o1 -> f1 -> s1 -> h1
    # Path 2: o1 -> f2 -> s2 -> h2
    path_dict = {p.claim.id: p for p in result.paths}
    assert [n.id for n in path_dict["h1"].nodes] == ["o1", "f1", "s1", "h1"]
    assert [n.id for n in path_dict["h2"].nodes] == ["o1", "f2", "s2", "h2"]


def test_shared_intermediate_nodes():
    """Multiple paths sharing intermediate nodes (finding) before diverging to patterns/hypotheses."""
    graph = _shared_intermediate_graph()
    explorer = ReasoningExplorer(graph)

    result = explorer.impact("o1")

    assert result.source.id == "o1"
    assert len(result.paths) == 2
    claim_ids = {p.claim.id for p in result.paths}
    assert claim_ids == {"h1", "h2"}
    # Both paths: o1 -> f1 -> s1/s2 -> h1/h2
    for path in result.paths:
        assert path.nodes[0].id == "o1"
        assert path.nodes[1].id == "f1"
        assert path.nodes[2].id in ("s1", "s2")
        assert path.nodes[3].id in ("h1", "h2")


def test_no_downstream_impact():
    """Isolated observation has no paths to any hypothesis."""
    graph = _no_downstream_graph()
    explorer = ReasoningExplorer(graph)

    result = explorer.impact("o1")

    assert result.source.id == "o1"
    assert len(result.paths) == 0


def test_unknown_node_id():
    """impact() raises KeyError for unknown node."""
    graph = _simple_chain_graph()
    explorer = ReasoningExplorer(graph)

    try:
        explorer.impact("nonexistent")
        raise AssertionError("Expected KeyError")
    except KeyError as exc:
        assert "Unknown reasoning node 'nonexistent'" in str(exc)


def test_preserves_relationship_types():
    """Impact paths preserve supported_by vs contradicted_by relationships."""
    graph = _mixed_relationships_graph()
    explorer = ReasoningExplorer(graph)

    result = explorer.impact("o1")

    assert len(result.paths) == 2
    path_dict = {p.claim.id: p for p in result.paths}
    # h1 path: o1 -(derived_from)-> f1 -(composed_from)-> s1 -(supported_by)-> h1
    h1_edges = [e.relationship for e in path_dict["h1"].edges]
    assert h1_edges == ["derived_from", "composed_from", "supported_by"]
    # h2 path: o1 -(derived_from)-> f1 -(conflicted_by)-> s2 -(contradicted_by)-> h2
    h2_edges = [e.relationship for e in path_dict["h2"].edges]
    assert h2_edges == ["derived_from", "conflicted_by", "contradicted_by"]


def test_impact_from_finding():
    """Impact from a finding node (not observation)."""
    graph = _simple_chain_graph()
    explorer = ReasoningExplorer(graph)

    result = explorer.impact("f1")

    assert result.source.id == "f1"
    assert len(result.paths) == 1
    path = result.paths[0]
    assert path.claim.id == "h1"
    assert [n.id for n in path.nodes] == ["f1", "s1", "h1"]
    assert [e.relationship for e in path.edges] == ["composed_from", "supported_by"]


def test_impact_from_pattern():
    """Impact from an evidence pattern node."""
    graph = _simple_chain_graph()
    explorer = ReasoningExplorer(graph)

    result = explorer.impact("s1")

    assert result.source.id == "s1"
    assert len(result.paths) == 1
    path = result.paths[0]
    assert path.claim.id == "h1"
    assert [n.id for n in path.nodes] == ["s1", "h1"]
    assert [e.relationship for e in path.edges] == ["supported_by"]


def test_impact_from_hypothesis():
    """Impact from a hypothesis node (claim itself) returns single-node path."""
    graph = _simple_chain_graph()
    explorer = ReasoningExplorer(graph)

    result = explorer.impact("h1")

    assert result.source.id == "h1"
    assert len(result.paths) == 1
    path = result.paths[0]
    assert path.claim.id == "h1"
    assert [n.id for n in path.nodes] == ["h1"]
    assert len(path.edges) == 0
