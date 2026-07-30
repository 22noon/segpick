from segpick.read_support.plotting import _merge_intervals


def test_reference_supported_intervals_merge_nearby_hsps() -> None:
    assert _merge_intervals(
        [(10, 30), (35, 50), (90, 100)],
        maximum_gap=5,
    ) == [(10, 50), (90, 100)]


def test_reference_supported_intervals_keep_large_gaps() -> None:
    assert _merge_intervals(
        [(10, 30), (57, 80)],
        maximum_gap=25,
    ) == [(10, 30), (57, 80)]
