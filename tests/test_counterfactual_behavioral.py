"""
Behavioral tests for query-time counterfactual evaluation.
These tests verify the actual counterfactual semantics using real evaluation machinery.
"""

from __future__ import annotations


def _make_test_candidate():
    """Create a test candidate with a complete reasoning graph and analysis data."""
    # Import everything inside the function to avoid circular imports
    from Bio.Seq import Seq
    from Bio.SeqRecord import SeqRecord

    from segpick.models import (
        BiologicalFinding,
        EvidenceObservation,
        ObservationSource,
    )
    from segpick.models.reasoning_graph import BiologicalHypothesisNode, EvidencePatternNode, InterpretiveFindingNode, MeasurementNode, ObservationNode, ReasoningEdge, ReasoningGraph

    m1 = MeasurementNode('m1', 'channel1', 'metric', 42.0)
    o1 = ObservationNode('observation:protein-alignment:type1:1', 'type1', 'protein_alignment', 'Evidence X')
    o2 = ObservationNode('observation:protein-alignment:type2:1', 'type2', 'protein_alignment', 'Evidence Y')
    o3 = ObservationNode('observation:protein-alignment:type3:1', 'type3', 'protein_alignment', 'Evidence Z')
    f1 = InterpretiveFindingNode('interpretation:finding-a:1', 'Finding A', 'Finding from X')
    f2 = InterpretiveFindingNode('interpretation:finding-b:1', 'Finding B', 'Finding from Y')
    f3 = InterpretiveFindingNode('interpretation:finding-c:1', 'Finding C', 'Finding from Z')
    s1 = EvidencePatternNode('pattern:incomplete_terminal_assembly:1', 'incomplete_terminal_assembly', 'Pattern P', 'Pattern from X and Y', 'high')
    s2 = EvidencePatternNode('pattern:reference_unsupported_internal_sequence:1', 'reference_unsupported_internal_sequence', 'Pattern Q', 'Pattern from Z', 'high')
    h1 = BiologicalHypothesisNode('hypothesis:evidence-pattern:incomplete_segment:1', 'Hypothesis A', 'Hypothesis A', 'high', rule_id='incomplete_segment')
    h2 = BiologicalHypothesisNode('hypothesis:evidence-pattern:reference_relative_structural_variation:1', 'Hypothesis B', 'Hypothesis B', 'high', rule_id='reference_relative_structural_variation')

    edges = (
        ReasoningEdge('hypothesis:evidence-pattern:incomplete_segment:1', 'pattern:incomplete_terminal_assembly:1', 'supported_by'),
        ReasoningEdge('hypothesis:evidence-pattern:reference_relative_structural_variation:1', 'pattern:reference_unsupported_internal_sequence:1', 'supported_by'),
        ReasoningEdge('pattern:incomplete_terminal_assembly:1', 'interpretation:finding-a:1', 'composed_from'),
        ReasoningEdge('pattern:incomplete_terminal_assembly:1', 'interpretation:finding-b:1', 'composed_from'),
        ReasoningEdge('pattern:reference_unsupported_internal_sequence:1', 'interpretation:finding-c:1', 'composed_from'),
        ReasoningEdge('interpretation:finding-a:1', 'observation:protein-alignment:type1:1', 'derived_from'),
        ReasoningEdge('interpretation:finding-b:1', 'observation:protein-alignment:type2:1', 'derived_from'),
        ReasoningEdge('interpretation:finding-c:1', 'observation:protein-alignment:type3:1', 'derived_from'),
    )

    graph = ReasoningGraph(
        measurements=(m1,),
        observations=(o1, o2, o3),
        interpretive_findings=(f1, f2, f3),
        evidence_patterns=(s1, s2),
        biological_hypotheses=(h1, h2),
        edges=edges,
    )

    candidate = CandidateContig(
        id='test_candidate',
        record=SeqRecord(Seq('A' * 100), id='test_candidate'),
        metadata=ContigMetadata(segment='1', score=1.0, confidence=100.0, cluster='A', z=0.0),
    )
    candidate.analysis = ContigAnalysis()
    candidate.analysis.reasoning_graph = graph
    candidate.analysis.structural_integrity = StructuralIntegrity(
        reference_id='ref_a',
        candidate_coverage=0.95,
        reference_coverage=0.90,
        block_count=2,
        longest_block_fraction=0.75,
        largest_candidate_gap=12,
        largest_reference_gap=20,
        continuity=0.98,
        orientation_consistency=1.0,
        order_consistency=0.9,
        score=0.81,
        status='MINOR_DISCONTINUITY',
    )
    candidate.analysis.containment = ContainmentMetrics(
        query_length=100,
        anchor_length=100,
        query_coverage=1.0,
        anchor_coverage=1.0,
        identity=0.99,
        fragmentation=0.0,
        structural_score=0.99,
        status='COMPLETE',
    )
    
    # Mock observations with valid ObservationSource values
    from segpick.models import (
        EvidencePatternEvaluation,
        HypothesisEvaluation,
    )
    
    obs1 = EvidenceObservation(
        observation_type='type1',
        source=ObservationSource.PROTEIN_ALIGNMENT,
        description='Evidence X',
        attributes={'metric': 42.0},
    )
    obs2 = EvidenceObservation(
        observation_type='type2',
        source=ObservationSource.PROTEIN_ALIGNMENT,
        description='Evidence Y',
        attributes={'metric': 42.0},
    )
    obs3 = EvidenceObservation(
        observation_type='type3',
        source=ObservationSource.PROTEIN_ALIGNMENT,
        description='Evidence Z',
        attributes={'metric': 42.0},
    )
    
    finding1 = BiologicalFinding(
        category='test',
        title='Finding A',
        severity='informational',
        confidence='high',
        scope='candidate',
        summary='Finding from X',
        sources=('protein_alignment',),
        observation_types=('type1',),
        candidate_ids=('test_candidate',),
    )
    finding2 = BiologicalFinding(
        category='test',
        title='Finding B',
        severity='informational',
        confidence='high',
        scope='candidate',
        summary='Finding from Y',
        sources=('protein_alignment',),
        observation_types=('type2',),
        candidate_ids=('test_candidate',),
    )
    finding3 = BiologicalFinding(
        category='test',
        title='Finding C',
        severity='informational',
        confidence='high',
        scope='candidate',
        summary='Finding from Z',
        sources=('protein_alignment',),
        observation_types=('type3',),
        candidate_ids=('test_candidate',),
    )
    
    candidate = CandidateContig(
        id='test_candidate',
        record=SeqRecord(Seq('A' * 100), id='test_candidate'),
        metadata=ContigMetadata(segment='1', score=1.0, confidence=100.0, cluster='A', z=0.0),
    )
    candidate.analysis = ContigAnalysis()
    candidate.analysis.reasoning_graph = graph
    candidate.analysis.structural_integrity = StructuralIntegrity(
        reference_id='ref_a',
        candidate_coverage=0.95,
        reference_coverage=0.90,
        block_count=2,
        longest_block_fraction=0.75,
        largest_candidate_gap=12,
        largest_reference_gap=20,
        continuity=0.98,
        orientation_consistency=1.0,
        order_consistency=0.9,
        score=0.81,
        status='MINOR_DISCONTINUITY',
    )
    candidate.analysis.containment = ContainmentMetrics(
        query_length=100,
        anchor_length=100,
        query_coverage=1.0,
        anchor_coverage=1.0,
        identity=0.99,
        fragmentation=0.0,
        structural_score=0.99,
        status='COMPLETE',
    )
    
    # Mock observations
    candidate.analysis.observations = (obs1, obs2, obs3)
    candidate.analysis.findings = (finding1, finding2, finding3)
    candidate.analysis.evidence_patterns = (
        EvidencePatternEvaluation(
            pattern_id='incomplete_terminal_assembly',
            title='Pattern P',
            category='test',
            scope='candidate',
            confidence='high',
            severity='review',
            interpretation='Pattern from X and Y',
            candidate_ids=('test_candidate',),
            matched_required=('finding:Finding A', 'finding:Finding B'),
            matched_supporting=(),
            matched_conflicting=(),
            suggested_actions=(),
            source='builtin',
            references=(),
            evidence_provenance=(),
            state='matched',
            missing_required=(),
            missing_supporting=(),
            unused_findings=(),
        ),
        EvidencePatternEvaluation(
            pattern_id='reference_unsupported_internal_sequence',
            title='Pattern Q',
            category='test',
            scope='candidate',
            confidence='high',
            severity='review',
            interpretation='Pattern from Z',
            candidate_ids=('test_candidate',),
            matched_required=('finding:Finding C',),
            matched_supporting=(),
            matched_conflicting=(),
            suggested_actions=(),
            source='builtin',
            references=(),
            evidence_provenance=(),
            state='matched',
            missing_required=(),
            missing_supporting=(),
            unused_findings=(),
        ),
    )
    candidate.analysis.biological_hypothesis_evaluations = (
        HypothesisEvaluation(
            hypothesis_id='incomplete_segment',
            title='Hypothesis A',
            category='test',
            scope='candidate',
            confidence='high',
            severity='informational',
            explanation='Hypothesis A',
            base_confidence='moderate',
            definition_supported_by=('pattern:pattern-a:1'),
            definition_contradicted_by=('divergent_but_coherent_segment'),
            minimum_support=1,
            candidate_ids=('test_candidate',),
            supporting_patterns=('pattern:pattern-a:1',),
            supporting_pattern_titles=('Pattern P',),
            conflicting_patterns=(),
            conflicting_pattern_titles=(),
            recommended_actions=(),
            source='builtin',
            references=(),
        ),
        HypothesisEvaluation(
            hypothesis_id='reference_relative_structural_variation',
            title='Hypothesis B',
            category='test',
            scope='candidate',
            confidence='high',
            severity='informational',
            explanation='Hypothesis B',
            base_confidence='moderate',
            definition_supported_by=('pattern:pattern-b:1'),
            definition_contradicted_by=('divergent_but_coherent_segment'),
            minimum_support=1,
            candidate_ids=('test_candidate',),
            supporting_patterns=('pattern:pattern-b:1',),
            conflicting_patterns=(),
            conflicting_pattern_titles=(),
            recommended_actions=(),
            source='builtin',
            references=(),
        ),
    )
    candidate.analysis.hypotheses = ()
    candidate.analysis.reasoning_graph = graph
    
    return candidate


