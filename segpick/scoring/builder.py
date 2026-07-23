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


def containment_evidence(candidate: CandidateContig) -> float:
    """Combine query and anchor coverage into one containment value."""

    metrics = candidate.analysis.containment

    return clamp01(float(metrics.query_coverage) * float(metrics.anchor_coverage))


def identity_evidence(candidate: CandidateContig) -> float:
    """Return alignment identity, already expected to be in the range 0–1."""

    return clamp01(float(candidate.analysis.containment.identity))


def fragmentation_evidence(candidate: CandidateContig) -> float:
    """Convert fragmentation penalty into positive evidence.

    A single continuous alignment has fragmentation 0 and receives evidence
    1.0. Completely fragmented or unaligned candidates approach 0.0.
    """

    fragmentation = float(candidate.analysis.containment.fragmentation)
    return clamp01(1.0 - fragmentation)


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
        containment=containment_evidence(candidate),
        identity=identity_evidence(candidate),
        fragmentation=fragmentation_evidence(candidate),
        read_support=read_support_evidence(candidate),
        orf_quality=orf_quality_evidence(candidate),
    )

def build_gene_evidence(
    candidates: Iterable[CandidateContig],
) -> dict[str, Evidence]:
    """Build evidence for every candidate in one gene."""

    candidate_list = list(candidates)

    return {candidate.id: build_evidence(candidate, candidate_list) for candidate in candidate_list}

def read_support_evidence(
    candidate: CandidateContig,
) -> float | None:
    """Return attached read-support evidence when available."""

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
