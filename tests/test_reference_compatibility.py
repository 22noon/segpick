from segpick.analysis.reference_compatibility import reference_compatibility_from_dotplot
from segpick.models import BlastNHSP, ReferenceDotplot


def hsp(qs, qe, ss, se, *, qlen=3000, slen=3000):
    return BlastNHSP(
        query_id="candidate", subject_id="reference",
        query_length=qlen, subject_length=slen,
        percent_identity=90.0, alignment_length=abs(qe-qs)+1,
        mismatches=0, gap_opens=0, query_start=qs, query_end=qe,
        subject_start=ss, subject_end=se, evalue=0.0, bitscore=100.0,
    )


def dotplot(*hsps):
    return ReferenceDotplot(
        candidate_id="candidate", reference_id="reference",
        query_length=3000, reference_length=3000, hsps=tuple(hsps),
        query_coverage=0.9, reference_coverage=0.9,
        identity_min=90.0, identity_max=90.0,
        output_path="x.tsv", reused_existing=False,
    )


def test_reference_compatible_collinear_blocks():
    result = reference_compatibility_from_dotplot(dotplot(
        hsp(1, 1500, 1, 1500), hsp(1501, 3000, 1501, 3000)
    ))
    assert result.unsupported_internal_candidate_bases == 0
    assert result.missing_internal_reference_bases == 0
    assert result.block_order_compatibility == 1.0
    assert result.orientation_compatibility == 1.0


def test_detects_unsupported_internal_candidate_sequence():
    result = reference_compatibility_from_dotplot(dotplot(
        hsp(1, 1566, 1, 1566), hsp(1910, 2891, 1567, 2548)
    ))
    assert result.unsupported_internal_candidate_bases == 343
    assert result.internal_candidate_compatibility < 1.0


def test_detects_reordered_reference_blocks():
    result = reference_compatibility_from_dotplot(dotplot(
        hsp(1, 1000, 2001, 3000), hsp(1001, 2000, 1, 1000)
    ))
    assert result.block_order_compatibility == 0.0
    assert result.status in {"REVIEW", "REFERENCE_INCOMPATIBLE"}


def test_detects_duplicate_reference_mapping():
    result = reference_compatibility_from_dotplot(dotplot(
        hsp(1, 1000, 1, 1000), hsp(1501, 2500, 501, 1500)
    ))
    assert result.duplicated_reference_bases == 500
    assert result.duplication_compatibility < 1.0


def test_reference_compatibility_assessment_reports_duplicated_mapping():
    from types import SimpleNamespace
    from segpick.analysis.evidence_assessments import reference

    compatibility = reference_compatibility_from_dotplot(dotplot(
        hsp(1, 1000, 1, 1000), hsp(1501, 2500, 501, 1500)
    ))
    candidate = SimpleNamespace(
        analysis=SimpleNamespace(reference_compatibility=compatibility)
    )
    assessment = reference(candidate, SimpleNamespace())
    finding_ids = {assessment.key_finding.finding_id} | {
        item.finding_id for item in assessment.supporting_findings
    }
    assert "duplicated_reference_mapping" in finding_ids
    assert any(item["name"] == "duplicated_reference_bases" for item in assessment.measurements)
