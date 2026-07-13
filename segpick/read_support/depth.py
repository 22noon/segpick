from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from statistics import fmean, median, pstdev

from segpick.models import ReadSupportMetrics


def parse_depth_lines(
    lines: Iterable[str],
) -> dict[str, dict[int, int]]:
    """Parse three-column samtools depth output.

    Expected columns:

        sequence_id    one_based_position    depth

    Returns:
        A nested dictionary:

        {
            "contig_a": {
                1: 12,
                2: 15,
            }
        }
    """

    depths: dict[str, dict[int, int]] = {}

    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        fields = line.split()

        if len(fields) < 3:
            raise ValueError(
                f"Invalid depth line {line_number}: expected at least "
                f"3 columns, found {len(fields)}"
            )

        sequence_id = fields[0]

        try:
            position = int(fields[1])
            depth = int(fields[2])
        except ValueError as error:
            raise ValueError(
                f"Invalid numeric value on depth line {line_number}: "
                f"{line!r}"
            ) from error

        if position < 1:
            raise ValueError(
                f"Depth position must be one-based and positive; "
                f"line {line_number} has {position}"
            )

        if depth < 0:
            raise ValueError(
                f"Depth cannot be negative; line {line_number} has {depth}"
            )

        sequence_depths = depths.setdefault(sequence_id, {})

        if position in sequence_depths:
            raise ValueError(
                f"Duplicate depth position for {sequence_id!r}: {position}"
            )

        sequence_depths[position] = depth

    return depths


def parse_depth_file(
    path: str | Path,
) -> dict[str, dict[int, int]]:
    """Read a samtools depth file."""

    path = Path(path)

    with path.open() as handle:
        return parse_depth_lines(handle)


def _depth_vector(
    position_depths: dict[int, int],
    sequence_length: int,
) -> list[int]:
    """Construct a complete depth vector, filling missing positions with zero."""

    if sequence_length < 1:
        raise ValueError("sequence_length must be greater than zero")

    invalid_positions = [
        position
        for position in position_depths
        if position > sequence_length
    ]

    if invalid_positions:
        raise ValueError(
            "Depth positions exceed sequence length: "
            + ", ".join(str(position) for position in sorted(invalid_positions))
        )

    return [
        position_depths.get(position, 0)
        for position in range(1, sequence_length + 1)
    ]


def _terminal_window_size(
    sequence_length: int,
    terminal_fraction: float,
    minimum_terminal_bases: int,
) -> int:
    if not 0 < terminal_fraction <= 0.5:
        raise ValueError(
            "terminal_fraction must be greater than zero and no more than 0.5"
        )

    if minimum_terminal_bases < 1:
        raise ValueError("minimum_terminal_bases must be at least 1")

    requested = max(
        minimum_terminal_bases,
        round(sequence_length * terminal_fraction),
    )

    return min(requested, max(1, sequence_length // 2))


def _terminal_support(
    terminal_depths: list[int],
    internal_median: float,
) -> float:
    """Compare terminal mean depth with internal median depth."""

    if not terminal_depths:
        return 0.0

    terminal_mean = fmean(terminal_depths)

    if internal_median <= 0:
        return 1.0 if terminal_mean > 0 else 0.0

    return min(1.0, terminal_mean / internal_median)


def calculate_read_support(
    sequence_id: str,
    position_depths: dict[int, int],
    sequence_length: int,
    *,
    minimum_depth: int = 3,
    terminal_fraction: float = 0.05,
    minimum_terminal_bases: int = 50,
) -> ReadSupportMetrics:
    """Calculate primitive read-support metrics for one sequence.

    Missing positions are treated as zero depth, so this remains safe even when
    the input was not generated with ``samtools depth -aa``.
    """

    if minimum_depth < 1:
        raise ValueError("minimum_depth must be at least 1")

    depths = _depth_vector(position_depths, sequence_length)

    mean_depth = fmean(depths)
    median_depth = float(median(depths))
    depth_sd = pstdev(depths)

    covered_bases = sum(
        depth >= minimum_depth
        for depth in depths
    )
    covered_fraction = covered_bases / sequence_length

    if mean_depth > 0:
        coefficient_of_variation = depth_sd / mean_depth
        uniformity = 1.0 / (1.0 + coefficient_of_variation)
    else:
        uniformity = 0.0

    terminal_size = _terminal_window_size(
        sequence_length=sequence_length,
        terminal_fraction=terminal_fraction,
        minimum_terminal_bases=minimum_terminal_bases,
    )

    left_depths = depths[:terminal_size]
    right_depths = depths[-terminal_size:]

    internal_start = terminal_size
    internal_end = sequence_length - terminal_size
    internal_depths = depths[internal_start:internal_end]

    if internal_depths:
        internal_median = float(median(internal_depths))
    else:
        internal_median = median_depth

    left_terminal_support = _terminal_support(
        left_depths,
        internal_median,
    )
    right_terminal_support = _terminal_support(
        right_depths,
        internal_median,
    )

    read_support = (
        covered_fraction
        * uniformity
        * min(
            left_terminal_support,
            right_terminal_support,
        )
    )

    return ReadSupportMetrics(
        sequence_id=sequence_id,
        sequence_length=sequence_length,
        mean_depth=mean_depth,
        median_depth=median_depth,
        depth_sd=depth_sd,
        covered_fraction=covered_fraction,
        uniformity=uniformity,
        left_terminal_support=left_terminal_support,
        right_terminal_support=right_terminal_support,
        read_support=read_support,
    )
