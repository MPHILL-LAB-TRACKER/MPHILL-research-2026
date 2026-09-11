"""Allowlisted owner-supplied assets, never served as an unrestricted directory.

Portrait mappings follow the adjacent names in Team.pptx (slides 2–4).
Only a public, explicitly approved record can include its bundled bytes in a
public response. File names and MIME types cannot be supplied by API callers.
"""
from __future__ import annotations
import base64
from functools import lru_cache
from pathlib import Path

ASSET_ROOT = Path(__file__).resolve().parents[1] / 'data' / 'assets'
PORTRAITS = {
    key: f'portraits/{key}.jpg' for key in (
        'albertina-shatri', 'davis-mumbengegwi', 'silas-bere', 'charity-maepa',
        'maneria-halweendo', 'denise-bouman', 'nonku-phili', 'naungwe-simasiku',
        'vevangapi-mbatara', 'paulus-hamutenya', 'jaydine-jeris'
    )
}
CERTIFICATES = {
    'falling-walls-paulus-hamutenya-2026': {
        'pdf': 'certificates/falling-walls-paulus-hamutenya-2026.pdf',
        'preview': 'certificates/falling-walls-paulus-hamutenya-2026.jpg'
    }
}

@lru_cache(maxsize=32)
def _encoded(relative: str, mime: str) -> str:
    return f'data:{mime};base64,' + base64.b64encode((ASSET_ROOT / relative).read_bytes()).decode('ascii')

def portrait_data(key: str) -> str:
    return _encoded(PORTRAITS[key], 'image/jpeg') if key in PORTRAITS else ''

def certificate_data(key: str) -> dict[str, str]:
    if key not in CERTIFICATES:
        return {}
    paths = CERTIFICATES[key]
    return {
        'document_url': _encoded(paths['pdf'], 'application/pdf'),
        'certificate_preview': _encoded(paths['preview'], 'image/jpeg'),
        'certificate_filename': Path(paths['pdf']).name,
    }

PORTRAITS.update({'naungwe-simasiku-v4':'portraits/naungwe-simasiku-v4.jpg','nailoke-pauline-kadhila-v4':'portraits/nailoke-pauline-kadhila-v4.jpg'})
HOMEPAGE={'laboratory-v4':'homepage/laboratory-v4.jpg'}
def homepage_data(key):
    return _encoded(HOMEPAGE[key], 'image/jpeg') if key in HOMEPAGE else ''
