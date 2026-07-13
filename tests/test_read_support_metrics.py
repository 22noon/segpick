from __future__ import annotations

import pytest

from segpick.read_support import (
    calculate_read_support,
    parse_depth_lines,
)


def test_parse_depth_lines() -> None:
    parsed = parse_depth_lines(
        [
            "contig_a\t1\t10\n",
            "contig_a\t2\t12\n",
            "contig_b\t1\t4\n",
        ]
    )

    assert parsed == {
        "contig_a": {
            1: 10,
            2: 12,
        },
        "contig_b": {
            1: 4,
        },
    }


def test_missing_positions_are_treated_as_zero() -> None:
    metrics = calculate_read_support(
        sequence_id="contig_a",
        position_depths={
            1: 10,
            2: 10,
            4: 10,
        },
        sequence_length=4,
        minimum_depth=3,
        terminal_fraction=0.25,
        minimum_terminal_bases=1,
    )

    assert metrics.covered_fraction == pytest.approx(0.75)
    assert metrics.mean_depth == pytest.approx(7.5)


def test_uniform_depth_has_maximum_uniformity() -> None:
    metrics = calculate_read_support(
        sequence_id="contig_a",
        position_depths={
            position: 10
            for position in range(1, 101)
        },
        sequence_length=100,
        minimum_terminal_bases=10,
    )

    assert metrics.uniformity == pytest.approx(1.0)
    assert metrics.left_terminal_support == pytest.approx(1.0)
    assert metrics.right_terminal_support == pytest.approx(1.0)
    assert metrics.read_support == pytest.approx(1.0)


def test_unsupported_right_terminal_reduces_read_support() -> None:
    depths = {
        position: 20
        for position in range(1, 101)
    }

    for position in range(91, 101):
        depths[position] = 0

    metrics = calculate_read_support(
        sequence_id="contig_a",
        position_depths=depths,
        sequence_length=100,
        minimum_depth=3,
        terminal_fraction=0.10,
        minimum_terminal_bases=10,
    )

    assert metrics.right_terminal_support == pytest.approx(0.0)
    assert metrics.read_support == pytest.approx(0.0)


def test_variable_depth_reduces_uniformity() -> None:
    depths = {
        position: (1 if position % 2 else 99)
        for position in range(1, 101)
    }

    metrics = calculate_read_support(
        sequence_id="contig_a",
        position_depths=depths,
        sequence_length=100,
        minimum_depth=1,
        minimum_terminal_bases=10,
    )

    assert metrics.covered_fraction == pytest.approx(1.0)
    assert metrics.uniformity < 0.6


def test_duplicate_positions_are_rejected() -> None:
    with pytest.raises(ValueError, match="Duplicate depth position"):
        parse_depth_lines(
            [
                "contig_a\t1\t10\n",
                "contig_a\t1\t12\n",
            ]
        )


def test_position_beyond_sequence_length_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="exceed sequence length",
    ):
        calculate_read_support(
            sequence_id="contig_a",
            position_depths={
                1: 10,
                11: 10,
            },
            sequence_length=10,
        )
