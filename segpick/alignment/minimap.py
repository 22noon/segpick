import shutil
import subprocess
from pathlib import Path

from segpick.io.paf import read_paf
from segpick.models import Gene


def run_minimap(
    anchor_fasta: str | Path,
    query_fasta: str | Path,
    paf_out: str | Path,
    preset: str = "asm5",
    cigar: bool = True,
) -> Path:
    """Run minimap2 and write a PAF file."""
    if shutil.which("minimap2") is None:
        raise RuntimeError("minimap2 was not found on PATH")
    paf_out = Path(paf_out)
    paf_out.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["minimap2", "-x", preset]
    if cigar:
        cmd.append("-c")
    cmd.extend([str(anchor_fasta), str(query_fasta)])
    with paf_out.open("w") as handle:
        subprocess.run(cmd, stdout=handle, check=True)
    return paf_out


def attach_existing_paf(gene, paf_path):
    alignments = read_paf(paf_path)
    gene.attach_alignments([a for a in alignments if a.query_id != a.target_id])
    return gene


def align_gene(
    gene: Gene,
    anchor_fasta: str | Path,
    query_fasta: str | Path,
    paf_out: str | Path,
    preset: str = "asm5",
) -> Gene:
    """Run minimap2 for one gene and attach PAF alignments to the Gene object."""
    paf = run_minimap(anchor_fasta, query_fasta, paf_out, preset=preset)
    gene.attach_alignments([a for a in read_paf(paf) if not (a.query_id == a.target_id)])
    return gene
