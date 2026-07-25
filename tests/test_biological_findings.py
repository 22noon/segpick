from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from segpick.analysis.findings import (
    candidate_biological_findings,
    gene_biological_findings,
)
from segpick.models import (
    CandidateContig,
    ContigMetadata,
    Gene,
    ProteinInterpretation,
    ProteinRelatedness,
)


def make_candidate(candidate_id: str = "contig_a") -> CandidateContig:
    return CandidateContig(
        id=candidate_id,
        record=SeqRecord(Seq("ATGAAATAA"), id=candidate_id),
        metadata=ContigMetadata(segment="1", score=1.0, confidence=1.0, cluster="c1"),
    )


def test_candidate_findings_wrap_existing_interpretations():
    candidate = make_candidate()
    candidate.analysis.protein_interpretation = ProteinInterpretation(
        structural_status="intact",
        terminal_status="complete",
        internal_indel_pattern="none",
        possible_frameshift_pattern=False,
        summary="Full-length protein recovered with no internal indels.",
        findings=(),
    )
    candidate.analysis.protein_relatedness = ProteinRelatedness(
        subject_id="ref1",
        subject_title="VP1 protein",
        percent_identity=45.0,
        query_coverage=0.95,
        subject_coverage=0.98,
        bitscore=500.0,
        evalue=1e-50,
        expected_gene_agrees=True,
        top_hit_count=10,
        top_hit_gene_agreement=1.0,
        classification="well_supported_divergent_match",
        summary="Broad gene-consistent match despite low identity.",
    )

    findings = candidate_biological_findings(candidate)

    assert [finding.title for finding in findings] == [
        "Complete protein recovered",
        "Divergent but structurally supported protein",
    ]
    assert all(finding.scope == "candidate" for finding in findings)


def test_gene_findings_report_complementary_fragments():
    gene = Gene(name="VP1", segment="1")
    first = make_candidate("head")
    second = make_candidate("tail")
    gene.candidates.extend([first, second])

    # Protein continuity derives intervals from attached BLASTX coordinates.
    from segpick.models import BlastXHit

    first.analysis.blastx = BlastXHit(
        query_id="head",
        subject_id="ref1",
        subject_title="VP1",
        percent_identity=90.0,
        alignment_length=50,
        evalue=1e-20,
        bitscore=100.0,
        query_start=1,
        query_end=150,
        subject_start=1,
        subject_end=50,
        query_length=300,
        subject_length=100,
        query_frame=1,
    )
    second.analysis.blastx = BlastXHit(
        query_id="tail",
        subject_id="ref1",
        subject_title="VP1",
        percent_identity=90.0,
        alignment_length=50,
        evalue=1e-20,
        bitscore=100.0,
        query_start=151,
        query_end=300,
        subject_start=51,
        subject_end=100,
        query_length=300,
        subject_length=100,
        query_frame=1,
    )

    findings = gene_biological_findings(gene)

    assert findings[0].title == "Possible split assembly"
    assert findings[0].candidate_ids == ("head", "tail")
    assert findings[0].scope == "gene"
