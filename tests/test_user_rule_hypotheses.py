from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from segpick.analysis.hypotheses import candidate_biological_hypotheses
from segpick.models import BiologicalFinding, CandidateContig, ContigMetadata
from segpick.reasoning import load_rule_file


def test_user_rule_generates_traceable_hypothesis(tmp_path):
    rule_file = tmp_path / "custom.yml"
    rule_file.write_text(
        """
rules:
  - id: custom_complete
    title: Laboratory complete-protein rule
    description: Demonstrates user-defined reasoning.
    category: custom
    scope: candidate
    severity: informational
    base_confidence: moderate
    summary: A complete protein satisfies the laboratory rule.
    requires:
      - finding: Complete protein recovered
    references:
      - doi:10.0000/example
"""
    )
    candidate = CandidateContig(
        id="contig_a",
        record=SeqRecord(Seq("ATGAAATAA"), id="contig_a"),
        metadata=ContigMetadata(segment="1", score=1.0, confidence=1.0, cluster="c1"),
    )
    candidate.analysis.findings = (
        BiologicalFinding(
            category="protein",
            title="Complete protein recovered",
            severity="informational",
            confidence="high",
            scope="candidate",
            summary="Complete.",
            sources=("protein_alignment",),
            candidate_ids=(candidate.id,),
        ),
    )

    hypothesis = candidate_biological_hypotheses(
        candidate,
        load_rule_file(rule_file),
    )[0]

    assert hypothesis.rule_id == "custom_complete"
    assert hypothesis.rule_source == str(rule_file)
    assert hypothesis.rule_description == "Demonstrates user-defined reasoning."
    assert hypothesis.rule_references == ("doi:10.0000/example",)
