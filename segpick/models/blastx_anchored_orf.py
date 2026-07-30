from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class BlastXAnchoredORF:
    """Coding sequence extended in the frame and strand of a DIAMOND hit.

    Coordinates use zero-based, end-exclusive positions on the original contig.
    ``nucleotide_sequence`` includes a terminal stop codon when one is found;
    ``protein_sequence`` never includes the terminal ``*``.
    """

    start: int
    end: int
    strand: str
    frame: int
    nucleotide_sequence: str
    protein_sequence: str
    has_start_codon: bool
    has_stop_codon: bool
    reaches_contig_start: bool
    reaches_contig_end: bool
    selected_orf_available: bool
    matches_selected_orf: bool
    same_strand: bool | None
    same_frame: bool | None
    same_start: bool | None
    same_end: bool | None
    n_terminal_difference_aa: int | None
    c_terminal_difference_aa: int | None

    @property
    def nucleotide_length(self) -> int:
        return len(self.nucleotide_sequence)

    @property
    def protein_length(self) -> int:
        return len(self.protein_sequence)

    @property
    def complete(self) -> bool:
        return self.has_start_codon and self.has_stop_codon

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload.update(
            nucleotide_length=self.nucleotide_length,
            protein_length=self.protein_length,
            complete=self.complete,
        )
        return payload
