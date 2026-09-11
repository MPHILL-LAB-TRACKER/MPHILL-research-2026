"""Shared, explicit form and public-output schemas. Unknown input keys are rejected."""
from __future__ import annotations
import re
from datetime import date
from urllib.parse import urlparse
from .assets import PORTRAITS, CERTIFICATES


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
  f('photo_upload_id','Uploaded portrait','image'),f('bundled_portrait','Portrait supplied in Team.pptx','select',options=list(PORTRAITS),public=False,help='The supplied presentation photograph. An approved uploaded portrait takes priority; choose an empty option to remove this fallback.'),f('photo_credit','Photographer / credit'),f('photo_source_url','Portrait source page','url'),
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
 'announcements':dict(label='Homepage alerts & events',title='title',fields=[
  f('title','Alert title',required=True),f('kind','Activity type','select',required=True,options=['conference','seminar','notice']),P,
  f('description','Public description','textarea',required=True),f('host','Host / organiser'),f('location','Location'),
  f('start_date','Laboratory-supplied start date','date'),f('end_date','Laboratory-supplied end date','date'),
  f('date_status','Date evidence','select',required=True,options=['host-confirmed','lab-supplied','date-conflict','date-to-be-announced']),
  f('official_start_date','Host-published start date','date'),f('official_end_date','Host-published end date','date'),
  f('official_url','Official conference / host page','url'),f('evidence_note','Public date / participation evidence note','textarea'),
  f('homepage','Show in homepage Alerts','checkbox'),NOTE]),
 'achievements':dict(label='Achievements & certificates',title='title',fields=[
  f('title','Achievement title',required=True),f('researcher_id','Researcher','relation',relation='people',required=True),
  f('date','Activity date','date',required=True),f('summary','Achievement description','textarea',required=True),
  f('evidence_note','What the evidence supports','textarea'),f('homepage','Show recognition on the homepage','checkbox'),
  f('certificate_key','Owner-supplied certificate','select',options=list(CERTIFICATES),public=False),
  f('document_id','Replacement certificate PDF','document',public=False),
  f('document_public','Publish certificate PDF','checkbox',help='Explicitly approve distribution of this certificate. A replacement upload overrides the bundled certificate.'),NOTE]),
 'funders':dict(label='Funders',title='name',fields=[
  f('name','Funder name',required=True),f('website','Website','url'),f('summary','Public acknowledgement','textarea'),
  f('award_reference','Public award reference'),SOURCE,f('amount','Internal awarded amount','money',public=False),f('currency','Internal currency',public=False),
  f('start_date','Funding start','date'),f('end_date','Funding end','date'),NOTE]),
 'sources':dict(label='Sources & credits',title='title',fields=[f('title','Source title',required=True),f('url','Source URL','url'),f('kind','Source type'),f('note','Evidence / reuse note','textarea')])
}
# V4: schema-driven admin editors; private fields never enter public projection.
SCHEMAS['settings']['fields'] += [
 f('hero_motion','Animate homepage photograph','checkbox'),
 f('hero_image_alt','Homepage photograph description'),f('hero_image_caption','Homepage photograph caption'),
 f('hero_upload_id','Upload homepage photograph','image',public=False),
 f('bundled_hero','Bundled homepage photograph','select',options=['laboratory-v4'],public=False),
 f('hero_permission','Homepage photograph permission','select',options=['not-recorded','approved'],public=False)]
SCHEMAS['people']['fields'] += [f('affiliation','Institution'),f('department','Department'),f('qualifications','Qualifications'),
 f('public_email','Public professional email','email'),f('public_phone','Public professional telephone'),f('website','Professional website','url'),
 f('private_email','Private email','email',public=False),f('private_phone','Private telephone',public=False),
 f('private_address','Private contact address','textarea',public=False)]
SCHEMAS['media']=dict(label='Media library',title='title',fields=[
 f('title','Title',required=True),f('kind','Media type','select',options=['image','video','document'],required=True),
 f('file_id','Uploaded media file','asset',public=False),f('approved','Approve this file for public sharing','checkbox',public=False),
 f('alt','Image / video description'),f('caption','Caption','textarea'),f('credit','Photographer / creator credit'),
 f('transcript','Video transcript','textarea'),SOURCE,NOTE])
SCHEMAS['sections']=dict(label='Pages & sections',title='title',fields=[
 f('title','Section title',required=True),f('eyebrow','Small heading'),f('body','Section text','textarea'),
 f('location','Display location','select',options=['homepage','researcher-profile','standalone-page'],required=True),
 f('position','Homepage position','select',options=['after-hero','after-alerts','after-research','before-footer']),
 f('researcher_id','Researcher profile','relation',relation='people'),
 f('layout','Layout','select',options=['text','split','gallery']),f('order','Display order','number'),
 f('media_items','Photographs / videos / documents','multi',relation='media'),
 f('navigation','Show standalone page in navigation','checkbox'),f('nav_label','Navigation label'),NOTE])
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
            if t in ('relation','image','document','asset') and v and not SLUG.fullmatch(v): raise ValueError('Invalid linked record.')
            if key=='doi' and v and not re.fullmatch(r'10\.\d{4,9}/\S+',v): raise ValueError('Enter the DOI only, beginning 10., not a URL.')
        out[key]=v
    for start,end in [('start_date','due_date'),('start_date','end_date')]:
        if out.get(start) and out.get(end) and out[start]>out[end]: raise ValueError('The end date must not precede the start date.')
    if collection == 'announcements':
        for first, last in [('start_date', 'end_date'), ('official_start_date', 'official_end_date')]:
            if out[last] and (not out[first] or out[last] < out[first]):
                raise ValueError('The end date must be on or after the corresponding start date.')
        if out['date_status'] == 'date-to-be-announced':
            if out['start_date'] or out['end_date']:
                raise ValueError('A date-to-be-announced activity must not contain a scheduled date.')
        elif not out['start_date']:
            raise ValueError('A dated activity needs a start date.')
        if out['date_status'] == 'date-conflict' and not out['evidence_note']:
            raise ValueError('Explain the date discrepancy in the public evidence note.')
    if collection=='sections' and out['location']=='researcher-profile' and not out['researcher_id']:
        raise ValueError('Select a researcher for a profile section.')
    return out
