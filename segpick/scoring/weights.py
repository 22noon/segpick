from __future__ import annotations

from dataclasses import asdict, dataclass, replace


@dataclass(frozen=True, slots=True)
class ScoringWeights:
    """Relative weights applied to normalised evidence channels."""

    protein_confidence: float = 0.30
    length_plausibility: float = 0.15
    containment: float = 0.25
    identity: float = 0.15
    fragmentation: float = 0.15

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            if value < 0:
                raise ValueError(
                    f"{name} weight cannot be negative; received {value}"
                )

        if self.total == 0:
            raise ValueError("At least one scoring weight must be greater than zero")

    @property
    def total(self) -> float:
        """Return the sum of all configured weights."""

        return sum(asdict(self).values())

    def normalised(self) -> "ScoringWeights":
        """Return weights scaled so they sum to one."""

        total = self.total
        return ScoringWeights(
            **{
                name: value / total
                for name, value in asdict(self).items()
            }
        )

    def with_overrides(
        self,
        **overrides: float | None,
    ) -> "ScoringWeights":
        """Return a copy with non-None values replaced."""

        valid = {
            name: value
            for name, value in overrides.items()
            if value is not None
        }

        unknown = set(valid) - set(asdict(self))
        if unknown:
            raise ValueError(
                "Unknown scoring weights: " + ", ".join(sorted(unknown))
            )

        return replace(self, **valid)

    def to_dict(self) -> dict[str, float]:
        """Return weights as a plain dictionary."""

        return asdict(self)
