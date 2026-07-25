from __future__ import annotations

from dataclasses import dataclass

from segpick.models import CandidateContig, Gene
from segpick.scoring import GeneRecommendation


@dataclass(frozen=True, slots=True)
class ReadSupportView:
    available: bool
    mean_depth: float | None
    median_depth: float | None
    covered_fraction: float | None
    uniformity: float | None
    left_terminal_support: float | None
    right_terminal_support: float | None
    overall_support: float | None


@dataclass(frozen=True, slots=True)
class ProteinRelatednessView:
    available: bool
    subject_id: str | None
    subject_title: str | None
    percent_identity: float | None
    query_coverage: float | None
    subject_coverage: float | None
    top_hit_gene_agreement: float | None
    classification: str | None
    summary: str | None


@dataclass(frozen=True, slots=True)
class ORFView:
    available: bool
    score: float | None
    strand: str | None
    frame: int | None
    start: int | None
    end: int | None
    protein_length: int | None
    complete: bool | None
    complete_orf_count: int
    other_complete_orf_count: int
    major_competing_orf_count: int
    largest_competing_orf_length: int
    reference_id: str | None
    protein_identity: float | None
    reference_coverage: float | None
    n_terminal_missing: int | None
    c_terminal_missing: int | None
    internal_gap_residues: int | None
    internal_gap_events: int | None
    largest_internal_gap: int | None
    internal_insertion_residues: int | None
    internal_insertion_events: int | None
    largest_internal_insertion: int | None
    internal_deletion_residues: int | None
    internal_deletion_events: int | None
    largest_internal_deletion: int | None
    difference_summary: tuple[str, ...]
    interpretation_status: str | None
    interpretation_summary: str | None
    possible_frameshift_pattern: bool
    alignment_text: str | None
    predicted_protein: str | None
    reference_protein: str | None
    predicted_header: str | None
    reference_header: str | None
    warnings: tuple[str, ...]
    relatedness: ProteinRelatednessView


@dataclass(frozen=True, slots=True)
class EvidenceView:
    name: str
    value: float | None
    contribution: float | None
    effective_weight: float | None


@dataclass(frozen=True, slots=True)
class RecommendationView:
    candidate_id: str
    score: float
    evidence: tuple[EvidenceView, ...]
    runner_up_id: str | None
    runner_up_score: float | None
    score_gap: float | None
    runner_up_strength: str | None
    confidence: str
    supporting_channels: tuple[str, ...]
    disagreeing_channels: tuple[str, ...]
    strong_conflicts: tuple[str, ...]
    supporting_evidence: tuple[str, ...]
    opposing_evidence: tuple[str, ...]
    evidence_conflicts: tuple[str, ...]
    manual_review: bool
    summary: str | None
    runner_up_reasons: tuple[str, ...]
    runner_up_advantages: tuple[str, ...]
    runner_up_strongest_difference: str | None


@dataclass(frozen=True, slots=True)
class CandidateView:
    candidate_id: str
    length: int
    confidence: float
    z: float | None
    cluster: str
    query_coverage: float
    anchor_coverage: float
    identity: float
    fragmentation: float
    structural_score: float
    status: str
    recommended: bool
    read_support: ReadSupportView
    orf: ORFView
    coverage_plot: str | None


@dataclass(frozen=True, slots=True)
class GenePageView:
    gene: str
    segment: str
    anchor: str | None
    recommendation: RecommendationView | None
    candidates: tuple[CandidateView, ...]


