from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from statistics import fmean, median, pstdev

from segpick.models import ReadSupportMetrics


def parse_depth_lines(lines: Iterable[str]) -> dict[str, dict[int, int]]:
    """Parse three-column samtools depth output."""

    depths: dict[str, dict[int, int]] = {}
    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        fields = line.split()
        if len(fields) < 3:
            raise ValueError(
                f"Invalid depth line {line_number}: expected at least 3 columns, "
                f"found {len(fields)}"
            )
        sequence_id = fields[0]
        try:
            position = int(fields[1])
            depth = int(fields[2])
        except ValueError as error:
            raise ValueError(
                f"Invalid numeric value on depth line {line_number}: {line!r}"
            ) from error
        if position < 1:
            raise ValueError(
                f"Depth position must be one-based and positive; line {line_number} has {position}"
            )
        if depth < 0:
            raise ValueError(f"Depth cannot be negative; line {line_number} has {depth}")
        sequence_depths = depths.setdefault(sequence_id, {})
        if position in sequence_depths:
            raise ValueError(f"Duplicate depth position for {sequence_id!r}: {position}")
        sequence_depths[position] = depth
    return depths


def parse_depth_file(path: str | Path) -> dict[str, dict[int, int]]:
    path = Path(path)
    with path.open() as handle:
        return parse_depth_lines(handle)


def _depth_vector(position_depths: dict[int, int], sequence_length: int) -> list[int]:
    if sequence_length < 1:
        raise ValueError("sequence_length must be greater than zero")
    invalid_positions = [position for position in position_depths if position > sequence_length]
    if invalid_positions:
        raise ValueError(
            "Depth positions exceed sequence length: "
            + ", ".join(str(position) for position in sorted(invalid_positions))
        )
    return [position_depths.get(position, 0) for position in range(1, sequence_length + 1)]


def _terminal_window_size(sequence_length: int, terminal_fraction: float, minimum_terminal_bases: int) -> int:
    if not 0 < terminal_fraction <= 0.5:
        raise ValueError("terminal_fraction must be greater than zero and no more than 0.5")
    if minimum_terminal_bases < 1:
        raise ValueError("minimum_terminal_bases must be at least 1")
    requested = max(minimum_terminal_bases, round(sequence_length * terminal_fraction))
    return min(requested, max(1, sequence_length // 2))


def _terminal_support(terminal_depths: list[int], internal_median: float) -> float:
    if not terminal_depths:
        return 0.0
    terminal_mean = fmean(terminal_depths)
    if internal_median <= 0:
        return 1.0 if terminal_mean > 0 else 0.0
    return min(1.0, terminal_mean / internal_median)


def _longest_run(depths: list[int], predicate) -> int:
    longest = current = 0
    for depth in depths:
        if predicate(depth):
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def _internal_low_depth_runs(depths: list[int], minimum_depth: int, terminal_size: int) -> int:
    if len(depths) <= terminal_size * 2:
        return 0
    internal = depths[terminal_size:-terminal_size]
    count = 0
    in_run = False
    for depth in internal:
        if depth < minimum_depth and not in_run:
            count += 1
            in_run = True
        elif depth >= minimum_depth:
            in_run = False
    return count


def calculate_read_support(
    sequence_id: str,
    position_depths: dict[int, int],
    sequence_length: int,
    *,
    region_start: int = 0,
    region_end: int | None = None,
    region_source: str = "whole_contig",
    minimum_depth: int = 3,
    terminal_fraction: float = 0.05,
    minimum_terminal_bases: int = 50,
) -> ReadSupportMetrics:
    """Calculate ORF-centred read sufficiency and integrity measurements.

    ``region_start`` and ``region_end`` are zero-based, end-exclusive contig
    coordinates. Missing depth positions are treated as zero.
    """

    if minimum_depth < 1:
        raise ValueError("minimum_depth must be at least 1")
    if region_end is None:
        region_end = sequence_length
    if not 0 <= region_start < region_end <= sequence_length:
        raise ValueError("Read-support region must lie within the candidate sequence")

    whole_depths = _depth_vector(position_depths, sequence_length)
    depths = whole_depths[region_start:region_end]
    region_length = len(depths)

    mean_depth = fmean(depths)
    median_depth = float(median(depths))
    depth_sd = pstdev(depths)
    any_covered_fraction = sum(depth > 0 for depth in depths) / region_length
    covered_fraction = sum(depth >= minimum_depth for depth in depths) / region_length

    if mean_depth > 0:
        coefficient_of_variation = depth_sd / mean_depth
        uniformity = 1.0 / (1.0 + coefficient_of_variation)
    else:
        uniformity = 0.0

    terminal_size = _terminal_window_size(
        sequence_length=region_length,
        terminal_fraction=terminal_fraction,
        minimum_terminal_bases=minimum_terminal_bases,
    )
    left_depths = depths[:terminal_size]
    right_depths = depths[-terminal_size:]
    internal_depths = depths[terminal_size:-terminal_size]
    internal_median = float(median(internal_depths)) if internal_depths else median_depth
    left_terminal_support = _terminal_support(left_depths, internal_median)
    right_terminal_support = _terminal_support(right_depths, internal_median)

    longest_uncovered_interval = _longest_run(depths, lambda depth: depth == 0)
    longest_low_depth_interval = _longest_run(depths, lambda depth: depth < minimum_depth)
    internal_interruptions = _internal_low_depth_runs(depths, minimum_depth, terminal_size)

    continuity = 1.0 - (longest_low_depth_interval / region_length)
    terminal_integrity = min(left_terminal_support, right_terminal_support)
    coverage_sufficiency = covered_fraction
    coverage_integrity = uniformity * continuity * terminal_integrity

    whole_mean = fmean(whole_depths)
    whole_median = float(median(whole_depths))
    whole_covered = sum(depth >= minimum_depth for depth in whole_depths) / sequence_length

    return ReadSupportMetrics(
        sequence_id=sequence_id,
        sequence_length=sequence_length,
        region_source=region_source,
        region_start=region_start,
        region_end=region_end,
        region_length=region_length,
        mean_depth=mean_depth,
        median_depth=median_depth,
        depth_sd=depth_sd,
        any_covered_fraction=any_covered_fraction,
        covered_fraction=covered_fraction,
        uniformity=uniformity,
        left_terminal_support=left_terminal_support,
        right_terminal_support=right_terminal_support,
        longest_uncovered_interval=longest_uncovered_interval,
        longest_low_depth_interval=longest_low_depth_interval,
        internal_low_depth_interruption_count=internal_interruptions,
        coverage_sufficiency=coverage_sufficiency,
        coverage_integrity=coverage_integrity,
        whole_contig_mean_depth=whole_mean,
        whole_contig_median_depth=whole_median,
        whole_contig_covered_fraction=whole_covered,
    )
