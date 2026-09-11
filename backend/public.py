"""Allowlisted public projection shared by the HTTP API and static compiler."""
from __future__ import annotations
from .schema import SCHEMAS
from .assets import portrait_data, certificate_data, homepage_data

def project_public(records, media_base=''):
    """No stored payload, hidden field or private relationship is serialized wholesale."""
    public={c:[p for p in records.get(c,[]) if p.get('visibility')=='public'] for c in SCHEMAS}
    public['media']=[p for p in public['media'] if p.get('approved') is True and p.get('file_id')]
    ids={c:{p['id'] for p in items} for c,items in public.items()}
    result={c:[] for c in SCHEMAS}
    for collection,items in public.items():
        for p in items:
            if collection=='settings' and p['id']!='laboratory':continue
            if collection=='theme' and p['id']!='website':continue
            if collection=='milestones' and (p.get('project_id') not in ids['projects'] or p.get('researcher_id') not in ids['people']):continue
            if collection in ('updates','achievements') and p.get('researcher_id') not in ids['people']:continue
            if collection=='announcements' and any(rid not in ids['people'] for rid in p.get('people',[])):continue
            if collection in ('sections','contacts') and p.get('researcher_id') and p['researcher_id'] not in ids['people']:continue
            if collection=='fields' and p.get('target_id') not in ids.get(p.get('target_collection'),set()):continue
            hidden=set(p.get('hidden_fields') or [])
            out={'id':p['id']}
            for field in SCHEMAS[collection]['fields']:
                key=field['key']
                if not field['public'] or key in hidden or key in ('photo_upload_id','document_public'):continue
                value=p.get(key)
                if field['relation']:
                    allowed=ids[field['relation']]
                    value=[i for i in (value or []) if i in allowed] if field['type']=='multi' else (value if value in allowed else '')
                out[key]=value
            if collection=='people' and 'photo_url' not in hidden and p.get('photo_permission')=='approved':
                if p.get('bundled_portrait'):out['photo_url']=portrait_data(p['bundled_portrait'])
                if p.get('photo_upload_id'):out['photo_url']=media_base+'/media/'+p['photo_upload_id']
            if collection=='achievements' and p.get('document_public') and not p.get('document_id'):out.update(certificate_data(p.get('certificate_key','')))
            if collection in ('publications','achievements') and p.get('document_public') and p.get('document_id'):out['document_url']=media_base+'/media/'+p['document_id']
            if collection=='settings' and p.get('hero_permission')=='approved' and 'hero_image_url' not in hidden:
                if p.get('bundled_hero'):out['hero_image_url']=homepage_data(p['bundled_hero'])
                if p.get('hero_upload_id'):out['hero_image_url']=media_base+'/media/'+p['hero_upload_id']
            if collection=='theme' and p.get('logo_approved') and p.get('logo_upload_id'):out['logo_url']=media_base+'/media/'+p['logo_upload_id']
            if collection=='media':out['asset_url']=media_base+'/media/'+p['file_id']
            result[collection].append(out)
    # A parent can itself be filtered by an assignment rule above.
    visible_ids={c:{p['id'] for p in ps} for c,ps in result.items()}
    result['fields']=[p for p in result['fields'] if p['target_id'] in visible_ids.get(p['target_collection'],set())]
    return result
