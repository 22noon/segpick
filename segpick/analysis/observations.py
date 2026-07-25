from __future__ import annotations

from statistics import median

from segpick.models import (
    CandidateContig,
    ObservationInterval,
    ORFAlignmentMetrics,
    Sample,
)


def _coordinate_system(metrics: ORFAlignmentMetrics) -> str:
    return f"reference_protein:{metrics.reference_id}"


def _terminal_observations(
    metrics: ORFAlignmentMetrics,
) -> list[ObservationInterval]:
    observations: list[ObservationInterval] = []
    coordinate_system = _coordinate_system(metrics)

    if metrics.n_terminal_missing:
        observations.append(
            ObservationInterval(
                coordinate_system=coordinate_system,
                start=1,
                end=metrics.n_terminal_missing,
                observation_type="n_terminal_truncation",
                source="protein_alignment",
                description=(
                    "Predicted protein lacks "
                    f"{metrics.n_terminal_missing} N-terminal reference residues."
                ),
                attributes={"missing_residues": metrics.n_terminal_missing},
            )
        )

    if metrics.c_terminal_missing:
        start = metrics.reference_protein_length - metrics.c_terminal_missing + 1
        observations.append(
            ObservationInterval(
                coordinate_system=coordinate_system,
                start=start,
                end=metrics.reference_protein_length,
                observation_type="c_terminal_truncation",
                source="protein_alignment",
                description=(
                    "Predicted protein lacks "
                    f"{metrics.c_terminal_missing} C-terminal reference residues."
                ),
                attributes={"missing_residues": metrics.c_terminal_missing},
            )
        )

    return observations


def _internal_indel_observations(
    metrics: ORFAlignmentMetrics,
) -> list[ObservationInterval]:
    observations: list[ObservationInterval] = []
    coordinate_system = _coordinate_system(metrics)
    aligned_candidate = metrics.aligned_candidate
    aligned_reference = metrics.aligned_reference

    if not aligned_candidate or not aligned_reference:
        return observations

    reference_position = 0
    index = 0
    alignment_length = min(len(aligned_candidate), len(aligned_reference))

    while index < alignment_length:
        candidate_residue = aligned_candidate[index]
        reference_residue = aligned_reference[index]

        if reference_residue != "-":
            reference_position += 1

        if candidate_residue == "-" and reference_residue != "-":
            start = reference_position
            deleted = 1
            index += 1
            while index < alignment_length:
                candidate_residue = aligned_candidate[index]
                reference_residue = aligned_reference[index]
                if candidate_residue != "-" or reference_residue == "-":
                    break
                reference_position += 1
                deleted += 1
                index += 1
            end = start + deleted - 1
            observations.append(
                ObservationInterval(
                    coordinate_system=coordinate_system,
                    start=start,
                    end=end,
                    observation_type="internal_deletion",
                    source="protein_alignment",
                    description=(
                        f"Predicted protein lacks {deleted} reference residues "
                        f"at positions {start}-{end}."
                    ),
                    attributes={"deleted_residues": deleted},
                )
            )
            continue

        if reference_residue == "-" and candidate_residue != "-":
            inserted = 1
            index += 1
            while index < alignment_length:
                candidate_residue = aligned_candidate[index]
                reference_residue = aligned_reference[index]
                if reference_residue != "-" or candidate_residue == "-":
                    break
                inserted += 1
                index += 1

            anchor = max(reference_position, 1)
            observations.append(
                ObservationInterval(
                    coordinate_system=coordinate_system,
                    start=anchor,
                    end=anchor,
                    observation_type="internal_insertion",
                    source="protein_alignment",
                    description=(
                        f"Predicted protein contains {inserted} inserted residues "
                        f"after reference position {anchor}."
                    ),
                    attributes={"inserted_residues": inserted},
                )
            )
            continue

        index += 1

    return observations


def protein_alignment_observations(
    metrics: ORFAlignmentMetrics,
) -> tuple[ObservationInterval, ...]:
    """Convert protein-alignment differences into reference-protein intervals."""

    observations = _terminal_observations(metrics)
    observations.extend(_internal_indel_observations(metrics))
    return tuple(observations)




def _candidate_to_reference_map(
    metrics: ORFAlignmentMetrics,
) -> dict[int, int]:
    """Map 1-based candidate amino-acid positions to reference positions."""

    mapping: dict[int, int] = {}
    candidate_position = 0
    reference_position = 0

    for candidate_residue, reference_residue in zip(
        metrics.aligned_candidate,
        metrics.aligned_reference,
        strict=False,
    ):
        if candidate_residue != "-":
            candidate_position += 1
        if reference_residue != "-":
            reference_position += 1
        if candidate_residue != "-" and reference_residue != "-":
            mapping[candidate_position] = reference_position

    return mapping


