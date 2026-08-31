"""Tests for the Scientific Conclusion evaluation layer."""

from __future__ import annotations

from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from segpick.models import (
    BiologicalFinding,
    CandidateContig,
    ContigAnalysis,
    ContigMetadata,
    EvidenceObservation,
    EvidencePatternEvaluation,
    HypothesisEvaluation,
    ObservationSource,
)
from segpick.models.reasoning_graph import (
    BiologicalHypothesisNode,
    EvidencePatternNode,
    InterpretiveFindingNode,
    MeasurementNode,
    ObservationNode,
    ReasoningEdge,
    ReasoningGraph,
)
from segpick.reasoning.conclusion_rules import (
    ConclusionCondition,
    ConclusionRule,
    HypothesisRelationship,
    evaluate_conclusions,
)


def _make_test_candidate():
    """Create a test candidate with a complete reasoning graph and analysis data."""
    from segpick.models import (
        ContainmentMetrics,
        StructuralIntegrity,
    )

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
        aligned_query_bp=100,
        aligned_anchor_bp=100,
        query_length=100,
        anchor_length=100,
        query_coverage=1.0,
        anchor_coverage=1.0,
        identity=0.99,
        fragmentation=0.0,
        n_blocks=0,
        status='HIGH',
    )

    # Mock observations and findings
    from segpick.models import (
        HypothesisEvaluation,
    )

    obs1 = EvidenceObservation(
        observation_type='type1', source=ObservationSource.PROTEIN_ALIGNMENT,
        description='Evidence X', attributes={'metric': 42.0}
    )
    obs2 = EvidenceObservation(
        observation_type='type2', source=ObservationSource.PROTEIN_ALIGNMENT,
        description='Evidence Y', attributes={'metric': 42.0}
    )

    finding1 = BiologicalFinding(
        category='test', title='Finding A', severity='informational',
        confidence='high', scope='candidate', summary='Finding from X',
        sources=('protein_alignment',), candidate_ids=('test_candidate',)
    )
    finding2 = BiologicalFinding(
        category='test', title='Finding B', severity='informational',
        confidence='high', scope='candidate', summary='Finding from Y',
        sources=('protein_alignment',), candidate_ids=('test_candidate',)
    )
    finding3 = BiologicalFinding(
        category='test', title='Finding C', severity='informational',
        confidence='high', scope='candidate', summary='Finding from Z',
        sources=('protein_alignment',), candidate_ids=('test_candidate',)
    )

    pattern1 = EvidencePatternEvaluation(
        pattern_id='incomplete_terminal_assembly',
        title='Pattern P',
        category='test', scope='candidate', confidence='high',
        severity='review', interpretation='Pattern from X and Y',
        candidate_ids=('test_candidate',),
        matched_required=('finding:Finding A', 'finding:Finding B'),
        matched_supporting=(),
        matched_conflicting=(),
        suggested_actions=(), source='builtin', references=(),
        evidence_provenance=(), state='matched',
        missing_required=(), missing_supporting=(),
        unused_findings=(),
    )
    pattern2 = EvidencePatternEvaluation(
        pattern_id='reference_unsupported_internal_sequence',
        title='Pattern Q',
        category='test', scope='candidate', confidence='high',
        severity='review', interpretation='Pattern from Z',
        candidate_ids=('test_candidate',),
        matched_required=('finding:Finding C',),
        matched_supporting=(),
        matched_conflicting=(),
        suggested_actions=(), source='builtin', references=(),
        evidence_provenance=(), state='matched',
        missing_required=(), missing_supporting=(),
        unused_findings=(),
    )

    hyp1 = HypothesisEvaluation(
        hypothesis_id='incomplete_segment',
        title='Hypothesis A',
        category='test', scope='candidate', confidence='high',
        severity='informational', explanation='Hypothesis A',
        base_confidence='moderate',
        definition_supported_by=('pattern_a',),
        definition_contradicted_by=(),
        minimum_support=1,
        candidate_ids=('test_candidate',),
        supporting_patterns=('incomplete_terminal_assembly',),
        supporting_pattern_titles=('Pattern P',),
        conflicting_patterns=(),
        conflicting_pattern_titles=(),
        recommended_actions=(), source='builtin', references=(),
    )
    hyp2 = HypothesisEvaluation(
        hypothesis_id='reference_relative_structural_variation',
        title='Hypothesis B',
        category='test', scope='candidate', confidence='high',
        severity='informational', explanation='Hypothesis B',
        base_confidence='moderate',
        definition_supported_by=('pattern_b',),
        definition_contradicted_by=(),
        minimum_support=1,
        candidate_ids=('test_candidate',),
        supporting_patterns=('reference_unsupported_internal_sequence',),
        supporting_pattern_titles=('Pattern Q',),
        conflicting_patterns=(),
        conflicting_pattern_titles=(),
        recommended_actions=(), source='builtin', references=(),
    )

    candidate = CandidateContig(
        id='test_candidate',
        record=SeqRecord(Seq('A' * 100), id='test_candidate'),
        metadata=ContigMetadata(segment='1', score=1.0, confidence=100.0, cluster='A', z=0.0),
    )
    candidate.analysis = ContigAnalysis()
    candidate.analysis.reasoning_graph = ReasoningGraph(
        measurements=(m1,),
        observations=(o1, o2, o3),
        interpretive_findings=(f1, f2, f3),
        evidence_patterns=(s1, s2),
        biological_hypotheses=(h1, h2),
        edges=edges,
    )
    candidate.analysis.evidence_patterns = (pattern1, pattern2)
    candidate.analysis.biological_hypothesis_evaluations = (hyp1, hyp2)
    candidate.analysis.findings = (finding1, finding2, finding3)

    return candidate


