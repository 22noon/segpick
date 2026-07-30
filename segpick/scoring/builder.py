from __future__ import annotations

import math
from collections.abc import Iterable

from segpick.models import CandidateContig
from segpick.scoring.evidence import Evidence


def clamp01(value: float) -> float:
    """Restrict a numeric value to the inclusive range 0–1."""

    return max(0.0, min(1.0, value))


def protein_confidence_evidence(
    candidate: CandidateContig,
    candidates: Iterable[CandidateContig],
) -> float:
    """Normalise confidence relative to the best candidate for the gene.

    The best observed confidence receives 1.0. A confidence of zero receives
    0.0. If all candidates have zero or negative confidence, all receive 0.0.
    """

    maximum = max(
        (max(0.0, float(item.metadata.confidence)) for item in candidates),
        default=0.0,
    )

    if maximum == 0.0:
        return 0.0

    return clamp01(max(0.0, float(candidate.metadata.confidence)) / maximum)


def length_plausibility_evidence(
    candidate: CandidateContig,
) -> float | None:
    """Convert the candidate length z-score into a 0–1 plausibility value.

    Uses the standard normal density-shaped penalty:

        exp(-z² / 2)

    Therefore:

    - z = 0 gives 1.0
    - |z| = 1 gives approximately 0.607
    - |z| = 2 gives approximately 0.135
    - |z| = 3 gives approximately 0.011

    A missing z-score is treated as unavailable evidence and currently receives
    zero. Missing evidence is to be handled with adjusting other weights
    (rather than being interpreted as poor evidence.)
    """
    z = candidate.metadata.z

    if z is None:
        return None

    return clamp01(math.exp(-0.5 * float(z) ** 2))


def structural_integrity_evidence(candidate: CandidateContig) -> float | None:
    """Return reference-relative structural integrity from MegaBLAST HSPs."""

    metrics = candidate.analysis.structural_integrity
    if metrics is not None:
        return clamp01(float(metrics.score))
    legacy = candidate.analysis.containment
    if legacy.query_length or legacy.anchor_length:
        return clamp01(
            float(legacy.query_coverage)
            * float(legacy.anchor_coverage)
            * (1.0 - float(legacy.fragmentation))
        )
    return None


def build_evidence(
    candidate: CandidateContig,
    candidates: Iterable[CandidateContig],
) -> Evidence:
    """Build normalised evidence for one candidate.

    Args:
        candidate: Candidate for which evidence is being calculated.
        candidates: All candidates belonging to the same gene. This is needed
            to normalise protein confidence within the gene.

    Returns:
        An immutable Evidence object containing values between 0 and 1.
    """

    candidate_list = list(candidates)
    return Evidence(
        protein_confidence=protein_confidence_evidence(
            candidate,
            candidate_list,
        ),
        length_plausibility=length_plausibility_evidence(candidate),
        structural_integrity=structural_integrity_evidence(candidate),
        containment=None,
        identity=None,
        fragmentation=None,
        coverage_sufficiency=coverage_sufficiency_evidence(candidate),
        coverage_integrity=coverage_integrity_evidence(candidate),
        orf_quality=orf_quality_evidence(candidate),
        blastx_consistency=blastx_consistency_evidence(candidate),
    )

def build_gene_evidence(
    candidates: Iterable[CandidateContig],
) -> dict[str, Evidence]:
    """Build evidence for every candidate in one gene."""

    candidate_list = list(candidates)

    return {candidate.id: build_evidence(candidate, candidate_list) for candidate in candidate_list}

def coverage_sufficiency_evidence(
    candidate: CandidateContig,
) -> float | None:
    """Return ORF breadth above the configured minimum depth."""

    metrics = candidate.analysis.read_support
    if metrics is None:
        return None
    return clamp01(float(metrics.coverage_sufficiency))


def coverage_integrity_evidence(
    candidate: CandidateContig,
) -> float | None:
    """Return the derived ORF coverage-shape summary."""

    metrics = candidate.analysis.read_support
    if metrics is None:
        return None
    return clamp01(float(metrics.coverage_integrity))


def read_support_evidence(candidate: CandidateContig) -> float | None:
    """Deprecated compatibility wrapper for the former combined channel."""

    metrics = candidate.analysis.read_support
    if metrics is None:
        return None
    return clamp01(float(metrics.read_support))


def orf_quality_evidence(
    candidate: CandidateContig,
) -> float | None:
    """Return the attached explainable ORF-quality score when available."""

    quality = candidate.analysis.orf_quality

    if quality is None:
        return None

    return clamp01(float(quality.score))


def blastx_consistency_evidence(
    candidate: CandidateContig,
) -> float | None:
    """Summarise ORF–BLASTX agreement as a high-value evidence channel."""

    consistency = candidate.analysis.blastx_consistency
    if consistency is None:
        return None

    components: list[tuple[float, float]] = [
        (1.0 if consistency.strand_agrees else 0.0, 0.20),
        (1.0 if consistency.frame_agrees else 0.0, 0.20),
        (clamp01(consistency.blastx_interval_coverage), 0.15),
        (clamp01(consistency.orf_interval_coverage), 0.05),
    ]

    optional = (
        (consistency.amino_acid_identity, 0.15),
        (consistency.subject_coverage, 0.20),
        (consistency.length_agreement, 0.05),
    )
    components.extend(
        (clamp01(float(value)), weight)
        for value, weight in optional
        if value is not None
    )

    available_weight = sum(weight for _, weight in components)
    return sum(value * weight for value, weight in components) / available_weight
