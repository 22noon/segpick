from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from segpick.analysis.boundary_coverage import assess_reference_boundaries
from segpick.models import BlastNHSP, CandidateContig, ContigMetadata, ReferenceDotplot


def _candidate(depths):
    candidate = CandidateContig(
        id="contig_a",
        record=SeqRecord(Seq("A" * 200), id="contig_a"),
        metadata=ContigMetadata(segment="2", score=1, confidence=1, cluster="x"),
    )
    candidate.analysis.depth_profile = depths
    candidate.analysis.reference_dotplot = ReferenceDotplot(
        candidate_id="contig_a",
        reference_id="ref",
        query_length=200,
        reference_length=200,
        hsps=(
            BlastNHSP("contig_a", "ref", 200, 200, 95, 80, 0, 0, 1, 80, 1, 80, 1e-20, 100),
            BlastNHSP("contig_a", "ref", 200, 200, 95, 80, 0, 0, 121, 200, 121, 200, 1e-20, 100),
        ),
        query_coverage=0.8,
        reference_coverage=0.8,
        identity_min=95,
        identity_max=95,
        output_path="x.tsv",
        reused_existing=False,
    )
    return candidate


def test_boundary_coverage_detects_gap():
    depths = {position: (20 if position < 81 or position > 120 else 0) for position in range(1, 201)}
    result = assess_reference_boundaries(_candidate(depths), minimum_depth=3)
    assert len(result) == 1
    assert result[0].classification == "coverage_gap"
    assert result[0].gap_start == 81
    assert result[0].gap_end == 120


def test_boundary_coverage_detects_continuous_coverage():
    depths = {position: 20 for position in range(1, 201)}
    result = assess_reference_boundaries(_candidate(depths), minimum_depth=3)
    assert result[0].classification == "continuous_coverage"


def test_boundary_coverage_detects_supported_sequence_with_left_junction_drop():
    depths = {}
    for position in range(1, 201):
        if 81 <= position <= 90:
            depths[position] = 3
        else:
            depths[position] = 20
    result = assess_reference_boundaries(_candidate(depths), minimum_depth=3)
    item = result[0]
    assert item.regional_sequence_supported is True
    assert item.left_junction_smooth is False
    assert item.right_junction_smooth is True
    assert item.classification == "supported_with_junction_discontinuity"
    assert item.placement_interpretation == "sequence_supported_placement_uncertain"


def test_boundary_coverage_reports_smooth_junction_ratios():
    depths = {position: 20 for position in range(1, 201)}
    item = assess_reference_boundaries(_candidate(depths), minimum_depth=3)[0]
    assert item.left_junction_ratio == 1.0
    assert item.right_junction_ratio == 1.0
    assert item.both_junctions_smooth is True
    assert item.placement_interpretation == "placement_depth_supported"