def test_two_supported_complementary_hypotheses_supported_conclusion():
    """Two supported hypotheses with jointly_supports relationship -> supported conclusion."""
    candidate = _make_test_candidate()

    # Create a rule with jointly_supports relationship
    rule = ConclusionRule(
        rule_id='structural_difference_supported',
        title='Structural difference supported',
        category='structural',
        scope='candidate',
        severity='review',
        base_confidence='high',
        summary='Structural difference supported by evidence',
        description='Both incomplete assembly and structural variation hypotheses are supported',
        conditions=(
            ConclusionCondition(target='incomplete_segment', state='supported', role='required'),
            ConclusionCondition(target='reference_relative_structural_variation', state='supported', role='required'),
        ),
        relationships=(
            HypothesisRelationship(type='jointly_supports', targets=('incomplete_segment', 'reference_relative_structural_variation')),
        ),
        minimum_supported=2,
        minimum_confidence='high',
    )

    candidate = _make_test_candidate()
    results = evaluate_conclusions((rule,), candidate.analysis.biological_hypothesis_evaluations)

    assert len(results) == 1
    result = results[0]
    assert result.state == 'supported'
    assert result.conclusion_id == 'structural_difference_supported'
    assert 'incomplete_segment' in result.supporting_hypotheses
    assert 'reference_relative_structural_variation' in result.supporting_hypotheses


def test_required_hypothesis_unresolved_conditional():
    """One required hypothesis unresolved -> conditional conclusion."""
    rule = ConclusionRule(
        rule_id='incomplete_with_ambiguous_variation',
        title='Incomplete with ambiguous variation',
        category='structural',
        scope='candidate',
        severity='review',
        base_confidence='high',
        summary='Incomplete assembly with ambiguous structural variation',
        conditions=(
            ConclusionCondition(target='incomplete_segment', state='supported', role='required'),
            ConclusionCondition(target='reference_relative_structural_variation', state='supported', role='required'),
        ),
        relationships=(
            HypothesisRelationship(type='jointly_supports', targets=('incomplete_segment', 'reference_relative_structural_variation')),
        ),
        minimum_supported=2,
    )

    candidate = _make_test_candidate()
    # Modify H2 to be unresolved
    hyp1 = candidate.analysis.biological_hypothesis_evaluations[0]
    hyp2 = HypothesisEvaluation(
        hypothesis_id='reference_relative_structural_variation',
        title='Hypothesis B',
        category='test', scope='candidate', confidence='provisional',
        severity='informational', explanation='Hypothesis B',
        base_confidence='moderate',
        definition_supported_by=('pattern:pattern-b:1',),
        definition_contradicted_by=(),
        minimum_support=1,
        candidate_ids=('test_candidate',),
        supporting_patterns=(),
        supporting_pattern_titles=(),
        conflicting_patterns=(),
        conflicting_pattern_titles=(),
        recommended_actions=(), source='builtin', references=(),
    )
    candidate.analysis.biological_hypothesis_evaluations = (hyp1, hyp2)

    results = evaluate_conclusions((rule,), candidate.analysis.biological_hypothesis_evaluations)
    assert len(results) == 1
    result = results[0]
    assert result.state == 'conditional'


