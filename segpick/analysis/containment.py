from collections import defaultdict
from segpick.models import ContainmentMetrics
from .status import classify_status

def merged_length(intervals):
    if not intervals: return 0
    iv=sorted((min(a,b),max(a,b)) for a,b in intervals)
    total=0; s,e=iv[0]
    for a,b in iv[1:]:
        if a <= e: e=max(e,b)
        else: total += e-s; s,e=a,b
    return total + e-s

def summarise_alignments(alignments):
    if not alignments: return ContainmentMetrics()
    qlen=alignments[0].query_length; tlen=alignments[0].target_length
    aq=merged_length([(a.query_start,a.query_end) for a in alignments])
    at=merged_length([(a.target_start,a.target_end) for a in alignments])
    matches=sum(a.matches for a in alignments); alen=sum(a.alignment_length for a in alignments)
    largest=max((a.query_end-a.query_start for a in alignments), default=0)
    qcov=aq/qlen if qlen else 0; tcov=at/tlen if tlen else 0; ident=matches/alen if alen else 0
    frag=1-largest/aq if aq else 1
    left=min(a.query_start for a in alignments); right=max(0, qlen-max(a.query_end for a in alignments))
    strands={a.strand for a in alignments}; orient=next(iter(strands)) if len(strands)==1 else 'mixed'
    score=qcov*ident*(1-frag)
    return ContainmentMetrics(aq,at,qlen,tlen,qcov,tcov,ident,frag,len(alignments),largest,left,right,orient,score,classify_status(qcov,ident,frag,len(alignments)))

def analyse_gene(gene):
    byq=defaultdict(list)
    for a in gene.alignments: byq[a.query_id].append(a)
    for c in gene.candidates:
        if c.id == gene.anchor_id:
            c.analysis.containment=ContainmentMetrics(c.length,c.length,c.length,c.length,1,1,1,0,1,c.length,0,0,'+',1,'ANCHOR')
        else:
            c.analysis.containment=summarise_alignments(byq.get(c.id,[]))
    for r in gene.references:
        if r.accession == gene.anchor_id:
            r.containment=ContainmentMetrics(r.length,r.length,r.length,r.length,1,1,1,0,1,r.length,0,0,'+',1,'ANCHOR')
        else:
            r.containment=summarise_alignments(byq.get(r.accession,[]))
    return gene
