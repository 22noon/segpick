from pathlib import Path

from Bio import SeqIO
from Bio.SeqRecord import SeqRecord


def read_fasta_dict(path: str | Path) -> dict[str, SeqRecord]:
    """Read a FASTA file into a dictionary keyed by sequence id."""
    return SeqIO.to_dict(SeqIO.parse(str(path), "fasta"))


def write_records(records: list[SeqRecord], path: str | Path) -> None:
    """Write sequence records to FASTA."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    SeqIO.write(records, str(path), "fasta")