def test_supported_competing_with_unresolved_conditional():
    """Supported hypothesis competing with unresolved -> conditional."""
    rule = ConclusionRule(
        rule_id='structural_variation_vs_artefact',
        title='Structural variation vs artefact',
        category='structural',
        scope='candidate',
        severity='review',
        base_confidence='high',
        summary='Structural variation vs assembly artefact',
        conditions=(
            ConclusionCondition(target='true_structural_variation', state='supported', role='required'),
        ),
        relationships=(
            HypothesisRelationship(type='competes_with', targets=('true_structural_variation', 'assembly_artefact')),
        ),
        minimum_supported=1,
    )

    candidate = _make_test_candidate()
    # Replace hypotheses
    hyp1 = HypothesisEvaluation(
        hypothesis_id='true_structural_variation',
        title='True structural variation',
        category='test', scope='candidate', confidence='high',
        severity='informational', explanation='True variation',
        base_confidence='moderate',
        definition_supported_by=('pattern_a',),
        definition_contradicted_by=(),
        minimum_support=1,
        candidate_ids=('test_candidate',),
        supporting_patterns=('pattern_a',), supporting_pattern_titles=('Pattern A',),
        conflicting_patterns=(), conflicting_pattern_titles=(),
        recommended_actions=(), source='builtin', references=(),
    )
    hyp2 = HypothesisEvaluation(
        hypothesis_id='assembly_artefact',
        title='Assembly artefact',
        category='test', scope='candidate', confidence='provisional',
        severity='informational', explanation='Assembly artefact',
        base_confidence='moderate',
        definition_supported_by=('pattern_b',),
        definition_contradicted_by=(),
        minimum_support=1,
        candidate_ids=('test_candidate',),
        supporting_patterns=(), supporting_pattern_titles=(),
        conflicting_patterns=(), conflicting_pattern_titles=(),
        recommended_actions=(), source='builtin', references=(),
    )
    candidate.analysis.biological_hypothesis_evaluations = (hyp1, hyp2)

    results = evaluate_conclusions((rule,), candidate.analysis.biological_hypothesis_evaluations)
    assert len(results) == 1
    result = results[0]
    assert result.state == 'conditional'


