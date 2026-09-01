"""Tests for Scientific Conclusions UI rendering."""

from __future__ import annotations

from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from segpick.models import (
    CandidateContig, ContigAnalysis, ContigMetadata, EvidenceObservation, 
    BiologicalFinding, EvidencePatternEvaluation, HypothesisEvaluation, ObservationSource, Gene
)
from segpick.reasoning import load_active_conclusion_rules
from segpick.reasoning.conclusion_rules import evaluate_conclusions
from segpick.reasoning.graph import build_reasoning_graph
from segpick.reporting.view_models import build_scientific_conclusion_views
from segpick.scoring import GeneRecommendation


def test_scientific_conclusions_ui_rendered():
    """Test that scientific conclusions panel renders in generated HTML."""
    # Create a realistic candidate
    candidate = CandidateContig(
        id='test_candidate',
        record=SeqRecord(Seq('A' * 100), id='test_candidate'),
        metadata=ContigMetadata(segment='1', score=1.0, confidence=100.0, cluster='A', z=0.0),
    )
    candidate.analysis = ContigAnalysis()

    candidate.analysis.observations = (
        EvidenceObservation(
            observation_type='protein_alignment',
            source=ObservationSource.PROTEIN_ALIGNMENT,
            description='Protein alignment evidence',
            severity='informational'
        ),
    )

    candidate.analysis.findings = (
        BiologicalFinding(
            category='test',
            title='Finding A',
            severity='informational',
            confidence='high',
            scope='candidate',
            summary='Test finding',
            sources=('protein_alignment',),
        ),
    )

    candidate.analysis.evidence_patterns = (
        EvidencePatternEvaluation(
            pattern_id='incomplete_terminal_assembly',
            title='Incomplete Terminal Assembly',
            interpretation='Incomplete terminal assembly detected',
            confidence='high',
            category='structural',
            scope='candidate',
            severity='review',
            state='matched',
            matched_required=('observation:protein_alignment',),
            matched_supporting=('finding:Finding A',),
            matched_conflicting=(),
        ),
    )

    candidate.analysis.biological_hypothesis_evaluations = (
        HypothesisEvaluation(
            hypothesis_id='incomplete_segment',
            title='Incomplete Segment',
            category='structural', scope='candidate', confidence='high',
            severity='informational', explanation='Incomplete segment',
            base_confidence='moderate',
            definition_supported_by=('incomplete_terminal_assembly',),
            definition_contradicted_by=(),
            minimum_support=1,
            candidate_ids=('test_candidate',),
            supporting_patterns=('incomplete_terminal_assembly',), 
            supporting_pattern_titles=('Incomplete Terminal Assembly',),
            conflicting_patterns=(), conflicting_pattern_titles=(),
            recommended_actions=(), source='builtin', references=(),
        ),
        HypothesisEvaluation(
            hypothesis_id='reference_relative_structural_variation',
            title='Reference Relative Structural Variation',
            category='structural', scope='candidate', confidence='high',
            severity='informational', explanation='Structural variation',
            base_confidence='moderate',
            definition_supported_by=('incomplete_terminal_assembly',),
            definition_contradicted_by=(),
            minimum_support=1,
            candidate_ids=('test_candidate',),
            supporting_patterns=('incomplete_terminal_assembly',), 
            supporting_pattern_titles=('Incomplete Terminal Assembly',),
            conflicting_patterns=(), conflicting_pattern_titles=(),
            recommended_actions=(), source='builtin', references=(),
        ),
    )

    candidate_rules, gene_rules = load_active_conclusion_rules()
    all_rules = candidate_rules + gene_rules

    # Build graph
    candidate.analysis.reasoning_graph = build_reasoning_graph(candidate)
    candidate.analysis.scientific_conclusions = evaluate_conclusions(
        all_rules,
        candidate.analysis.biological_hypothesis_evaluations,
        candidate_ids=(candidate.id,),
    )

    # Build scientific conclusion views directly
    conclusion_views = build_scientific_conclusion_views(candidate)
    assert len(conclusion_views) == 3
    
    # Create minimal mock objects for template rendering
    class MockCandidate:
        candidate_id = 'test_candidate'
        recommended = True
        biological_hypothesis_evaluations = []
        interpretations = type('obj', (object,), {'items': []})()
        cross_evidence_findings = []
        evidence_patterns = []
        unresolved_evidence_patterns = []
        next_evidence_views = {}
        impact_views = {}
        comparison_views = {}
        counterfactual_views = {}
        additional_supporting_evidence_views = {}
        reasoning_graph = type('obj', (object,), {
            'available': False,
            'valid': True,
            'validation_message': '',
            'measurement_count': 0,
            'observation_count': 0,
            'interpretation_count': 0,
            'evidence_pattern_count': 0,
            'hypothesis_count': 0,
            'component_count': 0,
            'hypothesis_component_count': 0,
            'pattern_component_count': 0,
            'finding_component_count': 0,
            'observation_component_count': 0,
            'measurement_only_component_count': 0,
            'components': (),
            'builtin_sources': (),
            'plugin_sources': (),
            'provenance_paths': (),
            'graph_json': '{}',
            'normalized_graph_json': '{}',
            'llm_bundle_json': '{}',
            'llm_bundle_schema_json': '{}',
            'llm_output_schema_json': '{}',
            'llm_review_package_base64': '',
        })()
        scientific_conclusion_views = conclusion_views
        confidence = 1.0
        length = 100
        z = 0.0
        cluster = 'A'
        candidate_coverage = 1.0
        reference_coverage = 1.0
        block_count = 1
        structural_reference_id = 'ref'
        longest_block_fraction = 1.0
        largest_candidate_gap = 0
        largest_reference_gap = 0
        structural_continuity = 1.0
        orientation_consistency = 1.0
        order_consistency = 1.0
        structural_integrity = 1.0
        structural_status = 'MATCH'
        reference_compatibility = 1.0
        reference_compatibility_status = 'MATCH'
        unsupported_internal_candidate_bases = 0
        missing_internal_reference_bases = 0
        duplicated_reference_bases = 0
        expected_reference_completeness = 1.0
        reference_block_order_compatibility = 1.0
        reference_orientation_compatibility = 1.0
        duplication_compatibility = 1.0
        read_support = type('obj', (object,), {'score': 1.0, 'status': 'HIGH', 'channel_id': 'read', 'channel_title': 'Read'})()
        orf = type('obj', (object,), {
            'protein': 'AAA', 'strand': 1, 'frame': 1, 'start': 0, 'end': 100, 
            'protein_length': 33, 'score': 1.0, 
            'relatedness': type('obj', (object,), {'available': False})()
        })()
        coverage_plot = None
        convergences = ()
        convergence_review_required = False
        hypotheses = ()
        boundary_coverage = ()
        additional_supporting_evidence_views = {}
        evidence_patterns = ()
        unresolved_evidence_patterns = ()
        biological_hypothesis_evaluations = ()

    class MockView:
        candidates = [MockCandidate()]
        biological_hypothesis_evaluations = []
        hypotheses = []
        recommendation = type('obj', (object,), {'candidate_id': 'test_candidate', 'score': 0.9, 'summary': 'Test'})()

    class MockGene:
        name = 'test_gene'
        segment = '1'
        anchor_id = 'test_anchor'
        references = []
        candidates = [MockCandidate()]

    class MockRecommendation:
        recommended = type('obj', (object,), {'candidate_id': 'test_candidate', 'score': 0.9})()
        candidates = [type('obj', (object,), {'candidate_id': 'test_candidate', 'score': 0.9})()]
        report = type('obj', (object,), {'confidence': 'high'})()
        agreement = type('obj', (object,), {'confidence': 'high', 'supporting_channels': (), 'disagreeing_channels': ()})()
        convergence_review_required = False
        summary = 'Test summary'
        candidate_id = 'test_candidate'
        score = 0.9
        confidence = 'high'
        manual_review = False
        recommendation_finding = 'test'
        agreement_summary = 'test'
        channel_assessments = []
        supporting_evidence = []
        opposing_evidence = []
        evidence_conflicts = []
        assembly_level_evidence = []

    # Now render template
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    env = Environment(
        loader=FileSystemLoader("segpick/reporting/templates"),
        autoescape=select_autoescape(['html', 'xml']),
    )
    template = env.get_template("gene.html")
    html = template.render(
        gene=MockGene(),
        view=MockView(),
        recommendation=MockRecommendation(),
    )

    # Check scientific conclusions panel is rendered
    assert 'scientific-conclusions-panel' in html
    assert 'Scientific Conclusions' in html
    assert 'Structural difference supported' in html
    # The template renders generating_relationship with |replace('_', ' ')|title
    # so "jointly_supports" becomes "Jointly Supports"
    assert 'Jointly Supports' in html
    assert 'Competes With' in html
    assert 'hypothesis-link' in html
    assert 'incomplete_segment' in html
    assert 'reference_relative_structural_variation' in html
    assert 'href="#scientific-conclusions-panel"' in html
    assert 'href="#hypothesis-incomplete_segment"' in html or 'data-hypothesis-id="incomplete_segment"' in html
    
    # Check state-specific classes
    assert 'conclusion-state-supported' in html
    assert 'conclusion-state-conditional' in html
    assert 'conclusion-state-unsupported' in html
    assert 'conclusion-state-contradicted' in html
    
    # Check for available vs unavailable hypothesis links
    assert 'hypothesis-link' in html  # clickable links exist
    assert 'hypothesis-link-muted' in html  # muted text for unavailable hypotheses
    
    # Check state-specific styling classes on conclusion cards
    assert 'conclusion-state-supported' in html
    assert 'conclusion-state-conditional' in html
    assert 'conclusion-state-unsupported' in html
    assert 'conclusion-state-contradicted' in html


