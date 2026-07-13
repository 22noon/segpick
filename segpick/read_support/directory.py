from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from segpick.models import ReadSupportMetrics, Sample

from .attach import attach_read_support
from .depth import parse_depth_file


@dataclass(frozen=True, slots=True)
class DepthAttachmentSummary:
    """Summary of attaching per-candidate depth files."""

    candidate_count: int
    files_found: int
    files_missing: int
    metrics_attached: int
    missing_candidates: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "candidate_count": self.candidate_count,
            "files_found": self.files_found,
            "files_missing": self.files_missing,
            "metrics_attached": self.metrics_attached,
            "missing_candidates": list(self.missing_candidates),
        }


def candidate_depth_path(
    depth_dir: str | Path,
    candidate_id: str,
    *,
    suffix: str = ".depth.txt",
) -> Path:
    """Return the expected depth-file path for one candidate."""

    if not suffix:
        raise ValueError("Depth filename suffix cannot be empty")

    return Path(depth_dir) / f"{candidate_id}{suffix}"


def attach_depth_directory(
    sample: Sample,
    depth_dir: str | Path,
    *,
    suffix: str = ".depth.txt",
    strict: bool = False,
    minimum_depth: int = 3,
    terminal_fraction: float = 0.05,
    minimum_terminal_bases: int = 50,
) -> DepthAttachmentSummary:
    """Attach read-support metrics from one depth file per candidate.

    Each candidate is matched to:

        <depth_dir>/<candidate_id><suffix>

    The depth file may contain rows for the candidate only, or rows for several
    sequences. When several sequence IDs occur, the matching candidate ID is
    selected.

    Args:
        sample: Sample containing genes and candidate contigs.
        depth_dir: Directory containing per-candidate depth files.
        suffix: Filename suffix appended to each candidate ID.
        strict: Raise when an expected depth file is missing.
        minimum_depth: Minimum depth used for coverage completeness.
        terminal_fraction: Fraction of the sequence used for terminal windows.
        minimum_terminal_bases: Minimum terminal-window size.

    Returns:
        Summary of discovered, missing, and attached depth files.
    """

    depth_dir = Path(depth_dir)

    if not depth_dir.exists():
        raise FileNotFoundError(
            f"Depth directory does not exist: {depth_dir}"
        )

    if not depth_dir.is_dir():
        raise NotADirectoryError(
            f"Depth path is not a directory: {depth_dir}"
        )

    candidate_count = 0
    files_found = 0
    metrics_attached = 0
    missing_candidates: list[str] = []

    for gene in sample.genes.values():
        for candidate in gene.candidates:
            candidate_count += 1

            path = candidate_depth_path(
                depth_dir,
                candidate.id,
                suffix=suffix,
            )

            if not path.exists():
                missing_candidates.append(candidate.id)

                if strict:
                    raise FileNotFoundError(
                        f"Depth file not found for candidate "
                        f"{candidate.id!r}: {path}"
                    )

                continue

            files_found += 1
            parsed = parse_depth_file(path)

            if candidate.id in parsed:
                position_depths = parsed[candidate.id]
            elif len(parsed) == 1:
                # Supports files whose first column uses an alternative
                # sequence label, provided the file contains only one sequence.
                position_depths = next(iter(parsed.values()))
            else:
                available = ", ".join(sorted(parsed))

                raise KeyError(
                    f"Depth file {path} does not contain candidate "
                    f"{candidate.id!r}. Available sequence IDs: {available}"
                )

            attach_read_support(
                candidate,
                position_depths,
                minimum_depth=minimum_depth,
                terminal_fraction=terminal_fraction,
                minimum_terminal_bases=minimum_terminal_bases,
            )

            metrics_attached += 1

    return DepthAttachmentSummary(
        candidate_count=candidate_count,
        files_found=files_found,
        files_missing=len(missing_candidates),
        metrics_attached=metrics_attached,
        missing_candidates=tuple(missing_candidates),
    )


def attached_read_support(
    sample: Sample,
) -> dict[str, ReadSupportMetrics]:
    """Return all currently attached read-support metrics by candidate ID."""

    return {
        candidate.id: candidate.analysis.read_support
        for gene in sample.genes.values()
        for candidate in gene.candidates
        if candidate.analysis.read_support is not None
    }