def build_recommendation_view(
    recommendation: GeneRecommendation | None,
) -> RecommendationView | None:
    if recommendation is None:
        return None

    selected = recommendation.recommended
    evidence = tuple(
        EvidenceView(
            name=name,
            value=value,
            contribution=selected.scored.contributions.get(name),
            effective_weight=selected.scored.effective_weights.get(name),
        )
        for name, value in selected.evidence.to_dict().items()
    )

    runner_up = (
        recommendation.candidates[1]
        if len(recommendation.candidates) > 1
        else None
    )

    if runner_up is None:
        score_gap = None
        runner_up_strength = None
    else:
        score_gap = selected.score - runner_up.score
        if score_gap < 0.05:
            runner_up_strength = "close"
        elif score_gap <= 0.15:
            runner_up_strength = "secondary"
        else:
            runner_up_strength = "weak"

    return RecommendationView(
        candidate_id=selected.candidate_id,
        score=selected.score,
        evidence=evidence,
        runner_up_id=runner_up.candidate_id if runner_up else None,
        runner_up_score=runner_up.score if runner_up else None,
        score_gap=score_gap,
        runner_up_strength=runner_up_strength,
        confidence=(
            recommendation.agreement.confidence
            if recommendation.agreement is not None
            else "unknown"
        ),
        supporting_channels=(
            recommendation.agreement.supporting_channels
            if recommendation.agreement is not None
            else ()
        ),
        disagreeing_channels=(
            recommendation.agreement.disagreeing_channels
            if recommendation.agreement is not None
            else ()
        ),
        strong_conflicts=(
            recommendation.agreement.strong_conflicts
            if recommendation.agreement is not None
            else ()
        ),
        supporting_evidence=(
            recommendation.report.supporting_evidence
            if recommendation.report is not None
            else ()
        ),
        opposing_evidence=(
            recommendation.report.opposing_evidence
            if recommendation.report is not None
            else ()
        ),
        evidence_conflicts=(
            recommendation.report.evidence_conflicts
            if recommendation.report is not None
            else ()
        ),
        manual_review=(
            recommendation.report.manual_review
            if recommendation.report is not None
            else False
        ),
        summary=(
            recommendation.report.summary
            if recommendation.report is not None
            else None
        ),
        runner_up_reasons=(
            recommendation.comparisons[0].reasons_not_selected
            if recommendation.comparisons
            else ()
        ),
        runner_up_advantages=(
            recommendation.comparisons[0].alternative_advantages
            if recommendation.comparisons
            else ()
        ),
        runner_up_strongest_difference=(
            recommendation.comparisons[0].strongest_difference
            if recommendation.comparisons
            else None
        ),
    )


def build_gene_page_view(
    gene: Gene,
    recommendation: GeneRecommendation | None,
    *,
    coverage_plot_paths: dict[str, str] | None = None,
) -> GenePageView:
    coverage_plot_paths = coverage_plot_paths or {}

    recommended_id = (
        recommendation.recommended.candidate_id
        if recommendation is not None
        else None
    )

    candidates = tuple(
        CandidateView(
            candidate_id=candidate.id,
            length=candidate.length,
            confidence=float(candidate.metadata.confidence),
            z=candidate.metadata.z,
            cluster=str(candidate.metadata.cluster),
            query_coverage=candidate.analysis.containment.query_coverage,
            anchor_coverage=candidate.analysis.containment.anchor_coverage,
            identity=candidate.analysis.containment.identity,
            fragmentation=candidate.analysis.containment.fragmentation,
            structural_score=candidate.analysis.containment.structural_score,
            status=candidate.analysis.containment.status,
            recommended=candidate.id == recommended_id,
            read_support=build_read_support_view(candidate),
            orf=build_orf_view(candidate),
            coverage_plot=coverage_plot_paths.get(candidate.id),
        )
        for candidate in gene.candidates
    )

    return GenePageView(
        gene=gene.name,
        segment=gene.segment,
        anchor=gene.anchor_id,
        recommendation=build_recommendation_view(recommendation),
        candidates=candidates,
    )


def build_read_support_view(candidate: CandidateContig) -> ReadSupportView:
    """Build optional read-support data for dashboard presentation."""

    metrics = candidate.analysis.read_support
    if metrics is None:
        return ReadSupportView(
            available=False,
            mean_depth=None,
            median_depth=None,
            covered_fraction=None,
            uniformity=None,
            left_terminal_support=None,
            right_terminal_support=None,
            overall_support=None,
        )

    return ReadSupportView(
        available=True,
        mean_depth=metrics.mean_depth,
        median_depth=metrics.median_depth,
        covered_fraction=metrics.covered_fraction,
        uniformity=metrics.uniformity,
        left_terminal_support=metrics.left_terminal_support,
        right_terminal_support=metrics.right_terminal_support,
        overall_support=metrics.read_support,
    )



