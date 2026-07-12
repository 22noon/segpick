from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from segpick.models import Sample
from segpick.scoring import GeneRecommendation


def write_recommendations_tsv(
    sample: Sample,
    recommendations: Mapping[str, GeneRecommendation],
    path: str | Path,
) -> None:
    """Write ranked candidate recommendations for all genes."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    columns = [
        "gene",
        "segment",
        "rank",
        "candidate",
        "recommended",
        "score",
        "raw_confidence",
        "length",
        "protein_confidence",
        "length_plausibility",
        "containment",
        "identity",
        "fragmentation",
        "protein_contribution",
        "length_contribution",
        "containment_contribution",
        "identity_contribution",
        "fragmentation_contribution",
    ]

    with path.open("w") as handle:
        handle.write("\t".join(columns) + "\n")

        for gene_name in sorted(recommendations):
            recommendation = recommendations[gene_name]
            gene = sample.genes[gene_name]

            for rank, candidate in enumerate(
                recommendation.candidates,
                start=1,
            ):
                evidence = candidate.evidence.to_dict()
                contributions = candidate.scored.contributions

                row = [
                    gene.name,
                    gene.segment,
                    str(rank),
                    candidate.candidate_id,
                    str(candidate.candidate_id == recommendation.recommended.candidate_id),
                    f"{candidate.score:.6f}",
                    f"{candidate.protein_confidence_raw:.6f}",
                    str(candidate.length),
                    _format_optional(evidence.get("protein_confidence")),
                    _format_optional(evidence.get("length_plausibility")),
                    _format_optional(evidence.get("containment")),
                    _format_optional(evidence.get("identity")),
                    _format_optional(evidence.get("fragmentation")),
                    _format_optional(contributions.get("protein_confidence")),
                    _format_optional(contributions.get("length_plausibility")),
                    _format_optional(contributions.get("containment")),
                    _format_optional(contributions.get("identity")),
                    _format_optional(contributions.get("fragmentation")),
                ]

                handle.write("\t".join(row) + "\n")


def _format_optional(value: float | None) -> str:
    """Format an optional floating-point value for TSV output."""

    if value is None:
        return ""

    return f"{value:.6f}"
