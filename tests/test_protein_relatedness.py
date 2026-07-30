from segpick.analysis.blastx import calculate_protein_relatedness
from segpick.models import BlastXHit


def hit(subject_id, identity=45.0, qcov=0.9, scov=0.95, bitscore=300.0):
    qlen = 1000
    slen = 300
    return BlastXHit(
        query_id="contig1",
        subject_id=subject_id,
        subject_title=f"Bluetongue virus {subject_id.split('|')[1]} protein",
        percent_identity=identity,
        alignment_length=285,
        evalue=1e-50,
        bitscore=bitscore,
        query_start=1,
        query_end=round(qlen * qcov),
        subject_start=1,
        subject_end=round(slen * scov),
        query_length=qlen,
        subject_length=slen,
        query_frame=1,
    )


def test_divergent_broad_match_is_not_treated_as_poor_assembly():
    result = calculate_protein_relatedness((hit("ref|VP2"),), "VP2")
    assert result.classification == "well_supported_divergent_match"
    assert "divergent lineage" in result.summary


def test_top_hit_gene_disagreement_is_ambiguous():
    hits = tuple(
        hit(f"ref|VP5|{index}", identity=70.0, bitscore=300 - index)
        for index in range(5)
    )
    result = calculate_protein_relatedness(hits, "VP2")
    assert result.classification == "ambiguous_assignment"
    assert result.top_hit_gene_agreement == 0.0


def test_partial_match_is_reported_separately():
    result = calculate_protein_relatedness(
        (hit("ref|VP2", identity=80.0, qcov=0.3, scov=0.4),),
        "VP2",
    )
    assert result.classification == "partial_match"