def _format_protein_alignment(alignment, width: int = 60) -> str | None:
    if alignment is None or not alignment.aligned_reference:
        return None

    lines: list[str] = []
    reference_position = 0
    candidate_position = 0
    for offset in range(0, len(alignment.aligned_reference), width):
        reference = alignment.aligned_reference[offset : offset + width]
        matches = alignment.match_line[offset : offset + width]
        candidate = alignment.aligned_candidate[offset : offset + width]
        reference_start = reference_position + 1
        candidate_start = candidate_position + 1
        reference_position += sum(residue != "-" for residue in reference)
        candidate_position += sum(residue != "-" for residue in candidate)
        lines.extend(
            [
                f"Reference {reference_start:>5}  {reference}  {reference_position}",
                f"                {matches}",
                f"Candidate {candidate_start:>5}  {candidate}  {candidate_position}",
                "",
            ]
        )
    return "\n".join(lines).rstrip()


def _describe_protein_differences(alignment) -> tuple[str, ...]:
    if alignment is None:
        return ()

    descriptions: list[str] = []
    if alignment.n_terminal_missing:
        descriptions.append(
            f"N-terminal truncation: {alignment.n_terminal_missing} reference residues missing."
        )
    if alignment.c_terminal_missing:
        descriptions.append(
            f"C-terminal truncation: {alignment.c_terminal_missing} reference residues missing."
        )
    if alignment.internal_deletion_events:
        descriptions.append(
            f"Internal deletion: {alignment.internal_deletion_residues} residues "
            f"across {alignment.internal_deletion_events} event(s); largest "
            f"{alignment.largest_internal_deletion} aa."
        )
    if alignment.internal_insertion_events:
        descriptions.append(
            f"Internal insertion: {alignment.internal_insertion_residues} residues "
            f"across {alignment.internal_insertion_events} event(s); largest "
            f"{alignment.largest_internal_insertion} aa."
        )
    if alignment.internal_gap_events > 1:
        descriptions.append(
            "Multiple internal indel events are present; inspect for scattered "
            "differences or possible assembly error."
        )
    if not descriptions:
        descriptions.append("No terminal truncations or internal indels detected.")
    return tuple(descriptions)

def build_protein_relatedness_view(
    candidate: CandidateContig,
) -> ProteinRelatednessView:
    relatedness = candidate.analysis.protein_relatedness
    if relatedness is None:
        return ProteinRelatednessView(
            available=False,
            subject_id=None,
            subject_title=None,
            percent_identity=None,
            query_coverage=None,
            subject_coverage=None,
            top_hit_gene_agreement=None,
            classification=None,
            summary=None,
        )
    return ProteinRelatednessView(
        available=True,
        subject_id=relatedness.subject_id,
        subject_title=relatedness.subject_title,
        percent_identity=relatedness.percent_identity,
        query_coverage=relatedness.query_coverage,
        subject_coverage=relatedness.subject_coverage,
        top_hit_gene_agreement=relatedness.top_hit_gene_agreement,
        classification=relatedness.classification,
        summary=relatedness.summary,
    )


