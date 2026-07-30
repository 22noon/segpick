from __future__ import annotations

from segpick.models import BiologicalFinding, CandidateContig


def generate_protein_findings(
    candidate: CandidateContig,
) -> tuple[BiologicalFinding, ...]:
    """Create candidate-level findings from protein interpretation."""
    protein = candidate.analysis.protein_interpretation
    if protein is None:
        return ()

    observation_types = tuple(
        observation.observation_type
        for observation in candidate.analysis.observations
        if observation.source == "protein_alignment"
    )

    if protein.possible_frameshift_pattern:
        finding = BiologicalFinding(
            category="protein",
            title="Possible frameshift pattern",
            severity="review",
            confidence="moderate",
            scope="candidate",
            summary=protein.summary,
            sources=("protein_alignment",),
            observation_types=observation_types,
            candidate_ids=(candidate.id,),
        )
    elif protein.structural_status == "intact":
        finding = BiologicalFinding(
            category="protein",
            title="Complete protein recovered",
            severity="informational",
            confidence="high",
            scope="candidate",
            summary=protein.summary,
            sources=("protein_alignment",),
            candidate_ids=(candidate.id,),
        )
    elif protein.structural_status in {"truncated", "truncated_with_indels"}:
        finding = BiologicalFinding(
            category="protein",
            title="Protein truncation detected",
            severity="warning",
            confidence="high",
            scope="candidate",
            summary=protein.summary,
            sources=("protein_alignment",),
            observation_types=observation_types,
            candidate_ids=(candidate.id,),
        )
    else:
        finding = BiologicalFinding(
            category="protein",
            title="Internal protein differences",
            severity="review",
            confidence="moderate",
            scope="candidate",
            summary=protein.summary,
            sources=("protein_alignment",),
            observation_types=observation_types,
            candidate_ids=(candidate.id,),
        )

    return (finding,)