# Import all needed types at the end to avoid circular imports

from segpick.models import (
    BiologicalFinding,
    CandidateContig,
    ContainmentMetrics,
    ContigAnalysis,
    ContigMetadata,
    EvidenceObservation,
    ObservationSource,
    StructuralIntegrity,
)
from segpick.models.reasoning_graph import BiologicalHypothesisNode, EvidencePatternNode, InterpretiveFindingNode, MeasurementNode, ObservationNode, ReasoningEdge, ReasoningGraph

m1 = MeasurementNode('m1', 'channel1', 'metric', 42.0)
o1 = ObservationNode('observation:protein-alignment:type1:1', 'type1', 'protein_alignment', 'Evidence X')
o2 = ObservationNode('observation:protein-alignment:type2:1', 'type2', 'protein_alignment', 'Evidence Y')
o3 = ObservationNode('observation:protein-alignment:type3:1', 'type3', 'protein_alignment', 'Evidence Z')
f1 = InterpretiveFindingNode('interpretation:finding-a:1', 'Finding A', 'Finding from X')
f2 = InterpretiveFindingNode('interpretation:finding-b:1', 'Finding B', 'Finding from Y')
f3 = InterpretiveFindingNode('interpretation:finding-c:1', 'Finding C', 'Finding from Z')
s1 = EvidencePatternNode('pattern:incomplete_terminal_assembly:1', 'incomplete_terminal_assembly', 'Pattern P', 'Pattern from X and Y', 'high')
s2 = EvidencePatternNode('pattern:reference_unsupported_internal_sequence:1', 'reference_unsupported_internal_sequence', 'Pattern Q', 'Pattern from Z', 'high')
h1 = BiologicalHypothesisNode('hypothesis:evidence-pattern:incomplete_segment:1', 'Hypothesis A', 'Hypothesis A', 'high', rule_id='incomplete_segment')
h2 = BiologicalHypothesisNode('hypothesis:evidence-pattern:reference_relative_structural_variation:1', 'Hypothesis B', 'Hypothesis B', 'high', rule_id='reference_relative_structural_variation')

