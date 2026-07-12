from pathlib import Path
import pandas as pd
REQUIRED_COLUMNS = {"genes", "contig", "segment", "score", "confidence", "cluster", "sseqid"}
def read_hits(path: str | Path) -> pd.DataFrame:
    """Read selected_hits.tsv. The file may be tab-separated or whitespace-separated."""
    hits = pd.read_csv(path, sep=r"\s+")
    missing = REQUIRED_COLUMNS - set(hits.columns)
    if missing: raise ValueError("selected hits file is missing required columns: " + ", ".join(sorted(missing)))
    return hits
