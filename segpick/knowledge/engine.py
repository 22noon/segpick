from __future__ import annotations
from segpick.models import BiologicalFinding, BiologicalScenario, EvidenceObservation
from .schema import KnowledgeModule

_ORDER=("low","moderate","high")

def evaluate_scenarios(modules, observations, findings, candidate_ids=()):
    out=[]
    for m in modules:
        req=tuple(c.label for c in m.requires if c.matches(observations, findings))
        if len(req)!=len(m.requires): continue
        sup=tuple(c.label for c in m.supports if c.matches(observations, findings))
        con=tuple(c.label for c in m.conflicts if c.matches(observations, findings))
        i=_ORDER.index(m.base_confidence)
        if sup and not con: i=min(2,i+1)
        if con: i=max(0,i-1)
        out.append(BiologicalScenario(m.scenario_id,m.title,m.category,m.scope,_ORDER[i],m.severity,m.interpretation,candidate_ids,req,sup,con,m.suggested_actions,m.source,m.references))
    return tuple(out)
