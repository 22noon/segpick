import json

from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from segpick.models import (
    BiologicalHypothesis,
    BlastXHit,
    CandidateContig,
    EvidenceConvergence,
    ContainmentMetrics,
    ContigMetadata,
    Gene,
    ObservationInterval,
    Sample,
)
from segpick.reporting import (
    write_gene_json_reports,
    write_html_dashboard,
    write_recommendations_tsv,
)
from segpick.scoring import ScoringWeights, rank_gene


def make_candidate(
    candidate_id: str,
    confidence: float,
) -> CandidateContig:
    candidate = CandidateContig(
        id=candidate_id,
        record=SeqRecord(
            Seq("A" * 100),
            id=candidate_id,
        ),
        metadata=ContigMetadata(
            segment="2",
            score=1.0,
            confidence=confidence,
            cluster="A",
            z=0.0,
        ),
    )

    candidate.analysis.containment = ContainmentMetrics(
        query_length=100,
        anchor_length=100,
        query_coverage=1.0,
        anchor_coverage=1.0,
        identity=1.0,
        fragmentation=0.0,
    )

    return candidate


def make_sample() -> tuple[Sample, dict]:
    gene = Gene(name="VP2", segment="2")
    contig_a = make_candidate("contig_a", 100)
    contig_b = make_candidate("contig_b", 50)
    contig_a.analysis.blastx = BlastXHit(
        query_id="contig_a",
        subject_id="ref|VP2|A",
        subject_title="VP2 reference A",
        percent_identity=95.0,
        alignment_length=180,
        evalue=1e-40,
        bitscore=300.0,
        query_start=1,
        query_end=540,
        subject_start=1,
        subject_end=180,
        query_length=600,
        subject_length=300,
        query_frame=1,
    )
    contig_b.analysis.blastx = BlastXHit(
        query_id="contig_b",
        subject_id="ref|VP2|B",
        subject_title="VP2 reference B",
        percent_identity=92.0,
        alignment_length=135,
        evalue=1e-30,
        bitscore=250.0,
        query_start=1,
        query_end=405,
        subject_start=151,
        subject_end=285,
        query_length=450,
        subject_length=300,
        query_frame=1,
    )
    protein_observation = ObservationInterval(
        coordinate_system="reference_protein:ref|VP2|A",
        start=40,
        end=43,
        observation_type="internal_deletion",
        source="protein_alignment",
        description="Predicted protein lacks reference residues 40-43.",
    )
    coverage_observation = ObservationInterval(
        coordinate_system="reference_protein:ref|VP2|A",
        start=39,
        end=45,
        observation_type="coverage_drop",
        source="read_coverage",
        description="Sustained low read coverage overlaps positions 39-45.",
    )
    contig_a.analysis.convergences = (
        EvidenceConvergence(
            coordinate_system="reference_protein:ref|VP2|A",
            start=39,
            end=45,
            strength="moderate",
            sources=("protein_alignment", "read_coverage"),
            observation_types=("coverage_drop", "internal_deletion"),
            observations=(protein_observation, coverage_observation),
            summary="2 independent evidence sources converge on reference-protein positions 39-45.",
            candidate_id="contig_a",
        ),
    )

    contig_a.analysis.hypotheses = (
        BiologicalHypothesis(
            rule_id="possible_assembly_interruption",
            title="Possible assembly interruption",
            category="assembly",
            scope="candidate",
            confidence="high",
            severity="review",
            summary="Protein and coverage evidence support local structural review.",
            candidate_ids=("contig_a",),
            matched_required=(
                "observation:internal_deletion@protein_alignment",
                "observation:coverage_drop@read_coverage",
            ),
            matched_supporting=("finding:Local evidence convergence",),
            rule_source="builtin:default_rules.yml",
            rule_description="Tests transparent rule rendering.",
            rule_references=("PMID:12345678",),
        ),
    )
    gene.hypotheses = (
        BiologicalHypothesis(
            rule_id="possible_split_assembly",
            title="Possible split assembly",
            category="assembly",
            scope="gene",
            confidence="moderate",
            severity="review",
            summary="Complementary candidates may recover different protein regions.",
            candidate_ids=("contig_a", "contig_b"),
            matched_required=("finding:Possible split assembly",),
            rule_source="builtin:default_rules.yml",
        ),
    )

    gene.add_candidate(contig_a)
    gene.add_candidate(contig_b)

    sample = Sample(name="example")
    sample.add_gene(gene)

    recommendation = rank_gene(
        gene,
        ScoringWeights(),
    )

    return sample, {"VP2": recommendation}


def test_write_recommendations_tsv(tmp_path) -> None:
    sample, recommendations = make_sample()

    output = tmp_path / "recommendations.tsv"

    write_recommendations_tsv(
        sample,
        recommendations,
        output,
    )

    text = output.read_text()

    assert "contig_a" in text
    assert "contig_b" in text
    assert "\tTrue\t" in text