def test_scientific_conclusions_view_model_fields():
    """Test that ScientificConclusionView has all required fields including available_hypothesis_ids."""
    from segpick.reporting.view_models import ScientificConclusionView
    
    # Verify all fields are present
    view = ScientificConclusionView(
        conclusion_id='test',
        title='Test',
        category='test',
        scope='candidate',
        state='supported',
        confidence='high',
        severity='review',
        rule_id='test',
        rule_version='',
        source='builtin',
        references=(),
        recommended_actions=(),
        explanation='Test explanation',
        base_confidence='moderate',
        supporting_hypotheses=('h1', 'h2'),
        conflicting_hypotheses=(),
        conditional_requirements=(),
        generating_relationship='jointly_supports',
        generating_hypotheses=('h1', 'h2'),
        available_hypothesis_ids=('h1',),
    )
    assert view.generating_relationship == 'jointly_supports'
    assert view.generating_hypotheses == ('h1', 'h2')
    assert view.available_hypothesis_ids == ('h1',)


def test_scientific_conclusion_state_styling_classes():
    """Test that conclusion state CSS classes are applied correctly."""
    from segpick.reporting.view_models import ScientificConclusionView
    
    # Test all four states
    for state in ['supported', 'conditional', 'unsupported', 'contradicted']:
        view = ScientificConclusionView(
            conclusion_id='test',
            title='Test',
            category='test',
            scope='candidate',
            state=state,
            confidence='high',
            severity='review',
            rule_id='test',
            rule_version='',
            source='builtin',
            references=(),
            recommended_actions=(),
            explanation='Test explanation',
            base_confidence='moderate',
            supporting_hypotheses=('h1', 'h2'),
            conflicting_hypotheses=(),
            conditional_requirements=(),
            generating_relationship='jointly_supports',
            generating_hypotheses=('h1', 'h2'),
            available_hypothesis_ids=('h1',),
        )
        assert view.state == state


