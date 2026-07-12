from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from segpick.models import Gene, ReferenceSequence
from segpick.reporting.html_report import _table_rows


def test_reference_missing_numeric_metadata_uses_none():
    gene = Gene(name="VP2", segment="2")
    gene.add_reference(ReferenceSequence("REF1", SeqRecord(Seq("ATGC"), id="REF1")))
    rows = _table_rows(gene)
    assert rows[0]["confidence"] is None
    assert rows[0]["z"] is None
    assert rows[0]["cluster"] is None
