"""Allowlisted public projection shared by the HTTP API and static compiler."""
from __future__ import annotations
from .schema import SCHEMAS

def project_public(records,media_base=''):
    """Never serialize a stored payload wholesale. Relationship IDs are filtered too."""
    public={c:[x for x in records.get(c,[]) if x.get('visibility')=='public'] for c in SCHEMAS}
    ids={c:{x['id'] for x in items} for c,items in public.items()}
    result={c:[] for c in SCHEMAS}
    for collection,items in public.items():
        for p in items:
            if collection=='settings' and p['id']!='laboratory': continue
            if collection=='milestones' and (p.get('project_id') not in ids['projects'] or p.get('researcher_id') not in ids['people']): continue
            if collection=='updates' and p.get('researcher_id') not in ids['people']: continue
            out={'id':p['id']}
            for field in SCHEMAS[collection]['fields']:
                key=field['key']
                if not field['public'] or key in ('photo_upload_id','document_public'): continue
                v=p.get(key)
                if field['relation']:
                    allowed=ids[field['relation']]
                    v=[i for i in (v or []) if i in allowed] if field['type']=='multi' else (v if v in allowed else '')
                out[key]=v
            # Only administrators can approve a photograph for local public delivery.
            if collection=='people' and p.get('photo_upload_id') and p.get('photo_permission')=='approved':
                out['photo_url']=media_base+'/media/'+p['photo_upload_id']
            if collection=='publications' and p.get('document_public') and p.get('document_id'):
                out['document_url']=media_base+'/media/'+p['document_id']
            result[collection].append(out)
    return result
