from __future__ import annotations

from segpick.analysis.convergence import detect_evidence_convergence
from segpick.findings import (
    generate_continuity_findings,
    generate_convergence_findings,
    generate_homology_findings,
    generate_protein_findings,
)
from segpick.models import BiologicalFinding, CandidateContig, Gene, Sample


def candidate_biological_findings(
    candidate: CandidateContig,
) -> tuple[BiologicalFinding, ...]:
    """Collect candidate-level findings from dedicated generators."""
    candidate.analysis.convergences = detect_evidence_convergence(
        candidate.analysis.observations,
        candidate.id,
    )
    return (
        *generate_protein_findings(candidate),
        *generate_homology_findings(candidate),
        *generate_convergence_findings(candidate),
    )


def gene_biological_findings(gene: Gene) -> tuple[BiologicalFinding, ...]:
    """Collect gene-level findings from dedicated generators."""
    return generate_continuity_findings(gene)


def attach_biological_findings(sample: Sample) -> None:
    """Attach candidate- and gene-level findings after analyses are complete."""
    for gene in sample.genes.values():
        for candidate in gene.candidates:
            candidate.analysis.findings = candidate_biological_findings(candidate)
        gene.findings = gene_biological_findings(gene)
