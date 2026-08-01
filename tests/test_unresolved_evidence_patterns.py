from pathlib import Path
from segpick.knowledge.engine import evaluate_evidence_patterns
from segpick.knowledge.schema import EvidencePatternDefinition
from segpick.reasoning.rules import RuleCondition
from segpick.models import CandidateContig, ContigMetadata, EvidenceObservation, Gene, Sample
from segpick.analysis.evidence_patterns import attach_evidence_patterns
from segpick.reporting.html_report import write_html_dashboard
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord


def _definition():
    return EvidencePatternDefinition(
        pattern_id="continuity_pattern",
        title="Continuity pattern",
        category="structure",
        scope="candidate",
        base_confidence="moderate",
        severity="info",
        interpretation="Continuity evidence is incomplete.",
        requires=(RuleCondition(kind="observation", value="complete_orf"),),
        supports=(RuleCondition(kind="observation", value="uniform_coverage"),),
    )


def test_include_incomplete_emits_partial_and_default_does_not():
    definition = _definition()
    no_observations = ()
    assert evaluate_evidence_patterns((definition,), no_observations, ()) == ()
    result = evaluate_evidence_patterns((definition,), no_observations, (), include_incomplete=True)
    assert len(result) == 1
    assert result[0].state == "not_evaluable"
    assert result[0].missing_required == ("observation:complete_orf",)


def test_dashboard_shows_unresolved_pattern_panel(tmp_path):
    candidate = CandidateContig(
        id="contig_a",
        record=SeqRecord(Seq("ATGAAATAA"), id="contig_a"),
        metadata=ContigMetadata(segment="1", score=1.0, confidence=1.0, cluster="A"),
    )
    sample = Sample(name="sample", genes={"VP1": Gene(name="VP1", segment="1", candidates=[candidate])})
    attach_evidence_patterns(sample, (_definition(),), ())
    assert candidate.analysis.evidence_patterns == ()
    assert candidate.analysis.unresolved_evidence_patterns
    assert candidate.analysis.unresolved_evidence_patterns[0].state == "not_evaluable"
    write_html_dashboard(sample, tmp_path)
    html = (tmp_path / "genes" / "VP1.html").read_text()
    assert "Unresolved evidence patterns" in html
    assert "Missing supporting evidence" in html


def test_unresolved_pattern_panel_is_classified_under_reasoning_tab():
    template = Path("segpick/reporting/templates/gene.html").read_text(encoding="utf-8")
    assert '"Unresolved evidence patterns"' in template
    reasoning_line = next(
        line for line in template.splitlines()
        if line.strip().startswith("reasoning: new Set(")
    )
    assert '"Unresolved evidence patterns"' in reasoning_line
