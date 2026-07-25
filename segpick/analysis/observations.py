from __future__ import annotations

from segpick.models import ObservationInterval, ORFAlignmentMetrics, Sample


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


def attach_observation_intervals(sample: Sample) -> None:
    """Attach spatial observations derived from candidate protein alignments."""

    for gene in sample.genes.values():
        for candidate in gene.candidates:
            alignment = candidate.analysis.orf_alignment
            candidate.analysis.observations = (
                protein_alignment_observations(alignment)
                if alignment is not None
                else ()
            )
