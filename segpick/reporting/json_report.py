from pathlib import Path
import json
from segpick.alignment.export import safe_name

def write_gene_json_reports(sample,outdir):
    outdir=Path(outdir); outdir.mkdir(parents=True,exist_ok=True)
    for name,g in sample.genes.items():
        data={'gene':g.name,'segment':g.segment,'anchor':g.anchor_id,'candidates':[],'references':[]}
        for c in g.candidates:
            data['candidates'].append({'id':c.id,'length':c.length,'confidence':c.metadata.confidence,'score':c.metadata.score,'z':c.metadata.z,'cluster':c.metadata.cluster,'blast_reference':c.metadata.sseqid,'containment':c.analysis.containment.to_dict()})
        for r in g.references:
            data['references'].append({'id':r.accession,'description':r.description,'length':r.length,'containment':r.containment.to_dict()})
        (outdir/f'{safe_name(name)}.json').write_text(json.dumps(data,indent=2))