def test_gene_json_contains_recommendation(tmp_path) -> None:
    sample, recommendations = make_sample()

    write_gene_json_reports(
        sample,
        tmp_path,
        recommendations=recommendations,
    )

    payload = json.loads((tmp_path / "VP2.json").read_text())

    assert payload["recommendation"] is not None
    assert payload["recommendation"]["recommended"]["candidate_id"] == "contig_a"
    assert len(payload["recommendation"]["candidates"]) == 2
    assert payload["recommendation"]["comparisons"][0]["candidate_id"] == "contig_b"
    assert payload["recommendation"]["comparisons"][0]["reasons_not_selected"]


def test_dashboard_contains_recommendation(tmp_path) -> None:
    sample, recommendations = make_sample()

    write_html_dashboard(
        sample,
        tmp_path,
        recommendations=recommendations,
    )

    html = (tmp_path / "genes" / "VP2.html").read_text()

    assert "Recommended candidate" in html
    assert "Why this candidate?" in html
    assert "Evidence requiring review" in html
    assert "Overall assessment" in html
    assert "Status" in html
    assert "Confidence" in html
    assert "Manual review recommended." in html
    assert 'class="traffic-good"' in html
    assert "contig_a" in html
    assert "Recommended candidate" in html
    assert "Overall evidence score" in html
    assert "Protein Confidence" in html
    assert "contig_a" in html
    assert "Evidence summary" in html
    assert "Weighted contribution" in html
    assert "Effective weight" in html
    assert "evidence-summary-row" in html
    assert "evidence-bar" not in html
    assert "Protein Confidence" in html
    assert "Read support" in html
    assert "Structural integrity" in html
    assert "Protein coordinate map" in html
    assert "Expected protein position" in html
    assert "contig_a ★" in html
    assert "ref|VP2|B" in html
    assert "Assembly-level review" in html
    assert "Local evidence convergence" in html
    assert "AA 39–45" in html
    assert "Biological interpretation" in html
    assert "Possible assembly interruption" in html
    assert "Possible split assembly" in html
    assert "Required matches" in html
    assert "Supporting matches" in html
    assert "Conflicting matches" in html
    assert "builtin:default_rules.yml" in html
    assert "PMID:12345678" in html

    assert "selectCandidate" in html
    assert "DashboardState" in html
    assert "candidate-row" in html
    assert "candidate-detail" in html
    assert 'data-sequence-id="contig_a"' in html

    assert "Runner-up" in html
    assert "Score gap" in html
    assert "Why not the runner-up?" in html
    assert "Evidence favouring the runner-up" in html or "Why not the runner-up?" in html

    index_html = (tmp_path / "index.html").read_text()

    assert "VP2" in index_html
    assert "contig_a" in index_html
    assert "genes/VP2.html" in index_html
    assert "Candidates" in index_html
    assert "Recommended candidate" in index_html
    assert "Segment-level assembly curation summary" in index_html
    assert "Confidence" in index_html
    assert "Manual review" in index_html
    assert "Assessment" in index_html
    assert "LOW" in index_html
    assert "Required" in index_html
    assert "distributed across multiple contigs" in index_html
    assert "Protein continuity" in index_html
    assert "Possible split assembly" in index_html




def test_dashboard_shows_empty_hypothesis_state(tmp_path) -> None:
    sample, recommendations = make_sample()
    gene = sample.genes["VP2"]
    gene.hypotheses = ()
    for candidate in gene.candidates:
        candidate.analysis.hypotheses = ()

    write_html_dashboard(
        sample,
        tmp_path,
        recommendations=recommendations,
    )

    html = (tmp_path / "genes" / "VP2.html").read_text()

    assert "Biological interpretation" in html
    assert "No rule-based biological hypotheses were generated." in html
    assert "No current hypothesis rule matched" in html


def test_gene_template_contains_reference_dotplot_panel():
    from pathlib import Path
    from segpick.reporting import html_report

    template = Path(html_report.__file__).resolve().parent / "templates" / "gene.html"
    content = template.read_text()
    assert "Candidate versus closest nucleotide reference" in content
    assert "reference_dotplots_json" in content
    assert "updateReferenceDotplot" in content
    assert "Candidates aligned to shared nucleotide reference" in content
    assert "reference_overviews" in content


def test_gene_template_explains_structural_integrity_score():
    from pathlib import Path
    from segpick.reporting import html_report

    template = Path(html_report.__file__).resolve().parent / "templates" / "gene.html"
    content = template.read_text()
    assert "How the score is calculated" in content
    assert "orientation consistency" in content.lower()
    assert "Nucleotide percentage identity is intentionally excluded" in content
