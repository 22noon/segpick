def classify_status(query_coverage, identity, fragmentation, n_blocks):
    if query_coverage == 0:
        return "NO_ALIGNMENT"
    if identity < 0.80 or query_coverage < 0.50:
        return "POOR"
    if n_blocks > 1 and fragmentation > 0.20:
        return "FRAGMENTED"
    if query_coverage >= 0.95 and identity >= 0.95 and fragmentation <= 0.10:
        return "COMPLETE"
    return "PARTIAL"
