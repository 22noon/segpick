from pathlib import Path
from segpick.models import Sample, Gene
from segpick.io.fasta import write_records
def safe_name(name: str) -> str:
    """Return a filesystem-safe gene name."""
    return name.replace("/", "_").replace("\\", "_").replace(":", "_").replace("|", "_").replace(" ", "_")
def export_gene_fasta(gene: Gene, outdir: str | Path) -> Path:
    outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True); out = outdir / f"{safe_name(gene.name)}.fa"; write_records(gene.all_records(), out); return out
def export_anchor_fasta(gene: Gene, outdir: str | Path) -> Path:
    outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True); anchor = gene.anchor_record()
    if anchor is None: raise ValueError(f"Gene {gene.name!r} has no anchor sequence")
    out = outdir / f"{safe_name(gene.name)}.anchor.fa"; write_records([anchor], out); return out
def export_gene_fastas(sample: Sample, outdir: str | Path) -> dict[str, Path]: return {name: export_gene_fasta(gene, outdir) for name, gene in sample.genes.items()}
def export_anchor_fastas(sample: Sample, outdir: str | Path) -> dict[str, Path]: return {name: export_anchor_fasta(gene, outdir) for name, gene in sample.genes.items()}
