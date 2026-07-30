from pathlib import Path

from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from segpick.models import CandidateContig, ContigMetadata, Gene, ReferenceSequence, Sample
from segpick.reporting.html_report import write_html_dashboard


def test_dashboard_writes_local_plotly_asset_and_loads_it(tmp_path: Path) -> None:
    candidate = CandidateContig(
        id="contig1",
        record=SeqRecord(Seq("ATGAAATAG"), id="contig1"),
        metadata=ContigMetadata(segment="1", score=1.0, confidence=1.0, cluster="cluster1"),
    )
    reference = ReferenceSequence(
        accession="ref1",
        record=SeqRecord(Seq("ATGAAATAG"), id="ref1"),
    )
    gene = Gene(name="VP1", segment="1", candidates=[candidate], references=[reference])
    sample = Sample(name="sample", genes={"VP1": gene})

    index = write_html_dashboard(sample, tmp_path)

    assert index.exists()
    asset = tmp_path / "assets" / "plotly.min.js"
    assert asset.exists()
    assert asset.stat().st_size > 100_000

    gene_page = tmp_path / "genes" / "VP1.html"
    html = gene_page.read_text(encoding="utf-8")
    assert '<script src="../assets/plotly.min.js"></script>' in html