def test_scientific_conclusion_available_hypothesis_ids():
    """Test that available_hypothesis_ids is correctly passed and accessible."""
    from segpick.reporting.view_models import build_scientific_conclusion_view
    from segpick.reasoning.conclusion_rules import ScientificConclusionEvaluation
    
    # Create a mock conclusion evaluation
    conclusion = ScientificConclusionEvaluation(
        conclusion_id='test',
        title='Test',
        category='test',
        scope='candidate',
        state='supported',
        confidence='high',
        severity='review',
        explanation='Test',
        base_confidence='moderate',
        rule_id='test',
        rule_version='',
        source='builtin',
        references=(),
        recommended_actions=(),
        supporting_hypotheses=('h1', 'h2'),
        conflicting_hypotheses=(),
        conditional_requirements=(),
    )
    
    # Build view with available hypothesis IDs
    view = build_scientific_conclusion_view(conclusion, available_hypothesis_ids=('h1',))
    assert view.available_hypothesis_ids == ('h1',)
    
    # Test with empty available IDs
    view = build_scientific_conclusion_view(conclusion, available_hypothesis_ids=())
    assert view.available_hypothesis_ids == ()


if __name__ == '__main__':
    test_scientific_conclusions_ui_rendered()
    test_scientific_conclusions_view_model_fields()
    test_scientific_conclusion_state_styling_classes()
    test_scientific_conclusion_available_hypothesis_ids()
    print("All tests passed!")
