from segpick.knowledge import evaluate_hypotheses, load_active_hypotheses
from segpick.models import EvidencePatternEvaluation


def pattern(pattern_id: str, title: str, candidate_id: str = "c1") -> EvidencePatternEvaluation:
    return EvidencePatternEvaluation(
        pattern_id=pattern_id,
        title=title,
        category="assembly",
        scope="candidate",
        confidence="high",
        severity="warning",
        interpretation="Matched pattern.",
        candidate_ids=(candidate_id,),
    )


def test_builtin_hypotheses_aggregate_patterns():
    candidate_modules, gene_modules = load_active_hypotheses()
    assert any(item.hypothesis_id == "assembly_breakpoint" for item in candidate_modules)
    assert any(item.hypothesis_id == "fragmented_gene_assembly" for item in gene_modules)

    result = evaluate_hypotheses(
        candidate_modules,
        (pattern("coverage_supported_assembly_breakpoint", "Coverage-supported assembly breakpoint"),),
    )
    hypothesis = next(item for item in result if item.hypothesis_id == "assembly_breakpoint")
    assert hypothesis.supporting_patterns == ("coverage_supported_assembly_breakpoint",)
    assert hypothesis.supporting_pattern_titles == ("Coverage-supported assembly breakpoint",)
    assert hypothesis.candidate_ids == ("c1",)
    assert hypothesis.recommended_actions


def test_conflicting_pattern_reduces_hypothesis_confidence():
    candidate_modules, _ = load_active_hypotheses()
    result = evaluate_hypotheses(
        candidate_modules,
        (
            pattern("incomplete_terminal_assembly", "Possible incomplete terminal assembly"),
            pattern("divergent_but_coherent_segment", "Divergent but structurally coherent segment"),
        ),
    )
    hypothesis = next(item for item in result if item.hypothesis_id == "incomplete_segment")
    assert hypothesis.confidence == "low"
    assert hypothesis.conflicting_patterns == ("divergent_but_coherent_segment",)


def test_dashboard_renders_collapsed_pattern_hypothesis(tmp_path):
    from segpick.reporting.html_report import write_html_dashboard
    from tests.test_recommendation_reporting import make_sample

    sample, recommendations = make_sample()
    candidate_modules, _ = load_active_hypotheses()
    candidate = sample.genes["VP2"].candidates[0]
    candidate.analysis.evidence_patterns = (
        pattern("coverage_supported_assembly_breakpoint", "Coverage-supported assembly breakpoint", candidate.id),
    )
    candidate.analysis.biological_hypothesis_evaluations = evaluate_hypotheses(
        candidate_modules, candidate.analysis.evidence_patterns, candidate_ids=(candidate.id,)
    )
    write_html_dashboard(sample, tmp_path, recommendations)
    html = (tmp_path / "genes" / "VP2.html").read_text()
    assert "Biological hypotheses" in html
    assert "Possible assembly breakpoint" in html
    assert 'class="hypothesis-item biological-hypothesis-evaluation-item"' in html
    assert "Supported by evidence patterns" in html
