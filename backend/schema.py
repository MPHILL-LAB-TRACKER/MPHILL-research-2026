"""Shared, explicit form and public-output schemas. Unknown input keys are rejected."""
from __future__ import annotations
import re
from datetime import date
from urllib.parse import urlparse


def f(key, label, kind='text', *, required=False, options=None, relation=None, public=True, help=''):
    return dict(key=key, label=label, type=kind, required=required, options=options or [], relation=relation, public=public, help=help)

P=f('people','Researchers','multi',relation='people')
NOTE=f('internal_notes','Internal notes','textarea',public=False,help='Never included in the public website or public export.')
SOURCE=f('source_url','Evidence / source URL','url')
SCHEMAS={
 'settings':dict(label='Website settings', title='title', fields=[
  f('title','Laboratory name',required=True),f('short_name','Short name'),f('institution','Institution'),
  f('hero_title','Homepage heading',required=True),f('hero_intro','Homepage introduction','textarea'),
  f('contact_name','Public contact name'),f('contact_email','Public contact email','email'),f('address','Public address','textarea'),
  f('hero_image_url','Homepage photograph URL','url'),f('hero_image_credit','Photograph credit'),f('hero_image_source','Photograph source page','url'),f('materials_image_url','Supporting materials photograph URL','url'),f('materials_image_credit','Materials photograph credit'),f('microscopy_image_url','Supporting microscopy photograph URL','url'),f('microscopy_image_credit','Microscopy photograph credit'),f('reviewed','Content review date','date')]),
 'capabilities':dict(label='Homepage research',title='title',fields=[f('title','Research heading',required=True),f('text','Description','textarea',required=True),f('order','Display order','number')]),
 'people':dict(label='Researchers & collaborators',title='name',fields=[
  f('name','Full display name',required=True),f('group','Directory','select',options=['researcher','collaborator'],required=True),f('role','Position / qualifications'),
  f('bio','Biography','textarea'),f('topics','Research interests','lines'),f('work','Selected work','textarea'),f('note','Public evidence note','textarea'),
  f('scholar_url','Google Scholar','url'),f('researchgate_url','ResearchGate','url'),f('linkedin_url','LinkedIn profile / attributed post','url'),f('orcid_url','ORCID','url'),
  f('photo_url','Remote portrait URL','url',help='Use only a portrait attributed to this named researcher; not a group-photo guess.'),
  f('photo_upload_id','Uploaded portrait','image'),f('photo_credit','Photographer / credit'),f('photo_source_url','Portrait source page','url'),
  f('photo_permission','Portrait permission','select',options=['not-recorded','unconfirmed','approved'],help='A public profile is not automatically a reuse licence. An approved local upload takes priority.'),
  f('source_urls','Biography evidence URLs','urls'),NOTE]),
 'publications':dict(label='Publications',title='title',fields=[
  f('title','Title',required=True),f('year','Publication year','year',required=True),f('authors','Authors — one per line','lines',required=True),P,
  f('venue','Journal / publisher / university'),f('volume','Volume / issue'),f('number','Article number / pages'),f('doi','DOI'),
  f('type','Evidence / output type','select',options=['peer-reviewed','author-listed','catalogued','preprint','chapter'],required=True),SOURCE,
  f('summary','Public summary','textarea'),f('note','Public evidence note','textarea'),f('document_id','PDF','document',public=False),
  f('document_public','Allow public download of this PDF','checkbox',help='Only publish a document when you have the right to distribute it.'),NOTE]),
 'collaborations':dict(label='Collaborations',title='title',fields=[f('title','Collaboration title',required=True),f('partner','Partner institution / group'),P,f('period','Period / source date'),f('summary','Public summary','textarea'),f('detail','Description','textarea'),SOURCE,f('note','Evidence / attribution note','textarea'),NOTE]),
 'projects':dict(label='Active research',title='title',fields=[
  f('title','Research project title',required=True),f('lead_id','Lead researcher','relation',relation='people',required=True),P,
  f('collaborators','Linked collaborations','multi',relation='collaborations'),f('funders','Linked funders','multi',relation='funders'),
  f('stage','Project stage','select',required=True,options=['planned','active','analysis','completed','on-hold']),
  f('summary','Public project summary','textarea'),f('start_date','Start date','date'),f('due_date','Target completion','date'),
  f('public_progress','Approved public progress (%)','percent',help='A deliberately approved figure; internal milestones never change public progress automatically.'),NOTE]),
 'manuscripts':dict(label='Manuscript pipeline',title='title',fields=[
  f('title','Manuscript title',required=True),P,f('project_id','Linked research project','relation',relation='projects'),
  f('stage','Manuscript stage','select',required=True,options=['idea','drafting','internal-review','submitted','under-review','revisions','accepted','published']),
  f('summary','Approved public summary','textarea'),f('journal','Journal (public when published here)'),f('doi','DOI'),
  f('due_date','Internal next deadline','date',public=False),f('submission_id','Journal submission reference',public=False),
  f('document_id','Private manuscript PDF','document',public=False),NOTE]),
 'milestones':dict(label='Milestones & progress',title='title',fields=[
  f('title','Milestone',required=True),f('project_id','Project','relation',relation='projects',required=True),
  f('researcher_id','Responsible researcher','relation',relation='people',required=True),
  f('status','Status','select',required=True,options=['todo','in-progress','done','blocked']),
  f('due_date','Target date','date'),f('weight','Weight toward internal project progress','weight'),f('summary','Optional public milestone summary','textarea'),NOTE]),
 'updates':dict(label='Research updates',title='title',fields=[
  f('title','Update title',required=True),f('researcher_id','Researcher','relation',relation='people',required=True),
  f('project_id','Project','relation',relation='projects'),f('date','Date','date',required=True),
  f('kind','Update type','select',options=['progress','experiment','conference','award','dataset','bio-change','other'],required=True),
  f('text','Update / proposed biography text','textarea',required=True),f('document_id','Supporting PDF','document',public=False),NOTE]),
 'funders':dict(label='Funders',title='name',fields=[
  f('name','Funder name',required=True),f('website','Website','url'),f('summary','Public acknowledgement','textarea'),
  f('award_reference','Public award reference'),SOURCE,f('amount','Internal awarded amount','money',public=False),f('currency','Internal currency',public=False),
  f('start_date','Funding start','date'),f('end_date','Funding end','date'),NOTE]),
 'sources':dict(label='Sources & credits',title='title',fields=[f('title','Source title',required=True),f('url','Source URL','url'),f('kind','Source type'),f('note','Evidence / reuse note','textarea')])
}
SLUG=re.compile(r'^[a-z0-9][a-z0-9-]{0,79}$')
RESEARCHER_COLLECTIONS={'projects','manuscripts','milestones','updates','people'}
RESEARCHER_EDIT={'manuscripts','milestones','updates'}

