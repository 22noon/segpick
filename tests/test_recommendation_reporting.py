import json

from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from segpick.models import (
    CandidateContig,
    ContainmentMetrics,
    ContigMetadata,
    Gene,
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
    gene.add_candidate(make_candidate("contig_a", 100))
    gene.add_candidate(make_candidate("contig_b", 50))

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


def test_dashboard_contains_recommendation(tmp_path) -> None:
    sample, recommendations = make_sample()

    write_html_dashboard(
        sample,
        tmp_path,
        recommendations=recommendations,
    )

    html = (tmp_path / "genes" / "VP2.html").read_text()

    assert "Recommended candidate" in html
    assert "contig_a" in html
    assert "Recommended candidate" in html
    assert "Overall evidence score" in html
    assert "Protein Confidence" in html
    assert "contig_a" in html
    assert "Contribution" in html
    assert "Effective weight" in html
    assert "Protein Confidence" in html
    assert "Read support" in html

    assert "selectCandidate" in html
    assert "DashboardState" in html
    assert "candidate-row" in html
    assert "candidate-detail" in html
    assert 'data-sequence-id="contig_a"' in html

    assert "Runner-up" in html
    assert "Score gap" in html

    index_html = (tmp_path / "index.html").read_text()

    assert "VP2" in index_html
    assert "contig_a" in index_html
    assert "genes/VP2.html" in index_html
    assert "Candidates" in index_html
    assert "Recommended candidate" in index_html