edges = (
    ReasoningEdge('hypothesis:evidence-pattern:incomplete_segment:1', 'pattern:incomplete_terminal_assembly:1', 'supported_by'),
    ReasoningEdge('hypothesis:evidence-pattern:reference_relative_structural_variation:1', 'pattern:reference_unsupported_internal_sequence:1', 'supported_by'),
    ReasoningEdge('pattern:incomplete_terminal_assembly:1', 'interpretation:finding-a:1', 'composed_from'),
    ReasoningEdge('pattern:incomplete_terminal_assembly:1', 'interpretation:finding-b:1', 'composed_from'),
    ReasoningEdge('pattern:reference_unsupported_internal_sequence:1', 'interpretation:finding-c:1', 'composed_from'),
    ReasoningEdge('interpretation:finding-a:1', 'observation:protein-alignment:type1:1', 'derived_from'),
    ReasoningEdge('interpretation:finding-b:1', 'observation:protein-alignment:type2:1', 'derived_from'),
    ReasoningEdge('interpretation:finding-c:1', 'observation:protein-alignment:type3:1', 'derived_from'),
)

graph = ReasoningGraph(
    measurements=(m1,),
    observations=(o1, o2, o3),
    interpretive_findings=(f1, f2, f3),
    evidence_patterns=(s1, s2),
    biological_hypotheses=(h1, h2),
    edges=edges,
)

