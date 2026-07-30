from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class ProteinInterpretation:
    """Biological interpretation derived from protein-alignment structure."""

    structural_status: str
    terminal_status: str
    internal_indel_pattern: str
    possible_frameshift_pattern: bool
    summary: str
    findings: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
