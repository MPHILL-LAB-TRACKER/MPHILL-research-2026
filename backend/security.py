"""Opaque, revocable server-side sessions; no tokens stored in JavaScript storage."""
from __future__ import annotations
import hashlib, secrets, time
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from fastapi import HTTPException, Request
HASHER=PasswordHasher(time_cost=3,memory_cost=65536,parallelism=4)
DUMMY=HASHER.hash(secrets.token_urlsafe(32))
COOKIE='ted2_session'
def digest(value): return hashlib.sha256(value.encode()).hexdigest()
def password_hash(password):
    if not isinstance(password,str) or not 12<=len(password)<=1024: raise ValueError('Use a password of 12–1024 characters.')
    return HASHER.hash(password)
def verify(encoded,password):
    if not isinstance(password,str) or len(password)>1024: return False
    try: return HASHER.verify(encoded,password)
    except (VerifyMismatchError,VerificationError,TypeError): return False

def user_for(request:Request,required=True):
    store=request.app.state.store; token=request.cookies.get(COOKIE,'')
    if not token or len(token)>256:
        if required: raise HTTPException(401,'Sign in to continue.')
        return None
    current=time.time()
    with store.connect(write=True) as c:
        r=c.execute('SELECT u.*,s.csrf,s.created,s.last_seen,s.expires FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=?',(digest(token),)).fetchone()
        if not r or not r['active'] or r['expires']<current or current-r['last_seen']>1800:
            c.execute('DELETE FROM sessions WHERE token_hash=?',(digest(token),))
            if required: raise HTTPException(401,'Your session expired. Please sign in again.')
            return None
        c.execute('UPDATE sessions SET last_seen=? WHERE token_hash=?',(current,digest(token)))
        return {k:r[k] for k in ['id','username','role','researcher_id','csrf']}

def same_origin(request:Request):
    if request.headers.get('origin','').rstrip('/') != request.app.state.origin:
        raise HTTPException(403,'This write must originate from the management website.')
    if request.headers.get('sec-fetch-site')=='cross-site': raise HTTPException(403,'Cross-site writes are not permitted.')

def write_user(request:Request):
    same_origin(request); u=user_for(request)
    if not secrets.compare_digest(request.headers.get('x-csrf-token',''),u['csrf']): raise HTTPException(403,'Security token missing or expired. Reload this page.')
    return u

def is_admin(u): return u['role'] in ('owner','admin')
def require_admin(u):
    if not is_admin(u): raise HTTPException(403,'This operation is restricted to administrators.')
def require_owner(u):
    if u['role']!='owner': raise HTTPException(403,'Only an owner can manage accounts.')

def assigned(store,u,collection,p):
    if is_admin(u): return True
    rid=u['researcher_id']
    if not rid: return False
    if collection=='people': return p['id']==rid
    if collection=='projects': return p.get('lead_id')==rid or rid in p.get('people',[])
    if collection=='manuscripts': return rid in p.get('people',[])
    if collection in ('milestones','updates'): return p.get('researcher_id')==rid
    return False