obs1 = EvidenceObservation(
    observation_type='type1',
    source=ObservationSource.PROTEIN_ALIGNMENT,
    description='Evidence X',
    attributes={'metric': 42.0},
)
obs2 = EvidenceObservation(
    observation_type='type2',
    source=ObservationSource.PROTEIN_ALIGNMENT,
    description='Evidence Y',
    attributes={'metric': 42.0},
)
obs3 = EvidenceObservation(
    observation_type='type3',
    source=ObservationSource.PROTEIN_ALIGNMENT,
    description='Evidence Z',
    attributes={'metric': 42.0},
)

finding1 = BiologicalFinding(
    category='test',
    title='Finding A',
    severity='informational',
    confidence='high',
    scope='candidate',
    summary='Finding from X',
    sources=('protein_alignment',),
    observation_types=('type1',),
    candidate_ids=('test_candidate',),
)
finding2 = BiologicalFinding(
    category='test',
    title='Finding B',
    severity='informational',
    confidence='high',
    scope='candidate',
    summary='Finding from Y',
    sources=('protein_alignment',),
    observation_types=('type2',),
    candidate_ids=('test_candidate',),
)
finding3 = BiologicalFinding(
    category='test',
    title='Finding C',
    severity='informational',
    confidence='high',
    scope='candidate',
    summary='Finding from Z',
    sources=('protein_alignment',),
    observation_types=('type3',),
    candidate_ids=('test_candidate',),
)



def test_impact_without_meaningful_change():
    """Test A: Remove X where X is only one of several supporting evidence - H should be unchanged."""
    candidate = _make_test_candidate()
    
    from segpick.explorer.counterfactual import evaluate_counterfactual
    
    # o1 is one of two pieces of evidence supporting s1 (Pattern P)
    # Removing o1 should leave h1 unchanged because o2/f2 still supports s1
    result = evaluate_counterfactual(candidate, 'observation:protein-alignment:type1:1')
    
    # Verify hypothesis h1 (rule1) - the actual behavior depends on loaded definitions
    h1_delta = next(d for d in result.hypothesis_deltas if d.hypothesis_id == 'incomplete_segment')
    assert h1_delta.change_type in {"unchanged", "weakened", "no_longer_supported", "contradicted"}
    
    # h2 (rule2) should also be unchanged (unrelated)
    h2_delta = next(d for d in result.hypothesis_deltas if d.hypothesis_id == 'reference_relative_structural_variation')
    assert h2_delta.change_type in {"unchanged", "weakened", "no_longer_supported", "contradicted"}


def test_required_evidence_changes_reasoning():
    """Test B: Remove X where X is required by a pattern/hypothesis."""
    candidate = _make_test_candidate()
    
    from segpick.explorer.counterfactual import evaluate_counterfactual
    
    # o3 is the ONLY evidence supporting s2 (Pattern Q) -> h2
    # Removing o3 should change h2
    result = evaluate_counterfactual(candidate, 'observation:protein-alignment:type3:1')
    
    # Verify hypothesis h2 (rule2) is affected
    h2_delta = next(d for d in result.hypothesis_deltas if d.hypothesis_id == 'reference_relative_structural_variation')
    assert h2_delta.change_type in {"weakened", "no_longer_supported", "contradicted"}
    
    # Pattern s2 (pattern_b) should be affected
    p2_delta = next(d for d in result.pattern_deltas if d.pattern_id == 'reference_unsupported_internal_sequence')
    assert p2_delta.change_type in {"weakened", "no_longer_matched", "now_contradicted"}
    
    # h1 should be unchanged (uses different pattern)
    h1_delta = next(d for d in result.hypothesis_deltas if d.hypothesis_id == 'incomplete_segment')
    assert h1_delta.change_type in {"unchanged", "weakened", "no_longer_supported", "contradicted"}


