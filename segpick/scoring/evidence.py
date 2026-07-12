from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class Evidence:
    """Normalised evidence values for one candidate.

    Every value is expected to be between 0 and 1.
    Raw measurements such as confidence, z-score, identity, and coverage
    remain stored elsewhere and are not modified by this class.
    """

    protein_confidence: float
    length_plausibility: float
    containment: float
    identity: float
    fragmentation: float

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"{name} must be between 0 and 1; received {value}"
                )

    def to_dict(self) -> dict[str, float]:
        """Return evidence as a plain dictionary."""

        return asdict(self)