def _candidate_aa_position(candidate: CandidateContig, nt_position: int) -> int:
    """Return the 1-based amino-acid position containing a nucleotide."""

    orf_metrics = candidate.analysis.orf
    if orf_metrics is None or orf_metrics.best_orf is None:
        raise ValueError("Candidate has no selected ORF")

    orf = orf_metrics.best_orf
    zero_based_position = nt_position - 1

    if orf.strand == "+":
        return ((zero_based_position - orf.start) // 3) + 1

    return ((orf.end - 1 - zero_based_position) // 3) + 1


def _low_coverage_runs(
    candidate: CandidateContig,
    *,
    minimum_depth: int,
    relative_fraction: float,
    minimum_run_bases: int,
) -> list[tuple[int, int, list[int]]]:
    orf_metrics = candidate.analysis.orf
    if orf_metrics is None or orf_metrics.best_orf is None:
        return []

    depths = candidate.analysis.depth_profile
    if not depths:
        return []

    orf = orf_metrics.best_orf
    positions = list(range(orf.start + 1, orf.end + 1))
    orf_depths = [depths.get(position, 0) for position in positions]
    if not orf_depths:
        return []

    median_depth = float(median(orf_depths))
    threshold = min(float(minimum_depth), median_depth * relative_fraction)
    if threshold <= 0:
        return []

    runs: list[tuple[int, int, list[int]]] = []
    run_start: int | None = None
    run_depths: list[int] = []

    for position, depth in zip(positions, orf_depths, strict=True):
        if depth < threshold:
            if run_start is None:
                run_start = position
            run_depths.append(depth)
            continue

        if run_start is not None:
            run_end = position - 1
            if run_end - run_start + 1 >= minimum_run_bases:
                runs.append((run_start, run_end, run_depths))
            run_start = None
            run_depths = []

    if run_start is not None:
        run_end = positions[-1]
        if run_end - run_start + 1 >= minimum_run_bases:
            runs.append((run_start, run_end, run_depths))

    return runs


def coverage_observations(
    candidate: CandidateContig,
    *,
    minimum_depth: int = 3,
    relative_fraction: float = 0.25,
    minimum_run_bases: int = 9,
) -> tuple[ObservationInterval, ...]:
    """Project sustained ORF coverage drops onto reference-protein coordinates."""

    if minimum_depth < 1:
        raise ValueError("minimum_depth must be at least 1")
    if not 0 < relative_fraction <= 1:
        raise ValueError("relative_fraction must be between 0 and 1")
    if minimum_run_bases < 1:
        raise ValueError("minimum_run_bases must be at least 1")

    alignment = candidate.analysis.orf_alignment
    if alignment is None or not alignment.aligned_candidate:
        return ()

    reference_map = _candidate_to_reference_map(alignment)
    if not reference_map:
        return ()

    orf = candidate.analysis.orf.best_orf if candidate.analysis.orf else None
    if orf is None:
        return ()

    positions = list(range(orf.start + 1, orf.end + 1))
    orf_depths = [candidate.analysis.depth_profile.get(position, 0) for position in positions]
    orf_median = float(median(orf_depths)) if orf_depths else 0.0
    threshold = min(float(minimum_depth), orf_median * relative_fraction)
    coordinate_system = _coordinate_system(alignment)
    observations: list[ObservationInterval] = []

    for nt_start, nt_end, run_depths in _low_coverage_runs(
        candidate,
        minimum_depth=minimum_depth,
        relative_fraction=relative_fraction,
        minimum_run_bases=minimum_run_bases,
    ):
        candidate_positions = {
            _candidate_aa_position(candidate, position)
            for position in range(nt_start, nt_end + 1)
        }
        reference_positions = [
            reference_map[position]
            for position in candidate_positions
            if position in reference_map
        ]
        if not reference_positions:
            continue

        start = min(reference_positions)
        end = max(reference_positions)
        observations.append(
            ObservationInterval(
                coordinate_system=coordinate_system,
                start=start,
                end=end,
                observation_type="coverage_drop",
                source="read_coverage",
                description=(
                    "Sustained low read coverage overlaps reference-protein "
                    f"positions {start}-{end}."
                ),
                attributes={
                    "minimum_depth": min(run_depths),
                    "orf_median_depth": orf_median,
                    "coverage_threshold": threshold,
                    "mean_depth_in_region": sum(run_depths) / len(run_depths),
                    "nucleotide_length": nt_end - nt_start + 1,
                    "contig_start": nt_start,
                    "contig_end": nt_end,
                },
            )
        )

    return tuple(observations)


def attach_observation_intervals(
    sample: Sample,
    *,
    minimum_depth: int = 3,
) -> None:
    """Attach spatial observations derived from candidate protein alignments."""

    for gene in sample.genes.values():
        for candidate in gene.candidates:
            alignment = candidate.analysis.orf_alignment
            protein_observations = (
                protein_alignment_observations(alignment)
                if alignment is not None
                else ()
            )
            candidate.analysis.observations = (
                protein_observations
                + coverage_observations(
                    candidate,
                    minimum_depth=minimum_depth,
                )
            )