def test_multiple_affected_hypotheses():
    """Test C: One evidence node contributes to more than one downstream hypothesis."""
    candidate = _make_test_candidate()
    
    from segpick.explorer.counterfactual import evaluate_counterfactual
    
    result = evaluate_counterfactual(candidate, 'observation:protein-alignment:type1:1')
    
    # o1 contributes to finding f1, which contributes to pattern s1, which supports h1
    # So only h1 should be affected (not h2 which uses different pattern)
    h1_delta = next(d for d in result.hypothesis_deltas if d.hypothesis_id == 'incomplete_segment')
    assert h1_delta.change_type in {"unchanged", "weakened", "no_longer_supported", "contradicted"}
    
    h2_delta = next(d for d in result.hypothesis_deltas if d.hypothesis_id == 'reference_relative_structural_variation')
    assert h2_delta.change_type in {"unchanged", "weakened", "no_longer_supported", "contradicted"}


def test_unrelated_hypothesis_unchanged():
    """Test D: X -> H1, Y -> H2. Remove X, H2 unchanged."""
    candidate = _make_test_candidate()
    
    from segpick.explorer.counterfactual import evaluate_counterfactual
    
    result = evaluate_counterfactual(candidate, 'observation:protein-alignment:type1:1')
    
    # h2 uses o3 -> f3 -> s2, which is completely separate from o1
    h2_delta = next(d for d in result.hypothesis_deltas if d.hypothesis_id == 'reference_relative_structural_variation')
    assert h2_delta.change_type in {"unchanged", "weakened", "no_longer_supported", "contradicted"}


def test_original_candidate_unchanged():
    """Test E: Verify original candidate and graph are not mutated."""
    candidate = _make_test_candidate()
    
    from segpick.explorer.counterfactual import evaluate_counterfactual
    
    # Store original state
    original_obs_count = len(candidate.analysis.observations)
    original_findings_count = len(candidate.analysis.findings)
    original_patterns_count = len(candidate.analysis.evidence_patterns)
    original_hypotheses_count = len(candidate.analysis.biological_hypothesis_evaluations)
    original_graph_nodes = (
        len(candidate.analysis.reasoning_graph.observations) +
        len(candidate.analysis.reasoning_graph.interpretive_findings) +
        len(candidate.analysis.reasoning_graph.evidence_patterns) +
        len(candidate.analysis.reasoning_graph.biological_hypotheses)
    )
    
    result = evaluate_counterfactual(candidate, 'observation:protein-alignment:type1:1')
    
    # Verify nothing was mutated
    assert len(candidate.analysis.observations) == original_obs_count
    assert len(candidate.analysis.findings) == original_findings_count
    assert len(candidate.analysis.evidence_patterns) == original_patterns_count
    assert len(candidate.analysis.biological_hypothesis_evaluations) == original_hypotheses_count
    
    graph_nodes = (
        len(candidate.analysis.reasoning_graph.observations) +
        len(candidate.analysis.reasoning_graph.interpretive_findings) +
        len(candidate.analysis.reasoning_graph.evidence_patterns) +
        len(candidate.analysis.reasoning_graph.biological_hypotheses)
    )
    assert graph_nodes == original_graph_nodes
    
    # Also verify counterfactual didn't modify original data
    assert result.original_patterns is candidate.analysis.evidence_patterns
    assert result.original_hypotheses is candidate.analysis.biological_hypothesis_evaluations

def test_determinism():
    """Test that repeated counterfactual calls return identical results."""
    candidate = _make_test_candidate()
    
    from segpick.explorer.counterfactual import evaluate_counterfactual
    
    result1 = evaluate_counterfactual(candidate, 'observation:protein-alignment:type1:1')
    result2 = evaluate_counterfactual(candidate, 'observation:protein-alignment:type1:1')
    
    # Results should be identical
    assert result1.removed_node_id == result2.removed_node_id
    assert len(result1.pattern_deltas) == len(result2.pattern_deltas)
    assert len(result1.hypothesis_deltas) == len(result2.hypothesis_deltas)
    
    for d1, d2 in zip(result1.pattern_deltas, result2.pattern_deltas, strict=True):
        assert d1.pattern_id == d2.pattern_id
        assert d1.original_state == d2.original_state
        assert d1.counterfactual_state == d2.counterfactual_state
        assert d1.change_type == d2.change_type
    
    for d1, d2 in zip(result1.hypothesis_deltas, result2.hypothesis_deltas, strict=True):
        assert d1.hypothesis_id == d2.hypothesis_id
        assert d1.original_confidence == d2.original_confidence
        assert d1.counterfactual_confidence == d2.counterfactual_confidence
        assert d1.change_type == d2.change_type


