"""
Tests for ReasoningExplorer.next_evidence() for BiologicalHypothesisNode.
"""

from __future__ import annotations

import segpick.explorer.explorer as explorer_module
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
from segpick.reasoning.rules import HypothesisRule, RuleCondition

# Create test rules that match our test graphs
TEST_RULE = HypothesisRule(
    rule_id="test_rule",
    title="Test Rule",
    category="test",
    scope="candidate",
    severity="informational",
    base_confidence="moderate",
    summary="Test rule for next_evidence",
    requires=(
        RuleCondition("observation", "type1", "structural_alignment"),
        RuleCondition("observation", "type2", "read_coverage"),
        RuleCondition("observation", "type3", "protein_alignment"),
    ),
    supports=(
        RuleCondition("finding", "Supporting Finding"),
        RuleCondition("finding", "Another Supporting Finding"),
    ),
    conflicts=(),
)


def _hypothesis_with_missing_required():
    """Has type1, missing type2 and type3 (both required)."""
    m = MeasurementNode("m1", "ch1", "metric", 1.0)
    o1 = ObservationNode("o1", "type1", "structural_alignment", "Present Observation")
    f = InterpretiveFindingNode("f1", "Finding", "Interpretation")
    s = EvidencePatternNode("s1", "p1", "Pattern", "Interp", "high")
    h = BiologicalHypothesisNode(id="h1", title="Hypothesis", summary="Explanation", confidence="high", rule_id="test_rule")
    edges = (ReasoningEdge(h.id, s.id, "supported_by"), ReasoningEdge(s.id, f.id, "composed_from"), ReasoningEdge(f.id, o1.id, "derived_from"), ReasoningEdge(o1.id, m.id, "supported_by"))
    return ReasoningGraph(measurements=(m,), observations=(o1,), interpretive_findings=(f,), evidence_patterns=(s,), biological_hypotheses=(h,), edges=edges)


def _hypothesis_with_missing_supporting():
    """Has all required (type1, type2, type3), missing supporting findings."""
    m = MeasurementNode("m1", "ch1", "metric", 1.0)
    o1 = ObservationNode("o1", "type1", "structural_alignment", "Observation 1")
    o2 = ObservationNode("o2", "type2", "read_coverage", "Observation 2")
    o3 = ObservationNode("o3", "type3", "protein_alignment", "Observation 3")
    f = InterpretiveFindingNode("f1", "Finding", "Interpretation")
    s = EvidencePatternNode("s1", "p1", "Pattern", "Interp", "high")
    h = BiologicalHypothesisNode(id="h1", title="Hypothesis", summary="Explanation", confidence="high", rule_id="test_rule")
    edges = (ReasoningEdge(h.id, s.id, "supported_by"), ReasoningEdge(s.id, f.id, "composed_from"), ReasoningEdge(f.id, o1.id, "derived_from"), ReasoningEdge(o1.id, m.id, "supported_by"))
    return ReasoningGraph(measurements=(m,), observations=(o1, o2, o3), interpretive_findings=(f,), evidence_patterns=(s,), biological_hypotheses=(h,), edges=edges)


def _hypothesis_complete():
    """Has all required and all supporting."""
    m = MeasurementNode("m1", "ch1", "metric", 1.0)
    o1 = ObservationNode("o1", "type1", "structural_alignment", "Observation 1")
    o2 = ObservationNode("o2", "type2", "read_coverage", "Observation 2")
    o3 = ObservationNode("o3", "type3", "protein_alignment", "Observation 3")
    f1 = InterpretiveFindingNode("f1", "Supporting Finding", "Supporting interp")
    f2 = InterpretiveFindingNode("f2", "Another Supporting Finding", "Another interp")
    s = EvidencePatternNode("s1", "p1", "Pattern", "Interp", "high")
    h = BiologicalHypothesisNode(id="h1", title="Hypothesis", summary="Explanation", confidence="high", rule_id="test_rule")
    edges = (ReasoningEdge(h.id, s.id, "supported_by"), ReasoningEdge(s.id, f1.id, "composed_from"), ReasoningEdge(f1.id, o1.id, "derived_from"), ReasoningEdge(o1.id, m.id, "supported_by"))
    return ReasoningGraph(measurements=(m,), observations=(o1, o2, o3), interpretive_findings=(f1, f2), evidence_patterns=(s,), biological_hypotheses=(h,), edges=edges)


