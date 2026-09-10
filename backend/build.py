"""Build the public single-file site. No private model is accepted or serialized here."""
from __future__ import annotations
import base64,json
from .db import ROOT
from .public import project_public

def js_json(value):
    return json.dumps(value,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
def image_data(name):
    return 'data:image/png;base64,'+base64.b64encode((ROOT/'web/images'/name).read_bytes()).decode()
def compile_public(data,*,live=False,api_base=''):
    wordmark=image_data('ted2-wordmark.png');unam=image_data('unam-logo.png')
    text=(ROOT/'web/public.html').read_text()
    text=text.replace('/*PUBLIC_CSS*/',(ROOT/'web/assets/public.css').read_text())
    text=text.replace('__WORDMARK__',wordmark).replace('__UNAM__',unam)
    config={'live':live,'apiBase':api_base}
    script='window.TED2_CONFIG='+js_json(config)+';window.TED2_DATA='+js_json(data)+';window.TED2_WORDMARK='+js_json(wordmark)+';'
    text=text.replace('/*PUBLIC_DATA*/',script).replace('/*PUBLIC_JS*/',(ROOT/'web/assets/public.js').read_text())
    return text

def build_seed(destination=None):
    seed=json.loads((ROOT/'data/seed.json').read_text())
    data=project_public(seed)
    html=compile_public(data)
    destination=destination or ROOT/'index.html'
    destination.write_text(html,encoding='utf-8')
    return destination
