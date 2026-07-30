from __future__ import annotations

from collections.abc import Mapping

from segpick.models import ORFAlignmentMetrics, ORFMetrics, ORFQuality, Sample

_COMPONENT_WEIGHTS: dict[str, float] = {
    "complete_orf": 0.20,
    "start_codon": 0.10,
    "stop_codon": 0.10,
    "protein_identity": 0.20,
    "reference_coverage": 0.15,
    "length_agreement": 0.10,
    "terminal_completeness": 0.10,
    "gap_integrity": 0.05,
}


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _weighted_score(
    components: Mapping[str, float | None],
) -> float:
    """Combine available components, redistributing missing component weight."""

    available = {
        name: value
        for name, value in components.items()
        if value is not None
    }
    total_weight = sum(_COMPONENT_WEIGHTS[name] for name in available)
    if total_weight == 0:
        return 0.0
    return sum(
        _COMPONENT_WEIGHTS[name] * value
        for name, value in available.items()
    ) / total_weight


def calculate_orf_quality(
    orf: ORFMetrics | None,
    alignment: ORFAlignmentMetrics | None,
) -> ORFQuality | None:
    """Convert raw ORF measurements into transparent normalized components."""

    if orf is None or orf.best_orf is None:
        return None

    best = orf.best_orf
    protein_identity = None
    reference_coverage = None
    length_agreement = None
    terminal_completeness = None
    gap_integrity = None

    if alignment is not None:
        protein_identity = _clamp(alignment.amino_acid_identity)
        reference_coverage = _clamp(alignment.reference_coverage)
        length_agreement = _clamp(
            min(alignment.length_ratio, 1.0 / alignment.length_ratio)
        )
        terminal_missing = (
            alignment.n_terminal_missing + alignment.c_terminal_missing
        )
        terminal_completeness = _clamp(
            1.0 - terminal_missing / alignment.reference_protein_length
        )
        gap_integrity = _clamp(
            1.0
            - alignment.internal_gap_residues
            / max(
                alignment.candidate_protein_length,
                alignment.reference_protein_length,
            )
        )

    components: dict[str, float | None] = {
        "complete_orf": float(best.complete),
        "start_codon": float(best.has_start_codon),
        "stop_codon": float(best.has_stop_codon),
        "protein_identity": protein_identity,
        "reference_coverage": reference_coverage,
        "length_agreement": length_agreement,
        "terminal_completeness": terminal_completeness,
        "gap_integrity": gap_integrity,
    }
    return ORFQuality(
        score=_weighted_score(components),
        **components,
    )


def attach_orf_quality(sample: Sample) -> None:
    """Attach ORF quality components to every candidate with an identified ORF."""

    for gene in sample.genes.values():
        for candidate in gene.candidates:
            candidate.analysis.orf_quality = calculate_orf_quality(
                candidate.analysis.orf,
                candidate.analysis.orf_alignment,
            )