def default_value(field):
    if field['type'] in ('multi','lines','urls'): return []
    if field['type']=='checkbox': return False
    if field['type'] in ('number','year','weight','percent','money'): return None
    return ''

def safe_url(value):
    if not value: return True
    p=urlparse(value)
    return p.scheme in ('http','https') and bool(p.netloc) and not p.username and not p.password and not any(ord(c)<32 for c in value)

def validate(collection, payload):
    if collection not in SCHEMAS or not isinstance(payload,dict): raise ValueError('Unknown collection or invalid record.')
    fields=SCHEMAS[collection]['fields']
    allowed={x['key'] for x in fields}|{'id','visibility'}
    unknown=set(payload)-allowed
    if unknown: raise ValueError('Unexpected fields: '+', '.join(sorted(unknown)))
    rid=payload.get('id','')
    if not isinstance(rid,str) or not SLUG.fullmatch(rid): raise ValueError('Record ID must use 1–80 lowercase letters, digits or hyphens.')
    visibility=payload.get('visibility','private')
    if visibility not in ('public','private'): raise ValueError('Choose public or private visibility.')
    out={'id':rid,'visibility':visibility}
    for field in fields:
        key,t=field['key'],field['type']; v=payload.get(key,default_value(field))
        if field['required'] and (v is None or v=='' or v==[]): raise ValueError(field['label']+' is required.')
        if t in ('lines','multi','urls'):
            if not isinstance(v,list) or len(v)>150 or any(not isinstance(s,str) or not s.strip() or len(s)>2000 for s in v): raise ValueError(field['label']+' must be a list of non-empty values.')
            v=list(dict.fromkeys(s.strip() for s in v))
            if t=='urls' and not all(safe_url(s) for s in v): raise ValueError('Invalid evidence URL.')
        elif t=='checkbox':
            if type(v) is not bool: raise ValueError(field['label']+' must be true or false.')
        elif t in ('number','year','weight','percent','money'):
            if v in (None,''): v=None
            else:
                if type(v) not in (int,float): raise ValueError(field['label']+' must be numeric.')
                if t!='money' and int(v)!=v: raise ValueError(field['label']+' must be a whole number.')
                low,high={'year':(1600,2100),'weight':(1,100),'percent':(0,100),'money':(0,1e12),'number':(0,10000)}[t]
                if not low<=v<=high: raise ValueError(field['label']+' is out of range.')
        else:
            if not isinstance(v,str) or len(v)>(30000 if t=='textarea' else 3000): raise ValueError(field['label']+' is invalid or too long.')
            v=v.strip()
            if t=='select' and v and v not in field['options']: raise ValueError('Invalid '+field['label'])
            if t=='url' and not safe_url(v): raise ValueError('Use an absolute HTTP(S) URL for '+field['label'])
            if t=='date' and v:
                try: date.fromisoformat(v)
                except ValueError: raise ValueError('Use YYYY-MM-DD for '+field['label'])
            if t=='email' and v and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',v): raise ValueError('Invalid email address.')
            if t in ('relation','image','document') and v and not SLUG.fullmatch(v): raise ValueError('Invalid linked record.')
            if key=='doi' and v and not re.fullmatch(r'10\.\d{4,9}/\S+',v): raise ValueError('Enter the DOI only, beginning 10., not a URL.')
        out[key]=v
    for start,end in [('start_date','due_date'),('start_date','end_date')]:
        if out.get(start) and out.get(end) and out[start]>out[end]: raise ValueError('The end date must not precede the start date.')
    return out
