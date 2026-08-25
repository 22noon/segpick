from __future__ import annotations

from dataclasses import asdict, dataclass, replace


@dataclass(frozen=True, slots=True)
class ScoringWeights:
    """Relative weights applied to normalised evidence channels."""

    protein_confidence: float = 0.20
    length_plausibility: float = 0.08
    structural_integrity: float = 0.32
    containment: float = 0.0  # deprecated compatibility
    identity: float = 0.0  # deprecated compatibility
    fragmentation: float = 0.0  # deprecated compatibility
    coverage_sufficiency: float = 0.04
    coverage_integrity: float = 0.04
    orf_quality: float = 0.12
    blastx_consistency: float = 0.20

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            if value < 0:
                raise ValueError(f"{name} weight cannot be negative; received {value}")

        if self.total == 0:
            raise ValueError("At least one scoring weight must be greater than zero")

    @property
    def total(self) -> float:
        """Return the sum of all configured weights."""

        return sum(asdict(self).values())
    def normalised(self) -> ScoringWeights:
        total = self.total

        return ScoringWeights(
            protein_confidence=self.protein_confidence / total,
            length_plausibility=self.length_plausibility / total,
            structural_integrity=self.structural_integrity / total,
            containment=self.containment / total,
            identity=self.identity / total,
            fragmentation=self.fragmentation / total,
            coverage_sufficiency=self.coverage_sufficiency / total,
            coverage_integrity=self.coverage_integrity / total,
            orf_quality=self.orf_quality / total,
            blastx_consistency=self.blastx_consistency / total,
        )

    def with_overrides(
        self,
        **overrides: float | None,
    ) -> ScoringWeights:
        """Return a copy with non-None values replaced."""

        valid = {name: value for name, value in overrides.items() if value is not None}

        unknown = set(valid) - set(asdict(self))
        if unknown:
            raise ValueError("Unknown scoring weights: " + ", ".join(sorted(unknown)))

        return replace(self, **valid)

    def to_dict(self) -> dict[str, float]:
        """Return active weights as a plain dictionary."""

        values = asdict(self)
        for name in ("containment", "identity", "fragmentation"):
            values.pop(name, None)
        return values