def _hypothesis_multiple_missing():
    """Has type1 only, missing type2, type3 (required) and both supporting findings."""
    m = MeasurementNode("m1", "ch1", "metric", 1.0)
    o1 = ObservationNode("o1", "type1", "structural_alignment", "Present Obs 1")
    f1 = InterpretiveFindingNode("f1", "Finding 1", "Interp 1")
    s = EvidencePatternNode("s1", "p1", "Pattern", "Interp", "high")
    h = BiologicalHypothesisNode(id="h1", title="Hypothesis", summary="Explanation", confidence="high", rule_id="test_rule")
    edges = (ReasoningEdge(h.id, s.id, "supported_by"), ReasoningEdge(s.id, f1.id, "composed_from"), ReasoningEdge(f1.id, o1.id, "derived_from"), ReasoningEdge(o1.id, m.id, "supported_by"))
    return ReasoningGraph(measurements=(m,), observations=(o1,), interpretive_findings=(f1,), evidence_patterns=(s,), biological_hypotheses=(h,), edges=edges)


def _non_hypothesis_node():
    m = MeasurementNode("m1", "ch1", "metric", 1.0)
    o = ObservationNode("o1", "type1", "structural_alignment", "Observation")
    edges = (ReasoningEdge(o.id, m.id, "supported_by"),)
    return ReasoningGraph(measurements=(m,), observations=(o,), interpretive_findings=(), evidence_patterns=(), biological_hypotheses=(), edges=edges)



def test_missing_required_evidence(monkeypatch):
    monkeypatch.setattr(explorer_module, 'CANDIDATE_RULES', (TEST_RULE,))
    monkeypatch.setattr(explorer_module, 'GENE_RULES', ())
    graph = _hypothesis_with_missing_required()
    explorer = ReasoningExplorer(graph)
    result = explorer.next_evidence("h1")
    assert result.hypothesis.id == "h1"
    assert result.rule_id == "test_rule"
    # Missing required: type2@read_coverage, type3@protein_alignment
    assert len(result.missing_required) == 2
    req_labels = {c.condition.label for c in result.missing_required}
    assert req_labels == {"observation:type2@read_coverage", "observation:type3@protein_alignment"}
    # Missing supporting: Supporting Finding, Another Supporting Finding
    assert len(result.missing_supporting) == 2
    sup_labels = {c.condition.label for c in result.missing_supporting}
    assert sup_labels == {"finding:Supporting Finding", "finding:Another Supporting Finding"}


def test_missing_supporting_evidence(monkeypatch):
    monkeypatch.setattr(explorer_module, 'CANDIDATE_RULES', (TEST_RULE,))
    monkeypatch.setattr(explorer_module, 'GENE_RULES', ())
    graph = _hypothesis_with_missing_supporting()
    explorer = ReasoningExplorer(graph)
    result = explorer.next_evidence("h1")
    assert result.hypothesis.id == "h1"
    assert result.rule_id == "test_rule"
    # All required present, but supporting findings missing
    assert len(result.missing_required) == 0
    assert len(result.missing_supporting) == 2
    sup_labels = {c.condition.label for c in result.missing_supporting}
    assert sup_labels == {"finding:Supporting Finding", "finding:Another Supporting Finding"}


