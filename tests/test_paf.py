from pathlib import Path

from segpick.io.paf import read_paf


def test_read_paf(tmp_path: Path):
    paf = tmp_path / "test.paf"
    paf.write_text("query\t100\t0\t90\t+\ttarget\t120\t10\t100\t88\t90\t60\n")
    a = read_paf(paf)
    assert len(a) == 1
    assert a[0].query_id == "query"
    assert a[0].target_id == "target"
    assert round(a[0].identity, 3) == 0.978
