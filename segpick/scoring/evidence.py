from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class Evidence:
    """Normalised evidence values for one candidate.

    Values are between 0 and 1. A value of None means that the evidence
    channel is unavailable and its scoring weight should be redistributed
    across the available channels.
    """

    protein_confidence: float | None = None
    length_plausibility: float | None = None
    structural_integrity: float | None = None
    containment: float | None = None  # deprecated compatibility
    identity: float | None = None  # deprecated compatibility
    fragmentation: float | None = None  # deprecated compatibility
    coverage_sufficiency: float | None = None
    coverage_integrity: float | None = None
    orf_quality: float | None = None
    blastx_consistency: float | None = None

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            if value is None:
                continue

            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1; received {value}")

    def available(self) -> dict[str, float]:
        """Return only evidence channels that are available."""

        return {name: value for name, value in asdict(self).items() if value is not None}

    def to_dict(self) -> dict[str, float | None]:
        """Return active evidence channels as a plain dictionary."""

        values = asdict(self)
        for name in ("containment", "identity", "fragmentation"):
            values.pop(name, None)
        return values
