from pathlib import Path

from segpick.models import Alignment


def read_paf(path: str | Path) -> list[Alignment]:
    """Read a minimap2 PAF file into Alignment objects."""
    path = Path(path)
    alignments: list[Alignment] = []
    if not path.exists() or path.stat().st_size == 0:
        return alignments
    with path.open() as handle:
        for line in handle:
            if not line.strip():
                continue
            f = line.rstrip("\n").split("\t")
            if len(f) < 12:
                continue
            alignments.append(
                Alignment(
                    query_id=f[0],
                    query_length=int(f[1]),
                    query_start=int(f[2]),
                    query_end=int(f[3]),
                    strand=f[4],
                    target_id=f[5],
                    target_length=int(f[6]),
                    target_start=int(f[7]),
                    target_end=int(f[8]),
                    matches=int(f[9]),
                    alignment_length=int(f[10]),
                    mapq=int(f[11]),
                )
            )
    return alignments
