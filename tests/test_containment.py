from segpick.analysis.containment import summarise_alignments
from segpick.models import Alignment


def test_complete():
    a = Alignment("q", 100, 0, 100, "+", "t", 120, 10, 110, 99, 100, 60)
    m = summarise_alignments([a])
    assert m.query_coverage == 1.0 and m.status == "COMPLETE"


def test_fragmented():
    xs = [
        Alignment("q", 100, 0, 40, "+", "t", 120, 0, 40, 39, 40, 60),
        Alignment("q", 100, 60, 100, "+", "t", 120, 60, 100, 39, 40, 60),
    ]
    m = summarise_alignments(xs)
    assert m.fragmentation == 0.5 and m.status == "FRAGMENTED"
