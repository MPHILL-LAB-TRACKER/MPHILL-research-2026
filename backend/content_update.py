"""Conservative, repeatable V2/V3→V4 seed update for an existing installation.

Only fields still equal to a shipped V2 or V3 baseline are replaced. Owner edits,
accounts, assignments, private work and upload files are not overwritten.
"""
from __future__ import annotations
import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from .db import ROOT, now
from .schema import validate


def _records(path: Path) -> dict[tuple[str, str], dict]:
    source = json.loads(path.read_text(encoding='utf-8'))
    return {(collection, item['id']): validate(collection, item)
            for collection, items in source.items() for item in items}


def upgrade_content(store, *, apply=False):
    """Return a report; writes require apply=True and an existing initialized DB."""
    previous = _records(ROOT / 'data/updates/v2-baseline.json')
    baseline_v3 = _records(ROOT / 'data/updates/v3-baseline.json')
    proposed = _records(ROOT / 'data/seed.json')
    with store.connect() as connection:
        if connection.execute('SELECT COUNT(*) FROM records').fetchone()[0] == 0:
            raise ValueError('This database is empty. Initialize it with python manage.py init.')
    backup = None
    if apply:
        directory = store.path.parent / 'backups'
        directory.mkdir(exist_ok=True)
        os.chmod(directory, 0o700)
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        backup = directory / f'pre-content-v4-{stamp}-{uuid.uuid4().hex[:8]}.sqlite3'
        with store.connect() as source, sqlite3.connect(backup) as target:
            source.backup(target)
        os.chmod(backup, 0o600)
    report = {'applied': apply, 'backup': str(backup) if backup else None,
              'inserted': [], 'updated': [], 'preserved_owner_fields': []}
    with store.connect(write=apply) as connection:
        for (collection, rid), new in proposed.items():
            row = connection.execute('SELECT * FROM records WHERE collection=? AND id=?', (collection, rid)).fetchone()
            if row is None:
                report['inserted'].append(f'{collection}/{rid}')
                if apply:
                    connection.execute('INSERT INTO records VALUES(?,?,?,?,1,?,?)',
                        (collection, rid, json.dumps(new, ensure_ascii=False), new['visibility'], 'content-v4', now()))
                    store.audit(connection, 'server-operator', 'content-v4-create', collection, rid, after=new)
                continue
            old = baseline_v3.get((collection, rid)) or previous.get((collection, rid))
            old_v2 = previous.get((collection, rid), {})
            # A record created independently with a release ID is never replaced.
            if old is None:
                continue
            current = validate(collection, json.loads(row['payload']))
            merged = dict(current)
            changed = []
            for key, value in new.items():
                if key == 'id' or current.get(key) == value:
                    continue
                if current.get(key) == old.get(key) or (key in old_v2 and current.get(key) == old_v2.get(key)):
                    merged[key] = value
                    changed.append(key)
                else:
                    report['preserved_owner_fields'].append(f'{collection}/{rid}: {key}')
            if not changed:
                continue
            merged = validate(collection, merged)
            report['updated'].append({'record': f'{collection}/{rid}', 'fields': changed})
            if apply:
                connection.execute('UPDATE records SET payload=?,visibility=?,version=version+1,updated_at=? WHERE collection=? AND id=?',
                    (json.dumps(merged, ensure_ascii=False), merged['visibility'], now(), collection, rid))
                store.audit(connection, 'server-operator', 'content-v4-update', collection, rid, before=current, after=merged)
    return report
