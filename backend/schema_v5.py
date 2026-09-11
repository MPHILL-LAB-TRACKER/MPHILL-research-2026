"""V5 editorial controls. Data-driven fields, not executable HTML/CSS."""
from __future__ import annotations
import re
from datetime import date

HOME_BLOCKS = ['hero', 'alerts', 'research', 'people', 'recognition', 'contacts']
NAV_ITEMS = ['researchers', 'activity', 'publications', 'research', 'pipeline', 'collaborators', 'funders', 'sources', 'gallery']
THEME_DEFAULTS = {
    'id': 'website', 'visibility': 'public', 'title': 'Website appearance',
    'primary': '#244d3e', 'accent': '#a88451', 'background': '#f5f3eb',
    'surface': '#ffffff', 'text_color': '#1d3028', 'muted_color': '#616c63',
    'border_color': '#d9dfd4', 'heading_font': 'serif', 'body_font': 'sans',
    'font_size': 16, 'content_width': 1200, 'corner_radius': 16,
    'density': 'comfortable', 'hero_layout': 'photo-right',
    'home_blocks': HOME_BLOCKS.copy(), 'hidden_navigation': [],
    'logo_upload_id': '', 'logo_approved': False, 'brand_tagline': '', 'footer_text': '',
}

def extend(schemas, field):
    f = field
    schemas['settings']['fields'] += [f(k,label) for k,label in [('hero_eyebrow','Homepage small heading'),('research_title','Research capabilities section heading'),('interactions_title','Cell–material section heading'),('scaffolds_title','Scaffolds section heading'),('people_title','People section heading'),('alerts_title','Homepage alerts heading'),('contacts_title','Contact section heading')]]
    schemas['contacts'] = dict(label='Contact information', title='label', fields=[
        f('label', 'Contact label', required=True),
        f('researcher_id', 'Assign to researcher (blank = laboratory)', 'relation', relation='people'),
        f('kind', 'Contact type', 'select', options=['email','telephone','website','address','other'], required=True),
        f('value', 'Contact information', 'textarea', required=True),
        f('show_homepage', 'Show in homepage contact section', 'checkbox'),
        f('order', 'Display order', 'number'),
        f('internal_notes', 'Private notes', 'textarea', public=False)])
    targets = [key for key in schemas if key not in ('media', 'contacts')]
    schemas['fields'] = dict(label='Custom fields', title='label', fields=[
        f('label', 'Field label', required=True),
        f('target_collection', 'Record type', 'select', options=targets, required=True),
        f('target_id', 'Assign to record', 'target', required=True),
        f('kind', 'Field type', 'select', options=['text','multiline','email','url','number','date'], required=True),
        f('value', 'Field value', 'textarea', required=True), f('order', 'Display order', 'number'),
        f('internal_notes', 'Private notes', 'textarea', public=False)])
    schemas['theme'] = dict(label='Theme & appearance', title='title', fields=[
        f('title', 'Configuration name', required=True),
        *[f(k, label, 'color', required=True) for k,label in [
            ('primary','Primary / links'),('accent','Accent'),('background','Page background'),
            ('surface','Cards / header'),('text_color','Text'),('muted_color','Secondary text'),('border_color','Borders')]],
        f('heading_font','Heading font','select',options=['serif','sans','humanist'],required=True),
        f('body_font','Body font','select',options=['sans','serif','humanist'],required=True),
        f('font_size','Base font size (14–22 px)','number',required=True),
        f('content_width','Content width (960–1600 px)','number',required=True),
        f('corner_radius','Card corners (0–28 px)','number',required=True),
        f('density','Spacing','select',options=['comfortable','compact'],required=True),
        f('hero_layout','Homepage opening layout','select',options=['photo-right','photo-left','text-only'],required=True),
        f('home_blocks','Homepage sections — select and reorder','multi-choice',options=HOME_BLOCKS),
        f('hidden_navigation','Hide navigation links','multi-choice',options=NAV_ITEMS),
        f('logo_upload_id','Custom laboratory logo','image',public=False),
        f('logo_approved','Approve custom logo for public use','checkbox',public=False),
        f('brand_tagline','Header tagline'),f('footer_text','Footer text','textarea')])
    for collection, schema in schemas.items():
        if collection not in ('media','fields','contacts','theme') and not any(x['key']=='media_items' for x in schema['fields']):
            schema['fields'].append(f('media_items','Photos, videos & downloadable files','multi',relation='media',
                help='Upload here or select existing files. Files are private until you approve them in the media library.'))
        if collection not in ('media','theme','fields','contacts'):
            protected = {'id','visibility','name','title','group','photo_permission','document_public','hero_permission','homepage','navigation'}
            hideable = [x['key'] for x in schema['fields'] if x['public'] and not x['required'] and not x['relation']
                        and x['type'] not in ('image','document','asset','checkbox') and x['key'] not in protected]
            if collection == 'people' and 'photo_url' not in hideable: hideable.append('photo_url')
            schema['fields'].append(f('hidden_fields','Hide optional fields from the public website','multi-choice',
                options=hideable,public=False,help='Hiding preserves the saved value. Use Clear next to an optional field to remove its current value. Required identifiers and relationship fields remain protected.'))

def validate_extra(collection, record):
    if collection == 'theme':
        if record['id'] != 'website' or record['visibility'] != 'public':
            raise ValueError('The website uses one public theme record: website.')
        for key, low, high in [('font_size',14,22),('content_width',960,1600),('corner_radius',0,28)]:
            if not low <= record[key] <= high: raise ValueError(key.replace('_',' ')+' is out of range.')
    if collection == 'fields':
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,79}',record['target_id']): raise ValueError('Choose the record for this custom field.')
        kind, value = record['kind'],record['value']
        if kind=='number':
            if not re.fullmatch(r'-?\d+(?:\.\d+)?',value): raise ValueError('Enter a numeric custom-field value.')
        if kind=='date':
            try: date.fromisoformat(value)
            except ValueError: raise ValueError('Use YYYY-MM-DD for the custom date field.')
    if collection in ('fields','contacts'):
        kind, value = record['kind'],record['value']
        if kind == 'email' and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',value): raise ValueError('Enter a valid email address.')
        if kind in ('url','website'):
            from .schema import safe_url
            if not safe_url(value): raise ValueError('Use an absolute HTTP(S) address.')