def test_complete_hypothesis(monkeypatch):
    monkeypatch.setattr(explorer_module, 'CANDIDATE_RULES', (TEST_RULE,))
    monkeypatch.setattr(explorer_module, 'GENE_RULES', ())
    graph = _hypothesis_complete()
    explorer = ReasoningExplorer(graph)
    result = explorer.next_evidence("h1")
    assert result.hypothesis.id == "h1"
    assert result.rule_id == "test_rule"
    assert len(result.missing_required) == 0
    assert len(result.missing_supporting) == 0


def test_multiple_missing_conditions(monkeypatch):
    monkeypatch.setattr(explorer_module, 'CANDIDATE_RULES', (TEST_RULE,))
    monkeypatch.setattr(explorer_module, 'GENE_RULES', ())
    graph = _hypothesis_multiple_missing()
    explorer = ReasoningExplorer(graph)
    result = explorer.next_evidence("h1")
    assert result.hypothesis.id == "h1"
    assert result.rule_id == "test_rule"
    assert len(result.missing_required) == 2
    req_labels = {c.condition.label for c in result.missing_required}
    assert req_labels == {"observation:type2@read_coverage", "observation:type3@protein_alignment"}
    assert len(result.missing_supporting) == 2
    sup_labels = {c.condition.label for c in result.missing_supporting}
    assert sup_labels == {"finding:Supporting Finding", "finding:Another Supporting Finding"}


def test_unknown_node_id(monkeypatch):
    monkeypatch.setattr(explorer_module, 'CANDIDATE_RULES', (TEST_RULE,))
    monkeypatch.setattr(explorer_module, 'GENE_RULES', ())
    graph = _hypothesis_complete()
    explorer = ReasoningExplorer(graph)
    try:
        explorer.next_evidence("nonexistent")
        raise AssertionError("Expected KeyError")
    except KeyError as exc:
        assert "Unknown reasoning node 'nonexistent'" in str(exc)


def test_non_hypothesis_node(monkeypatch):
    monkeypatch.setattr(explorer_module, 'CANDIDATE_RULES', (TEST_RULE,))
    monkeypatch.setattr(explorer_module, 'GENE_RULES', ())
    graph = _non_hypothesis_node()
    explorer = ReasoningExplorer(graph)
    result = explorer.next_evidence("o1")
    assert result.hypothesis.id == "o1"
    assert result.rule_id == ""
    assert len(result.missing_required) == 0
    assert len(result.missing_supporting) == 0


def test_preserves_rule_condition_structure(monkeypatch):
    monkeypatch.setattr(explorer_module, 'CANDIDATE_RULES', (TEST_RULE,))
    monkeypatch.setattr(explorer_module, 'GENE_RULES', ())
    graph = _hypothesis_with_missing_required()
    explorer = ReasoningExplorer(graph)
    result = explorer.next_evidence("h1")
    gap = result.missing_required[0]
    assert hasattr(gap.condition, 'kind')
    assert hasattr(gap.condition, 'value')
    assert hasattr(gap.condition, 'source')
    assert gap.condition.kind == "observation"
    assert gap.condition.value == "type2"
    assert gap.condition.source == "read_coverage"
    assert gap.condition.label == "observation:type2@read_coverage"


def test_hypothesis_without_rule_id(monkeypatch):
    monkeypatch.setattr(explorer_module, 'CANDIDATE_RULES', (TEST_RULE,))
    monkeypatch.setattr(explorer_module, 'GENE_RULES', ())
    graph = _hypothesis_complete()
    h = BiologicalHypothesisNode(id="h1", title="Hypothesis", summary="Explanation", confidence="high", rule_id="")
    graph = ReasoningGraph(measurements=graph.measurements, observations=graph.observations, interpretive_findings=graph.interpretive_findings, evidence_patterns=graph.evidence_patterns, biological_hypotheses=(h,), edges=graph.edges)
    explorer = ReasoningExplorer(graph)
    result = explorer.next_evidence("h1")
    assert result.hypothesis.id == "h1"
    assert result.rule_id == ""
    assert len(result.missing_required) == 0
    assert len(result.missing_supporting) == 0
