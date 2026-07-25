from __future__ import annotations

from collections import defaultdict

from segpick.models import EvidenceConvergence, ObservationInterval


def _strength(source_count: int) -> str:
    if source_count >= 4:
        return "very_strong"
    if source_count == 3:
        return "strong"
    return "moderate"


def detect_evidence_convergence(
    observations: tuple[ObservationInterval, ...],
    candidate_id: str,
    proximity: int = 3,
) -> tuple[EvidenceConvergence, ...]:
    """Find nearby observations supported by at least two independent sources.

    Intervals are clustered separately within each coordinate system. Two
    observations are considered connected when they overlap or are separated
    by no more than ``proximity`` amino-acid positions.
    """

    if proximity < 0:
        raise ValueError("proximity must be non-negative")

    grouped: dict[str, list[ObservationInterval]] = defaultdict(list)
    for observation in observations:
        grouped[observation.coordinate_system].append(observation)

    convergences: list[EvidenceConvergence] = []
    for coordinate_system, items in grouped.items():
        ordered = sorted(items, key=lambda item: (item.start, item.end))
        clusters: list[list[ObservationInterval]] = []

        for observation in ordered:
            if not clusters:
                clusters.append([observation])
                continue

            current = clusters[-1]
            current_end = max(item.end for item in current)
            if observation.start <= current_end + proximity + 1:
                current.append(observation)
            else:
                clusters.append([observation])

        for cluster in clusters:
            sources = tuple(sorted({item.source for item in cluster}))
            if len(sources) < 2:
                continue

            start = min(item.start for item in cluster)
            end = max(item.end for item in cluster)
            observation_types = tuple(
                sorted({item.observation_type for item in cluster})
            )
            strength = _strength(len(sources))
            source_text = ", ".join(sources)
            summary = (
                f"{len(sources)} independent evidence sources converge on "
                f"reference-protein positions {start}-{end}: {source_text}."
            )
            convergences.append(
                EvidenceConvergence(
                    coordinate_system=coordinate_system,
                    start=start,
                    end=end,
                    strength=strength,
                    sources=sources,
                    observation_types=observation_types,
                    observations=tuple(cluster),
                    summary=summary,
                    candidate_id=candidate_id,
                )
            )

    return tuple(convergences)