def build_orf_view(candidate: CandidateContig) -> ORFView:
    """Build ORF structural details and conservative review warnings."""

    metrics = candidate.analysis.orf
    quality = candidate.analysis.orf_quality
    alignment = candidate.analysis.orf_alignment
    interpretation = candidate.analysis.protein_interpretation

    if metrics is None or metrics.best_orf is None:
        return ORFView(
            available=False,
            score=None,
            strand=None,
            frame=None,
            start=None,
            end=None,
            protein_length=None,
            complete=None,
            complete_orf_count=0,
            other_complete_orf_count=0,
            major_competing_orf_count=0,
            largest_competing_orf_length=0,
            reference_id=None,
            protein_identity=None,
            reference_coverage=None,
            n_terminal_missing=None,
            c_terminal_missing=None,
            internal_gap_residues=None,
            internal_gap_events=None,
            largest_internal_gap=None,
            internal_insertion_residues=None,
            internal_insertion_events=None,
            largest_internal_insertion=None,
            internal_deletion_residues=None,
            internal_deletion_events=None,
            largest_internal_deletion=None,
            difference_summary=(),
            interpretation_status=None,
            interpretation_summary=None,
            possible_frameshift_pattern=False,
            alignment_text=None,
            predicted_protein=None,
            reference_protein=None,
            predicted_header=None,
            reference_header=None,
            warnings=("No ORF was identified.",),
            relatedness=build_protein_relatedness_view(candidate),
        )

    best = metrics.best_orf
    warnings: list[str] = []
    if not best.complete:
        warnings.append("Best ORF is incomplete.")
    if metrics.major_competing_orf_count > 0:
        warnings.append(
            f"Major competing complete ORFs detected "
            f"({metrics.major_competing_orf_count})."
        )
    if alignment is not None:
        if alignment.reference_coverage < 0.90:
            warnings.append("Reference protein coverage is below 90%.")
        terminal_missing = (
            alignment.n_terminal_missing + alignment.c_terminal_missing
        )
        if terminal_missing > 0:
            warnings.append(
                f"Reference alignment is missing {terminal_missing} terminal residues."
            )
        if alignment.internal_gap_residues > 0:
            warnings.append(
                f"Protein alignment contains {alignment.internal_gap_residues} internal gap residues."
            )

    return ORFView(
        available=True,
        score=quality.score if quality is not None else None,
        strand=best.strand,
        frame=best.frame,
        start=best.start,
        end=best.end,
        protein_length=best.protein_length,
        complete=best.complete,
        complete_orf_count=metrics.complete_orf_count,
        other_complete_orf_count=metrics.other_complete_orf_count,
        major_competing_orf_count=metrics.major_competing_orf_count,
        largest_competing_orf_length=metrics.largest_competing_orf_length,
        reference_id=alignment.reference_id if alignment is not None else None,
        protein_identity=(
            alignment.amino_acid_identity if alignment is not None else None
        ),
        reference_coverage=(
            alignment.reference_coverage if alignment is not None else None
        ),
        n_terminal_missing=(
            alignment.n_terminal_missing if alignment is not None else None
        ),
        c_terminal_missing=(
            alignment.c_terminal_missing if alignment is not None else None
        ),
        internal_gap_residues=(
            alignment.internal_gap_residues if alignment is not None else None
        ),
        internal_gap_events=(
            alignment.internal_gap_events if alignment is not None else None
        ),
        largest_internal_gap=(
            alignment.largest_internal_gap if alignment is not None else None
        ),
        internal_insertion_residues=(
            alignment.internal_insertion_residues if alignment is not None else None
        ),
        internal_insertion_events=(
            alignment.internal_insertion_events if alignment is not None else None
        ),
        largest_internal_insertion=(
            alignment.largest_internal_insertion if alignment is not None else None
        ),
        internal_deletion_residues=(
            alignment.internal_deletion_residues if alignment is not None else None
        ),
        internal_deletion_events=(
            alignment.internal_deletion_events if alignment is not None else None
        ),
        largest_internal_deletion=(
            alignment.largest_internal_deletion if alignment is not None else None
        ),
        difference_summary=(
            interpretation.findings
            if interpretation is not None
            else _describe_protein_differences(alignment)
        ),
        interpretation_status=(
            interpretation.structural_status if interpretation is not None else None
        ),
        interpretation_summary=(
            interpretation.summary if interpretation is not None else None
        ),
        possible_frameshift_pattern=(
            interpretation.possible_frameshift_pattern
            if interpretation is not None
            else False
        ),
        alignment_text=_format_protein_alignment(alignment),
        predicted_protein=best.protein,
        reference_protein=(
            candidate.analysis.blastx.subject_protein
            if candidate.analysis.blastx is not None
            else None
        ),
        predicted_header=(
            f"{candidate.id}|selected_orf|strand={best.strand}|"
            f"frame={best.frame}|nt={best.start}-{best.end}|"
            f"length={best.protein_length}aa"
        ),
        reference_header=(
            candidate.analysis.blastx.subject_id
            if candidate.analysis.blastx is not None
            and candidate.analysis.blastx.subject_protein is not None
            else None
        ),
        warnings=tuple(warnings),
        relatedness=build_protein_relatedness_view(candidate),
    )
