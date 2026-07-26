from __future__ import annotations

from dataclasses import dataclass

from .reference_dotplot import BlastNHSP


@dataclass(frozen=True, slots=True)
class ContigDotplot:
    query_id: str
    target_id: str
    query_length: int
    target_length: int
    hsps: tuple[BlastNHSP, ...]
    query_coverage: float
    target_coverage: float
    identity_min: float | None
    identity_max: float | None
    output_path: str
    reused_existing: bool

    @property
    def available(self) -> bool:
        return bool(self.hsps)

    @property
    def block_count(self) -> int:
        return len(self.hsps)

    @property
    def orientation(self) -> str:
        strands = {hsp.strand for hsp in self.hsps}
        if not strands:
            return "unavailable"
        if strands == {"+"}:
            return "forward"
        if strands == {"-"}:
            return "reverse"
        return "mixed"

    @property
    def pair_key(self) -> str:
        return "__vs__".join(sorted((self.query_id, self.target_id)))

    def to_dict(self) -> dict[str, object]:
        return {
            "query_id": self.query_id,
            "target_id": self.target_id,
            "query_length": self.query_length,
            "target_length": self.target_length,
            "hsps": [hsp.to_dict() for hsp in self.hsps],
            "query_coverage": self.query_coverage,
            "target_coverage": self.target_coverage,
            "identity_min": self.identity_min,
            "identity_max": self.identity_max,
            "block_count": self.block_count,
            "orientation": self.orientation,
            "output_path": self.output_path,
            "reused_existing": self.reused_existing,
            "available": self.available,
            "pair_key": self.pair_key,
        }