def test_supported_competing_with_supported_conflicting():
    """Supported hypothesis competing with supported conflicting hypothesis -> contradicted."""
    rule = ConclusionRule(
        rule_id='structural_variation_vs_artefact',
        title='Structural variation vs artefact',
        category='structural',
        scope='candidate',
        severity='warning',
        base_confidence='high',
        summary='Structural variation vs assembly artefact',
        conditions=(
            ConclusionCondition(target='true_structural_variation', state='supported', role='required'),
            ConclusionCondition(target='assembly_artefact', state='supported', role='conflicting'),
        ),
        relationships=(
            HypothesisRelationship(type='competes_with', targets=('true_structural_variation', 'assembly_artefact')),
        ),
        minimum_supported=1,
    )

    candidate = _make_test_candidate()
    hyp1 = HypothesisEvaluation(
        hypothesis_id='true_structural_variation',
        title='True structural variation',
        category='test', scope='candidate', confidence='high',
        severity='informational', explanation='True variation',
        base_confidence='moderate',
        definition_supported_by=('pattern_a',),
        definition_contradicted_by=(),
        minimum_support=1,
        candidate_ids=('test_candidate',),
        supporting_patterns=('pattern_a',), supporting_pattern_titles=('Pattern A',),
        conflicting_patterns=(), conflicting_pattern_titles=(),
        recommended_actions=(), source='builtin', references=(),
    )
    hyp2 = HypothesisEvaluation(
        hypothesis_id='assembly_artefact',
        title='Assembly artefact',
        category='test', scope='candidate', confidence='high',
        severity='informational', explanation='Assembly artefact',
        base_confidence='moderate',
        definition_supported_by=('pattern_b',),
        definition_contradicted_by=(),
        minimum_support=1,
        candidate_ids=('test_candidate',),
        supporting_patterns=('pattern_b',), supporting_pattern_titles=('Pattern B',),
        conflicting_patterns=(), conflicting_pattern_titles=(),
        recommended_actions=(), source='builtin', references=(),
    )
    candidate.analysis.biological_hypothesis_evaluations = (hyp1, hyp2)

    results = evaluate_conclusions((rule,), candidate.analysis.biological_hypothesis_evaluations)
    assert len(results) == 1
    result = results[0]
    assert result.state == 'contradicted'


def test_unrelated_unresolved_in_relationship_becomes_conditional():
    """Unrelated unresolved hypothesis in a jointly_supports relationship makes conclusion conditional."""
    rule = ConclusionRule(
        rule_id='incomplete_segment_conclusion',
        title='Incomplete segment conclusion',
        category='structural',
        scope='candidate',
        severity='review',
        base_confidence='high',
        summary='Incomplete segment conclusion',
        conditions=(
            ConclusionCondition(target='incomplete_segment', state='supported', role='required'),
        ),
        relationships=(
            HypothesisRelationship(type='jointly_supports', targets=('incomplete_segment', 'unrelated_hypothesis')),
        ),
        minimum_supported=1,
    )

    candidate = _make_test_candidate()
    # Add an unrelated unresolved hypothesis
    hyp1 = candidate.analysis.biological_hypothesis_evaluations[0]
    hyp2 = HypothesisEvaluation(
        hypothesis_id='unrelated_hypothesis',
        title='Unrelated hypothesis',
        category='test', scope='candidate', confidence='provisional',
        severity='informational', explanation='Unrelated',
        base_confidence='moderate',
        definition_supported_by=('pattern_c',),
        definition_contradicted_by=(),
        minimum_support=1,
        candidate_ids=('test_candidate',),
        supporting_patterns=(), supporting_pattern_titles=(),
        conflicting_patterns=(), conflicting_pattern_titles=(),
        recommended_actions=(), source='builtin', references=(),
    )
    candidate.analysis.biological_hypothesis_evaluations = (hyp1, hyp2)

    results = evaluate_conclusions((rule,), candidate.analysis.biological_hypothesis_evaluations)
    # The unrelated hypothesis is in the jointly_supports relationship but is unresolved
    # This makes the conclusion conditional
    assert len(results) == 1
    result = results[0]
    assert result.state == 'conditional'

# Keep the old function name for backwards compatibility
test_unrelated_unresolved_no_effect = test_unrelated_unresolved_in_relationship_becomes_conditional


def test_single_hypothesis_no_relationship_rejected():
    """Single hypothesis without relationship cannot produce a conclusion."""
    rule = ConclusionRule(
        rule_id='single_hyp_conclusion',
        title='Single hypothesis conclusion',
        category='test',
        scope='candidate',
        severity='informational',
        base_confidence='high',
        summary='Single hypothesis conclusion',
        conditions=(
            ConclusionCondition(target='incomplete_segment', state='supported', role='required'),
        ),
        relationships=(),  # No relationship
        minimum_supported=1,
    )

    candidate = _make_test_candidate()
    results = evaluate_conclusions((rule,), candidate.analysis.biological_hypothesis_evaluations)
    assert len(results) == 0  # Should be rejected
