from dataclasses import dataclass, field
from .gene import Gene
@dataclass(slots=True)
class Sample:
    """A BTV assembly sample containing multiple genes/segments."""
    name: str = "sample"
    genes: dict[str, Gene] = field(default_factory=dict)
    def add_gene(self, gene: Gene) -> None: self.genes[gene.name] = gene
    def __len__(self) -> int: return len(self.genes)
    def summary_lines(self) -> list[str]:
        lines = [f"Sample: {self.name}", f"Loaded genes: {len(self.genes)}", ""]
        for gene_name in sorted(self.genes):
            gene = self.genes[gene_name]; best = gene.best_by_confidence()
            lines.append(f"{gene.name}	segment={gene.segment}	candidates={len(gene.candidates)}	references={len(gene.references)}	anchor={gene.anchor_id or gene.longest_sequence_id()}	alignments={len(gene.alignments)}	best_conf={best.id if best else 'NA'}")
        return lines
