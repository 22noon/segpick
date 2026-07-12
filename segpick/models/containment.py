from dataclasses import dataclass, asdict

@dataclass(slots=True)
class ContainmentMetrics:
    aligned_query_bp: int = 0
    aligned_anchor_bp: int = 0
    query_length: int = 0
    anchor_length: int = 0
    query_coverage: float = 0.0
    anchor_coverage: float = 0.0
    identity: float = 0.0
    fragmentation: float = 1.0
    n_blocks: int = 0
    largest_block_bp: int = 0
    left_clip: int = 0
    right_clip: int = 0
    orientation: str = "."
    structural_score: float = 0.0
    status: str = "NO_ALIGNMENT"

    def to_dict(self):
        return asdict(self)
