/* Management client. Server authorization is authoritative for every operation. */
'use strict';
(() => {
    const E = v => String(v ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
    const app = document.getElementById('app');
    let state = null, user = null, dirty = false, lastHash = '', working = false;
    const admin = () => user && ['owner', 'admin'].includes(user.role);
    const rows = c => state?.records[c] || [];
    const titleOf = (c, p) => p[state.schemas[c].title] || p.id;
    const nice = v => String(v || '').replace(/-/g, ' ').replace(/^\w/, c => c.toUpperCase());
    const tag = (v, cls = '') => `<span class="tag ${E(cls || v)}">${E(nice(v))}</span>`;
    const link = (hash, t, cls = '') => `<a class="${E(cls)}" href="#/${E(hash)}">${E(t)}</a>`;
    const choose = (c, id) => state?.choices[c]?.find(x => x.id === id)?.name || id || 'Not assigned';
    const empty = (a, b) => `<div class="empty"><h3>${E(a)}</h3>${E(b)}</div>`;
    function notify(msg) { const n = document.getElementById('notification'); n.textContent = msg; n.hidden = false; setTimeout(() => n.hidden = true, 4500); }
    function showError(msg) { const n = document.getElementById('form-error') || document.getElementById('page-error'); if (n) {
        n.textContent = msg;
        if (msg.includes('Sign in again')) {
            const a = document.createElement('a');
            a.href = '/login';
            a.target = '_blank';
            a.rel = 'noopener';
            a.textContent = ' Open sign-in in a new tab';
            n.appendChild(a);
        }
        n.hidden = false;
        n.scrollIntoView({ block: 'nearest' });
    }
    else
        notify(msg); }
    async function api(path, options = {}) {
        if (options.method && options.method !== 'GET' && path !== '/login') {
            const check = await fetch('/api/session', { credentials: 'same-origin', cache: 'no-store' });
            const session = await check.json();
            if (!session.user)
                throw new Error('Sign in again in a new tab, then return here and save. Unsaved form contents have been preserved.');
            if (user && session.user.id !== user.id)
                throw new Error('The signed-in account changed. Copy unsaved text to a private location and reopen the form using the intended account.');
            user = session.user;
        }
        const headers = new Headers(options.headers || {});
        if (options.body && !(options.body instanceof FormData))
            headers.set('Content-Type', 'application/json');
        if (options.method && options.method !== 'GET')
            headers.set('X-CSRF-Token', user?.csrf || '');
        const response = await fetch('/api' + path, { ...options, headers, credentials: 'same-origin', cache: 'no-store' });
        const data = await response.json().catch(() => ({ detail: 'Unexpected response from the server.' }));
        if (!response.ok) {
            if (response.status === 401 && !path.includes('login') && !dirty) {
                location.href = '/login';
            }
            throw new Error(typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail));
        }
        return data;
    }
    async function refresh() { state = await api('/bootstrap'); user = state.user; }
    function loginScreen() {
        document.title = 'Sign in | TED²';
        app.innerHTML = `<main class="login-layout" id="content"><section class="login-story"><a class="login-brand" href="/"><img src="/images/ted2-wordmark.png" alt="TED² Laboratory"></a><p class="eyebrow">Research workspace</p><h1>One laboratory.<br>Every next step.</h1><p>A dedicated place to manage research, share verified work and keep projects moving.</p><div class="principles"><span>Private drafts</span><span>Approved publishing</span><span>Researcher-led progress</span></div></section><section class="login-panel"><div class="login-card"><p class="eyebrow">Welcome back</p><h2>Sign in to your workspace.</h2><p>Accounts are issued by the laboratory owner. There is no public registration.</p><form id="login-form"><label class="field"><span>Username</span><input name="username" autocomplete="username" required maxlength="60" autofocus></label><label class="field"><span>Password</span><input name="password" type="password" autocomplete="current-password" required maxlength="1024"></label><div id="form-error" class="error" role="alert" hidden></div><button class="button" type="submit">Sign in →</button></form><p class="login-footer"><a href="/">Back to the public laboratory website</a><br>Forgotten password? Ask the owner to reset your account.</p></div></section></main>`;
        document.getElementById('login-form').addEventListener('submit', async (e) => { e.preventDefault(); const b = e.target.querySelector('button'); b.disabled = true; try {
            const result = await api('/login', { method: 'POST', body: JSON.stringify(Object.fromEntries(new FormData(e.target))) });
            location.href = result.next;
        }
        catch (err) {
            showError(err.message);
            b.disabled = false;
        } });
    }
    function shell() {
        const personal = !admin();
        const sections = personal ? [
            ['My workspace', [['dashboard', 'Overview'], ['progress', 'My research progress'], ['records/projects', 'Assigned projects'], ['records/manuscripts', 'My manuscripts'], ['records/milestones', 'My milestones'], ['records/updates', 'My updates'], ['records/people', 'My profile']]],
            ['Account', [['password', 'Change password']]]
        ] : [
            ['Website studio', [['studio', 'Website studio'], ['media', 'Photos & videos'], ['records/sections', 'Pages & sections'], ['edit/theme/website', 'Theme & colours'], ['records/contacts', 'Contact information'], ['records/fields', 'Custom fields'], ['trash', 'Trash & restore'], ['publish', 'Publish to GitHub']]],
            ['Research management', [['dashboard', 'Overview'], ['progress', 'Researcher progress'], ['records/projects', 'Active research'], ['board', 'Manuscript pipeline'], ['records/milestones', 'Milestones & progress'], ['records/updates', 'Research updates']]],
            ['Website content', [['records/announcements', 'Homepage alerts & events'], ['records/achievements', 'Achievements & certificates'], ['records/people', 'Researchers & collaborators'], ['records/publications', 'Publications'], ['records/collaborations', 'Collaborations'], ['records/funders', 'Funders'], ['records/capabilities', 'Homepage research'], ['records/settings', 'Website settings'], ['records/sources', 'Sources & credits']]],
            ['Publishing & access', [['export', 'Publish & export'], ['audit', 'Activity log'], ...(user.role === 'owner' ? [['users', 'Accounts & permissions']] : []), ['password', 'Change password']]]
        ];
        app.innerHTML = `<div class="app-shell"><aside class="sidebar" id="sidebar"><a class="sidebar-brand" href="#/dashboard"><img src="/images/ted2-wordmark.png" alt="TED² Laboratory"></a><div class="sidebar-sub">${personal ? 'Researcher workspace' : 'Laboratory management'}</div><label class="sidebar-search"><span>Find an editor</span><input type="search" id="sidebar-search" placeholder="Search navigation…"></label>${sections.map(([label, links]) => `<p class="nav-section">${E(label)}</p><nav aria-label="${E(label)}">${links.map(([h, t]) => link(h, t)).join('')}</nav>`).join('')}<div class="sidebar-footer"><p>${personal ? 'Your assigned work only.' : 'Public content and private research are kept separate.'}</p><p><a href="/" target="_blank" rel="noopener">Visit public website ↗</a></p></div></aside><div class="workspace-body"><header class="topbar"><button id="mobile-menu" class="button secondary mobile-toggle" aria-expanded="false" aria-controls="sidebar">Menu</button><span class="topbar-title">TED² · ${personal ? 'Researcher workspace' : 'Administration · V5'}</span><div class="topbar-right"><a href="/" target="_blank" class="public-link" rel="noopener">View public site ↗</a><span class="user-pill">${E(user.username)} · ${E(user.role)}</span><button class="text-button" id="logout">Sign out</button></div></header><main id="content" class="content" tabindex="-1"></main></div></div>`;
        document.getElementById('sidebar-search').addEventListener('input',e=>{const query=e.target.value.toLowerCase();document.querySelectorAll('.sidebar nav a').forEach(a=>a.hidden=!a.textContent.toLowerCase().includes(query));});
        document.getElementById('mobile-menu').addEventListener('click', () => { const v = document.getElementById('sidebar').classList.toggle('open'); document.getElementById('mobile-menu').setAttribute('aria-expanded', String(v)); });
        document.getElementById('logout').addEventListener('click', async () => { if (dirty && !confirm('Discard unsaved changes and sign out?'))
            return; try {
            await api('/logout', { method: 'POST' });
            dirty = false;
            location.href = '/login';
        }
        catch (e) {
            showError(e.message);
        } });
    }
    const heading = (eye, title, desc = '', actions = '') => `<div class="page-title"><div><p class="eyebrow">${E(eye)}</p><h1>${E(title)}</h1>${desc ? `<p>${E(desc)}</p>` : ''}</div>${actions ? `<div class="title-actions">${actions}</div>` : ''}</div><div id="page-error" class="error" role="alert" hidden></div>`;
    function weighted(p, person = '') { const ms = rows('milestones').filter(m => m.project_id === p.id && (!person || m.researcher_id === person)); const total = ms.reduce((s, m) => s + (m.weight || 1), 0), done = ms.filter(m => m.status === 'done').reduce((s, m) => s + (m.weight || 1), 0); return { value: total ? Math.round(done / total * 100) : null, done: ms.filter(m => m.status === 'done').length, total: ms.length, blocked: ms.filter(m => m.status === 'blocked').length }; }
    function progressCard(p, person = '') { const w = weighted(p, person); return `<article class="progress-card"><div class="progress-meta"><span>${E(nice(p.stage))}</span>${tag(p.visibility)}</div><h3>${link('edit/projects/' + p.id, p.title)}</h3>${w.value !== null ? `<progress value="${w.value}" max="100" aria-label="Internal weighted progress"></progress>` : ''}<div class="progress-meta"><span>${w.value === null ? 'No milestones yet' : w.value + '% · internal weighted progress'}</span><span>${w.done}/${w.total} done${w.blocked ? ' · ' + w.blocked + ' blocked' : ''}</span></div>${p.due_date ? `<p class="help">Target completion: ${E(p.due_date)}</p>` : ''}</article>`; }
    function dashboard() {
        const c = document.getElementById('content'), pub = Object.values(state.records).flat().filter(x => x.visibility === 'public').length, pri = Object.values(state.records).flat().filter(x => x.visibility === 'private').length;
        const due = rows('milestones').filter(m => m.status !== 'done' && m.due_date).sort((a, b) => a.due_date.localeCompare(b.due_date)).slice(0, 6);
        c.innerHTML = heading(admin() ? 'Laboratory overview' : 'Your workspace', admin() ? 'Research, with a clear next step.' : 'Your work. Your next milestone.', admin() ? 'Manage people and publications, approve public updates and follow the work happening across the laboratory.' : 'Track your assigned projects, keep manuscript stages current and submit private updates for administrator review.', link('new/updates', 'Add a research update', 'button')) +
            `<div class="metrics"><div class="metric"><span>Research projects</span><strong>${rows('projects').length}</strong><small>${admin() ? 'Across the laboratory' : 'Assigned to you'}</small></div><div class="metric"><span>Manuscripts</span><strong>${rows('manuscripts').length}</strong><small>Preparation through publication</small></div><div class="metric"><span>Open milestones</span><strong>${rows('milestones').filter(m => m.status !== 'done').length}</strong><small>Tasks still in progress</small></div><div class="metric"><span>${admin() ? 'Private records' : 'Completed milestones'}</span><strong>${admin() ? pri : rows('milestones').filter(m => m.status === 'done').length}</strong><small>${admin() ? pub + ' approved public records' : 'Your recorded progress'}</small></div></div>
    <div class="notice">${admin() ? 'New research records start private. An administrator must deliberately publish them. Internal notes, submission references, draft PDFs and funding amounts are never included in the public feed.' : 'Your account can edit assigned private manuscripts, milestones and updates. Only an administrator can publish content or change researcher assignments. To request a biography change, add a private update with type “Bio change”.'}</div>
    <div class="panel-grid"><section class="panel"><div class="panel-heading"><div><h2>Research progress</h2><p>Weighted milestones · private workspace measure</p></div>${link('progress', 'View all', 'text-button')}</div><div class="progress-list">${rows('projects').length ? rows('projects').slice(0, 5).map(p => progressCard(p, admin() ? '' : user.researcher_id)).join('') : empty('Start with a research project.', admin() ? 'Create a project, select its lead and team, then assign milestones.' : 'The laboratory administrator has not assigned a project to your account yet.')}</div>${admin() ? `<div class="inline-links">${link('new/projects', 'Create research project →')}${link('new/milestones', 'Add milestone →')}</div>` : ''}</section><section class="panel"><div class="panel-heading"><div><h2>Upcoming milestones</h2><p>Nearest recorded target dates</p></div></div>${due.length ? `<table><tbody>${due.map(m => `<tr><td>${link('edit/milestones/' + m.id, m.title)}<span class="help">${E(choose('people', m.researcher_id))}</span></td><td>${E(m.due_date)}<br>${tag(m.status)}</td></tr>`).join('')}</tbody></table>` : empty('No dated milestones yet.', 'Add a milestone with a target date to bring the next action into view.')}</section></div>`;
    }
    function records(collection) {
        const s = state.schemas[collection];
        if (!s)
            return;
        const allowed = admin() || ['manuscripts', 'milestones', 'updates'].includes(collection);
        document.getElementById('content').innerHTML = heading('Content & activity', s.label, admin() ? 'Search records, edit details and choose what is visible publicly.' : 'Only records assigned to your account are shown. Published records require an administrator to change.', allowed && !['settings','theme'].includes(collection) ? link('new/' + collection, 'Add ' + (collection === 'people' ? 'profile' : 'record'), 'button') : '') + `<section class="panel"><div class="toolbar"><label class="grow field"><span>Search records</span><input id="record-search" type="search"></label><label class="field"><span>Visibility</span><select id="visibility-filter"><option value="">All records</option><option value="private">Private / pending approval</option><option value="public">Public</option></select></label></div><div id="record-list"></div></section>`;
        const update = () => { const q = document.getElementById('record-search').value.toLowerCase(), v = document.getElementById('visibility-filter').value; const list = rows(collection).filter(p => (!v || v === p.visibility) && [titleOf(collection, p), p.stage, p.role, p.summary, p.status, p.kind].join(' ').toLowerCase().includes(q)); document.getElementById('record-list').innerHTML = list.length ? `<div class="table-scroll"><table><thead><tr><th>Record</th><th>Visibility</th><th>Updated</th><th>Action</th></tr></thead><tbody>${list.map(p => `<tr><td>${link('edit/' + collection + '/' + p.id, titleOf(collection, p))}<span class="help">${E(nice(p.stage || p.status || p.group || p.type || p.kind || ''))}</span></td><td>${tag(p.visibility)}</td><td>${E((p._updated_at || '').slice(0, 10))}</td><td class="record-action">${link('edit/' + collection + '/' + p.id, admin() || (['manuscripts', 'milestones', 'updates'].includes(collection) && p.visibility === 'private') ? 'Edit record →' : 'View record →')}${admin()&&!['settings','theme'].includes(collection)?` <button class="text-button danger-text" data-trash-record="${E(collection+'/'+p.id)}">Delete</button>`:''}</td></tr>`).join('')}</tbody></table></div>` : empty('No matching records.', q || v ? 'Change the search or visibility filter.' : 'Create the first record when its details are ready.'); };
        document.getElementById('record-search').addEventListener('input', update);
        document.getElementById('visibility-filter').addEventListener('change', update);
        update();
    }
    function defaultRecord(collection) {
        const out = { id: '', visibility: 'private' };
        for (const f of state.schemas[collection].fields) {
            out[f.key] = ['multi', 'lines', 'urls','multi-choice'].includes(f.type) ? [] : f.type === 'checkbox' ? false : ['number', 'year', 'weight', 'percent', 'money'].includes(f.type) ? null : f.type === 'select' ? f.options[0] || '' : '';
        }
        if (collection === 'people') out.bundled_portrait = '';
        if (collection === 'achievements') out.certificate_key = '';
        if (collection === 'announcements') out.date_status = 'lab-supplied';
        if (collection === 'milestones')
            out.weight = 1;
        if (collection === 'updates')
            out.date = new Date().toISOString().slice(0, 10);
        if (!admin()) {
            if ('researcher_id' in out)
                out.researcher_id = user.researcher_id;
            if ('people' in out)
                out.people = [user.researcher_id];
        }
        return out;
    }
    function fieldHTML(f, p, readOnly, isNew) {
        const v = p[f.key], id = 'f-' + f.key;
        const locked = readOnly || (!admin() && ['people', 'researcher_id'].includes(f.key));
        const dis = locked ? ' disabled' : '';
        const req = f.required && !locked ? ' required' : '';
        const full = ['textarea', 'lines', 'urls', 'image', 'document', 'asset','multi','multi-choice'].includes(f.type);
        const label = E(f.label) + (f.public ? '' : ` <small class="private-label">${['certificate_key','bundled_portrait'].includes(f.key) ? 'Managed asset choice' : 'Private field'}</small>`);
        let control;
        if (['textarea', 'lines', 'urls'].includes(f.type))
            control = `<textarea id="${id}" name="${E(f.key)}"${dis}${req}>${E(Array.isArray(v) ? v.join('\n') : v)}</textarea>`;
        else if(f.type==='target')control=`<select id="${id}" name="${E(f.key)}"${dis}${req}><option value="">Select a record…</option></select>`;
        else if(f.type==='multi-choice'){const values=[...(Array.isArray(v)?v:[]),...f.options.filter(x=>!(v||[]).includes(x))];control=`<input type="hidden" name="${E(f.key)}" value=""><div class="choice-list" data-choice-group="${E(f.key)}">${values.map(x=>`<div class="choice-row"><label><input type="checkbox" value="${E(x)}"${(v||[]).includes(x)?' checked':''}${dis}> ${E(nice(x.replace(/_/g,' ')))}</label>${f.key==='home_blocks'?`<button type="button" class="text-button" data-choice-up aria-label="Move ${E(x)} up">↑</button><button type="button" class="text-button" data-choice-down aria-label="Move ${E(x)} down">↓</button>`:''}</div>`).join('')}</div>`;}
        else if (['select', 'relation', 'multi'].includes(f.type)) {
            const options = f.type === 'select' ? f.options.map(x => ({ id: x, name: nice(x) })) : (state.choices[f.relation] || []);
            control = `<select id="${id}" name="${E(f.key)}"${f.type === 'multi' ? ' multiple hidden' : ''}${dis}${req}>${f.type !== 'multi' ? '<option value="">Select…</option>' : ''}${options.map(x => `<option value="${E(x.id)}"${(Array.isArray(v) ? v.includes(x.id) : v === x.id) ? ' selected' : ''}>${E(x.name)}</option>`).join('')}</select>${f.type === 'multi' ? `<div class="multi-checks">${options.map(x=>`<label><input type="checkbox" data-multi-key="${E(f.key)}" value="${E(x.id)}"${(v||[]).includes(x.id)?' checked':''}${dis}> ${E(x.name)}</label>`).join('')||'<span class="help">No records available yet.</span>'}</div>` : ''}`;
        }
        else if (f.type === 'checkbox')
            control = `<input type="checkbox" id="${id}" name="${E(f.key)}"${v ? ' checked' : ''}${dis}>`;
        else if (['image', 'document', 'asset'].includes(f.type))
            control = `<div class="upload-box"><input type="hidden" id="${id}" name="${E(f.key)}" value="${E(v || '')}"><div id="preview-${E(f.key)}">${v ? `${f.type === 'image' ? `<img class="upload-preview" src="/media/${E(v)}" alt="Current portrait">` : ''}<a href="/media/${E(v)}" target="_blank" rel="noopener">Open current ${f.type === 'image' ? 'photograph' : f.type === 'asset' ? 'media' : 'PDF'} ↗</a>` : '<span class="help">No file attached.</span>'}</div>${!readOnly ? `${isNew ? '<p class="help">Save this record first, then upload its file.</p>' : `<input type="file" data-file="${E(f.key)}" accept="${f.type === 'image' ? '.jpg,.jpeg,.png,.webp,.gif,.bmp,.tif,.tiff' : f.type === 'asset' ? '.jpg,.jpeg,.png,.webp,.gif,.bmp,.tif,.tiff,.mp4,.webm,.mov,.m4v,.pdf' : 'application/pdf'}" aria-label="Choose ${f.type === 'image' ? 'photograph' : f.type === 'asset' ? 'media' : 'PDF'}"><button type="button" class="button secondary" data-upload="${E(f.key)}">Upload ${f.type === 'image' ? 'photograph' : f.type === 'asset' ? 'media' : 'PDF'}</button>${v ? `<button type="button" class="text-button" data-remove-file="${E(f.key)}">Detach file</button>` : ''}`}` : ''}<span class="help">${f.type === 'image' ? 'JPEG/JPG, PNG, WebP, GIF, BMP or TIFF up to 20 MB. GIF/TIFF: first frame/page. Approve publication in this record before sharing.' : f.type === 'asset' ? 'Images up to 20 MB; MP4/WebM/MOV videos up to 80 MB; PDF up to 20 MB. Choose the matching media type and explicitly approve public sharing.' : 'This dedicated PDF slot accepts PDFs up to 20 MB. Use Photos, videos & files below for images or videos. Manuscripts and research-update PDF attachments remain private. Publication and certificate PDFs require explicit approval. PDFs are not antivirus-scanned.'}</span></div>`;
        else {
            const type = ['number', 'year', 'weight', 'percent', 'money'].includes(f.type) ? 'number' : f.type === 'url' ? 'url' : f.type === 'date' ? 'date' : f.type === 'email' ? 'email' : f.type === 'color' ? 'color' : 'text';
            control = `<input id="${id}" name="${E(f.key)}" type="${type}" value="${E(v ?? '')}"${dis}${req}${type === 'number' ? ` step="${f.type === 'money' ? '0.01' : '1'}"` : ''}>`;
        }
        if (f.type === 'checkbox')
            return `<label class="field checkbox full">${control}<span>${label}${f.help ? `<small class="help">${E(f.help)}</small>` : ''}</span></label>`;
        return `<div class="field ${full ? 'full' : ''} ${f.required ? 'required' : ''}"><label for="${id}"><span>${label}</span></label>${control}${!locked&&!f.required&&!['image','document','asset','multi','multi-choice','target'].includes(f.type)?`<button type="button" class="clear-field" data-clear-field="${E(f.key)}">Clear value</button>`:''}${f.help ? `<span class="help">${E(f.help)}</span>` : ''}</div>`;
    }
    async function edit(collection, rid) {
        const s = state.schemas[collection];
        if (!s)
            return;
        const isNew = !rid;
        let p = isNew ? defaultRecord(collection) : await api('/records/' + collection + '/' + encodeURIComponent(rid));
        if(isNew){const query=new URLSearchParams(location.hash.split('?')[1]||'');for(const key of ['researcher_id','target_collection','target_id'])if(query.has(key)&&key in p)p[key]=query.get(key);}
        const readOnly = !admin() && (!['manuscripts', 'milestones', 'updates'].includes(collection) || p.visibility === 'public');
        const c = document.getElementById('content');
        c.innerHTML = heading(isNew ? 'Create record' : readOnly ? 'Assigned record' : 'Edit record', isNew ? 'New ' + (collection === 'people' ? 'profile' : s.label.toLowerCase()) : titleOf(collection, p), readOnly ? 'This record is read-only for your account. Submit a private update to request a change.' : 'Changes are saved to the server. Private records remain off the public website.', link('records/' + collection, 'Back to records', 'button secondary')) +
            `<section class="panel"><form id="record-form"><div class="grid-two"><div class="field required"><label for="record-id"><span>Permanent record ID</span></label><input id="record-id" name="id" value="${E(p.id)}" pattern="[a-z0-9][a-z0-9-]{0,79}" maxlength="80" required${!isNew ? ' disabled' : ''}><span class="help">${isNew ? 'A short URL-safe name is generated from the title. You may edit it before saving.' : 'Kept stable so links and assignments continue to work.'}</span></div><div class="field"><label for="record-visibility"><span>Public visibility</span></label><select id="record-visibility" name="visibility"${!admin() || readOnly ? ' disabled' : ''}><option value="private"${p.visibility === 'private' ? ' selected' : ''}>Private — workspace only</option><option value="public"${p.visibility === 'public' ? ' selected' : ''}>Public — visible on the website</option></select><span class="help">${admin() ? 'Publishing exposes only the approved public fields. Internal notes and private PDFs are excluded.' : 'Only an administrator can approve public publication.'}</span></div>${s.fields.filter(f=>!f.key.startsWith('private_')).map(f => fieldHTML(f, p, readOnly, isNew)).join('')}${s.fields.some(f=>f.key.startsWith('private_')) ? '<div class="private-section full"><h2>Private contact information</h2><p>Visible only within the authorized workspace. Never exported to the public website.</p></div>'+s.fields.filter(f=>f.key.startsWith('private_')).map(f=>fieldHTML(f,p,readOnly,isNew)).join('') : ''}</div><div id="form-error" class="error" role="alert" hidden></div>${readOnly ? '' : `<div class="form-actions"><button class="button" type="submit">${isNew ? 'Create record' : 'Save changes'}</button>${link('records/' + collection, 'Cancel', 'button secondary')}${admin()?link('publish','Review publishing →','text-button'):''}<span class="save-hint">${isNew ? 'Not saved yet' : 'Record version ' + p._version + ' · ' + (p._updated_at || '').slice(0, 16).replace('T', ' ')}</span></div>`}</form></section>${admin() && !isNew ? `<section class="panel"><div class="panel-heading"><h2>Revision history</h2><button class="button secondary" id="load-history">View saved revisions</button></div><div id="history-content"><p class="muted">Earlier saved values are retained in the private audit history.</p></div></section>` : ''}`;
        if(collection==='media' && !isNew)c.insertAdjacentHTML('afterbegin','<section class="panel media-editor-preview">'+previewMedia(p)+'</section>');
        setupV5Editor(collection,p,isNew,readOnly);
        const form = document.getElementById('record-form');
        let idTouched = false;
        if (isNew) {
            document.getElementById('record-id').addEventListener('input', () => idTouched = true);
            const titleInput = form.elements[s.title];
            if (titleInput)
                titleInput.addEventListener('input', () => { if (!idTouched)
                    document.getElementById('record-id').value = titleInput.value.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 80); });
        }
        form.addEventListener('input', () => dirty = true);
        form.addEventListener('change', () => dirty = true);
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (readOnly || working)
                return;
            const out = { id: form.elements.id.value, visibility: form.elements.visibility.value };
            for (const f of s.fields) {
                const input = form.elements[f.key];
                if (!input)
                    continue;
                out[f.key] = valueFrom(form,f);
            }
            if (!isNew)
                out._version = p._version;
            const becamePublic = out.visibility === 'public' && (isNew || p.visibility !== 'public');
            if (becamePublic && !confirm('Publish the public fields of this record on the laboratory website? Internal notes and private files will remain private.'))
                return;
            working = true;
            const button = form.querySelector('[type=submit]');
            button.disabled = true;
            try {
                const saved = await api('/records/' + collection + (isNew ? '' : '/' + encodeURIComponent(rid)), { method: isNew ? 'POST' : 'PUT', body: JSON.stringify(out) });
                dirty = false;
                await refresh();
                notify(saved.visibility === 'public' ? 'Saved locally. Use Publish to GitHub to update the online website.' : 'Private record saved.');
                if (isNew)
                    location.hash = '/edit/' + collection + '/' + saved.id;
                else
                    await edit(collection, rid);
            }
            catch (err) {
                showError(err.message);
            }
            finally {
                working = false;
                if (button.isConnected)
                    button.disabled = false;
            }
        });
        form.querySelectorAll('[data-upload]').forEach(b => b.addEventListener('click', async () => { const key = b.dataset.upload, file = form.querySelector(`[data-file="${key}"]`).files[0]; if (!file) {
            showError('Choose a file first.');
            return;
        } const fd = new FormData(); fd.append('file', file); b.disabled = true; try {
            const result = await api('/uploads/' + collection + '/' + rid, { method: 'POST', body: fd });
            form.elements[key].value = result.id;
            document.getElementById('preview-' + key).innerHTML = (result.mime.startsWith('image/') ? `<img class="upload-preview" src="${E(result.url)}" alt="Uploaded portrait">` : '') + `<a href="${E(result.url)}" target="_blank" rel="noopener">${E(result.name)} ↗</a>`;
            dirty = true;
            notify('File uploaded. Save the record to attach it.');
        }
        catch (err) {
            showError(err.message);
        }
        finally {
            b.disabled = false;
        } }));
        form.querySelectorAll('.upload-box').forEach(box=>{const input=box.querySelector('input[type=file]'),button=box.querySelector('[data-upload]');if(!input||!button)return;box.classList.add('drop-zone-compact');box.insertAdjacentHTML('afterbegin','<p class="help">Drop a file here, or browse below.</p>');box.addEventListener('dragover',e=>{e.preventDefault();box.classList.add('dragging');});box.addEventListener('dragleave',()=>box.classList.remove('dragging'));box.addEventListener('drop',e=>{e.preventDefault();box.classList.remove('dragging');if(e.dataTransfer.files.length!==1){showError('Drop one file at a time.');return;}input.files=e.dataTransfer.files;button.click();});});
        form.querySelectorAll('[data-remove-file]').forEach(b => b.addEventListener('click', () => { form.elements[b.dataset.removeFile].value = ''; document.getElementById('preview-' + b.dataset.removeFile).textContent = 'File detached from this unsaved form. Save changes to apply.'; dirty = true; }));
        document.getElementById('load-history')?.addEventListener('click', async () => { try {
            const history = await api('/history/' + collection + '/' + rid);
            document.getElementById('history-content').innerHTML = history.length ? history.map(h => `<details><summary>${E(h.created_at)} · ${E(h.actor)} · ${E(h.action)}</summary><pre class="audit-history">${E(JSON.stringify(JSON.parse(h.after_json || 'null'), null, 2))}</pre></details>`).join('') : 'No saved revision events yet. Seed records begin their audit history on the first edit.';
        }
        catch (e) {
            showError(e.message);
        } });
    }
    function board() { document.getElementById('content').innerHTML = heading('Publication progress', 'The manuscript pipeline.', 'Track private manuscript stages and approve selected public statuses without exposing review notes.', link('new/manuscripts', 'Add manuscript', 'button')) + `<div class="board">${[['Preparation', ['idea', 'drafting', 'internal-review']], ['Submission & review', ['submitted', 'under-review']], ['Revisions', ['revisions']], ['Accepted / published', ['accepted', 'published']]].map(([name, stages]) => { const ps = rows('manuscripts').filter(p => stages.includes(p.stage)); return `<section class="board-column"><h2>${E(name)} · ${ps.length}</h2>${ps.length ? ps.map(p => `<a class="board-card" href="#/edit/manuscripts/${E(p.id)}">${tag(p.stage)}${tag(p.visibility)}<h3>${E(p.title)}</h3><p>${E((p.people || []).map(id => choose('people', id)).join(', '))}</p>${p.due_date ? `<p>Next deadline: ${E(p.due_date)}</p>` : ''}</a>`).join('') : empty('Nothing here yet.', 'Add a manuscript or update its stage.')}</section>`; }).join('')}</div>`; }
    function progress() {
        const personal = !admin();
        document.getElementById('content').innerHTML = heading('Research progress', personal ? 'Your research progress.' : 'A workspace for every researcher.', 'Internal progress is the weight of completed milestones divided by the weight of all assigned milestones. It does not change the public progress percentage automatically.') +
            `${admin() ? `<section class="panel"><label class="field"><span>Researcher</span><select id="progress-person"><option value="">All researchers</option>${state.choices.people.map(p => `<option value="${E(p.id)}">${E(p.name)}</option>`).join('')}</select></label></section>` : ''}<div id="progress-results"></div>`;
        const update = () => { const id = personal ? user.researcher_id : document.getElementById('progress-person').value; const projects = rows('projects').filter(p => !id || p.lead_id === id || (p.people || []).includes(id)); const manuscripts = rows('manuscripts').filter(p => !id || (p.people || []).includes(id)); const updates = rows('updates').filter(p => !id || p.researcher_id === id).sort((a, b) => (b.date || '').localeCompare(a.date || '')); document.getElementById('progress-results').innerHTML = `<div class="panel-grid"><section class="panel"><div class="panel-heading"><h2>Assigned research</h2></div><div class="progress-list">${projects.length ? projects.map(p => progressCard(p, id)).join('') : empty('No projects assigned.', 'Project leads and team members are assigned by an administrator.')}</div></section><section class="panel"><div class="panel-heading"><h2>Manuscripts</h2></div>${manuscripts.length ? manuscripts.map(p => `<article class="progress-card"><h3>${link('edit/manuscripts/' + p.id, p.title)}</h3>${tag(p.stage)} ${tag(p.visibility)}</article>`).join('') : empty('No manuscript records yet.', 'Create private drafts and track their progression.')}</section></div><section class="panel"><div class="panel-heading"><h2>Research activity</h2>${link('new/updates', 'Add update', 'button secondary')}</div>${updates.length ? updates.map(p => `<article class="progress-card"><div class="progress-meta"><span>${E(p.date)} · ${E(choose('people', p.researcher_id))}</span>${tag(p.visibility)}</div><h3>${link('edit/updates/' + p.id, p.title)}</h3><p>${E(p.text)}</p></article>`).join('') : empty('No activity recorded.', 'Add a progress update, conference note or another research milestone.')}</section>`; };
        document.getElementById('progress-person')?.addEventListener('change', update);
        update();
    }
    function exportPage() { document.getElementById('content').innerHTML = heading('Publishing', 'One public website. One private workspace.', 'Keep the existing GitHub Pages address and connect it to this management server.') + `<div class="notice warning"><strong>GitHub Pages cannot run the admin application.</strong> Host this Python application on a persistent server behind HTTPS. Then use the connected public file below. Never upload the database, backups or private manuscript files to your public repository.</div><div class="panel-grid"><section class="panel"><p class="eyebrow">Recommended for ongoing updates</p><h2>Connected public page</h2><p class="help">This file contains the public design and this server’s public API address. It contains no database records, passwords or drafts. Each page load fetches the latest approved public content.</p><div class="inline-links"><a class="button" href="/api/export/connected" download>Download connected index.html</a></div><p class="help">Upload the downloaded file to <strong>MPHILL-LAB-TRACKER/MPHILL-research-2026</strong> as <code>index.html</code>. Server address: <code>${E(state.origin)}</code>.</p>${state.origin.startsWith('http:') ? '<p class="error">Local HTTP address detected. This export works only from this computer’s local server. For the real GitHub website, first run the application at a public HTTPS address.</p>' : ''}</section><section class="panel"><p class="eyebrow">Read-only backup / public preview</p><h2>Public snapshot</h2><p class="help">A standalone snapshot of approved public fields. It does not receive later changes automatically. Approved local portrait images are embedded. Approved certificate PDFs are embedded too. Other linked PDFs and remote photographs still require their source server.</p><div class="inline-links"><a class="button secondary" href="/api/export/snapshot" download>Download public snapshot</a></div></section></div><section class="panel"><h2>Publishing workflow</h2><div class="progress-list"><article class="progress-card"><h3>1. Save a private record</h3><p>Enter the researcher, project, publication or funder details. Upload files to the specific record. Save again to attach the upload.</p></article><article class="progress-card"><h3>2. Review and approve</h3><p>Check names, publication evidence and photograph permissions. Choose Public only when the public fields are ready. The server excludes internal fields regardless of visibility.</p></article><article class="progress-card"><h3>3. Public pages update on the next load</h3><p>The connected website reads the new approved data directly. To remove content from the public feed, change its visibility back to Private. Static snapshots previously downloaded by visitors cannot be recalled.</p></article></div></section>`; }
    async function auditPage() { document.getElementById('content').innerHTML = heading('Change history', 'Laboratory activity log.', 'The most recent 200 recorded content, upload and account events.') + '<section class="panel" id="audit-content">Loading events…</section>'; const events = await api('/audit'); document.getElementById('audit-content').innerHTML = `<div class="table-scroll"><table><thead><tr><th>Time (UTC)</th><th>Account</th><th>Action</th><th>Record</th></tr></thead><tbody>${events.map(e => `<tr><td>${E(e.created_at)}</td><td>${E(e.actor)}</td><td>${E(e.action)}</td><td>${E(e.collection)} / ${E(e.record_id)}</td></tr>`).join('')}</tbody></table></div>`; }
    async function usersPage() {
        const list = await api('/users');
        document.getElementById('content').innerHTML = heading('Owner controls', 'Accounts & permissions.', 'Create named accounts, assign researcher profiles and revoke access. A role or password change signs that account out.') +
            `<div class="notice"><strong>Owner:</strong> accounts and all content. <strong>Admin:</strong> all content and publishing, but no account permissions. <strong>Researcher:</strong> assigned private manuscripts, milestones and updates only. The last active owner cannot be disabled.</div><div class="account-grid"><section class="panel"><h2>Existing accounts</h2><div class="table-scroll"><table><thead><tr><th>Account</th><th>Role</th><th>Access</th><th></th></tr></thead><tbody>${list.map(u => `<tr><td>${E(u.username)}<span class="help">${E(choose('people', u.researcher_id))}</span></td><td>${E(u.role)}</td><td>${u.active ? 'Active' : 'Disabled'}</td><td><button class="text-button" data-account="${E(u.id)}">Manage</button></td></tr>`).join('')}</tbody></table></div></section><section class="panel" id="account-editor"></section></div>`;
        function editor(account = null) {
            document.getElementById('account-editor').innerHTML = `<h2>${account ? 'Manage ' + E(account.username) : 'Create an account'}</h2><form id="account-form" class="grid-two"><label class="field full"><span>Username</span><input name="username" value="${E(account?.username || '')}" pattern="[a-z0-9][a-z0-9._-]{2,59}" required${account ? ' disabled' : ''} autocomplete="off"></label><label class="field"><span>Role</span><select name="role">${['researcher', 'admin', 'owner'].map(r => `<option${(account?.role || 'researcher') === r ? ' selected' : ''}>${r}</option>`).join('')}</select></label><label class="field"><span>Account status</span><select name="active"><option value="true"${account?.active === 0 ? '' : ' selected'}>Active</option><option value="false"${account?.active === 0 ? ' selected' : ''}>Disabled</option></select></label><label class="field full"><span>Linked researcher profile</span><select name="researcher_id"><option value="">Not assigned</option>${state.choices.people.map(p => `<option value="${E(p.id)}"${account?.researcher_id === p.id ? ' selected' : ''}>${E(p.name)}</option>`).join('')}</select><small class="help">Required for researcher accounts. Administrators do not need a profile assignment.</small></label><label class="field full"><span>${account ? 'New password (leave empty to keep current)' : 'Initial password'}</span><input name="password" type="password" minlength="12" maxlength="1024" autocomplete="new-password"${account ? '' : ' required'}><small class="help">At least 12 characters. Share the initial password privately and ask the researcher to change it after signing in.</small></label><div id="form-error" class="error full" role="alert" hidden></div><div class="field full"><button type="submit" class="button">${account ? 'Save account changes' : 'Create account'}</button>${account ? ' <button type="button" id="new-account" class="button secondary">New account</button>' : ''}</div></form>`;
            document.getElementById('new-account')?.addEventListener('click', () => editor());
            document.getElementById('account-form').addEventListener('submit', async (e) => { e.preventDefault(); const b = Object.fromEntries(new FormData(e.target)); b.active = b.active === 'true'; try {
                await api('/users' + (account ? '/' + account.id : ''), { method: account ? 'PUT' : 'POST', body: JSON.stringify(b) });
                notify(account ? 'Account updated. Existing sessions revoked.' : 'Account created.');
                await usersPage();
            }
            catch (err) {
                showError(err.message);
            } });
        }
        editor();
        document.querySelectorAll('[data-account]').forEach(b => b.addEventListener('click', () => editor(list.find(u => u.id === b.dataset.account))));
    }
    function passwordPage() { document.getElementById('content').innerHTML = heading('Account security', 'Change your password.', 'All sessions will be signed out after a password change.') + `<section class="panel"><form id="password-form" class="grid-two"><label class="field full"><span>Current password</span><input name="current" type="password" required autocomplete="current-password"></label><label class="field"><span>New password</span><input name="password" type="password" required minlength="12" maxlength="1024" autocomplete="new-password"></label><label class="field"><span>Confirm new password</span><input name="confirm" type="password" required minlength="12" maxlength="1024" autocomplete="new-password"></label><div id="form-error" class="error field full" role="alert" hidden></div><div class="field full"><button type="submit" class="button">Change password & sign out</button></div></form></section>`; document.getElementById('password-form').addEventListener('submit', async (e) => { e.preventDefault(); const b = Object.fromEntries(new FormData(e.target)); if (b.password !== b.confirm) {
        showError('The new passwords do not match.');
        return;
    } try {
        await api('/password', { method: 'POST', body: JSON.stringify(b) });
        dirty = false;
        location.href = '/login';
    }
    catch (err) {
        showError(err.message);
    } }); }
    function studio() {
        document.getElementById('content').innerHTML = heading('Website studio · V5', 'Your laboratory. Your website.', 'Edit information, upload photographs and videos, and publish approved changes from this workspace.', link('publish','Publish to GitHub →','button')) +
        `<div class="studio-banner"><div><p class="eyebrow">A clear path from draft to public</p><h2>Edit. Review. Publish.</h2><p>Your private research stays here. Every GitHub push needs your current admin password.</p><a class="button secondary" href="/" target="_blank" rel="noopener">Preview local website ↗</a></div><div class="studio-stats"><strong>${rows('people').length}</strong><span>researcher & collaborator profiles</span><strong>${rows('media').length}</strong><span>uploaded media records</span></div></div>` +
        `<div class="studio-grid">${[
            ['edit/settings/laboratory','01','Homepage & contact','Change your main heading, photograph, animation and laboratory information.'],
            ['records/people','02','People & profiles','Edit professional details, replace portraits and manage private contact information.'],
            ['media','03','Photos, videos & files','Drag files here, add captions and choose exactly what may be published.'],
            ['records/sections','04','Pages & sections','Add a gallery, a text panel, a researcher section or a new page.'],
            ['records/announcements','05','Alerts & events','Keep conferences, seminars and upcoming activities current.'],
            ['records/achievements','06','Achievements','Add recognition and approve certificate downloads.'],
            ['edit/theme/website','07','Theme & colours','Change colours, fonts, layout, logo and the order of homepage sections.'],
            ['records/contacts','08','Contact information','Assign emails, phone numbers, addresses and other contacts to a researcher or the laboratory.'],
            ['records/fields','09','Custom fields','Add your own labelled information to a record, and edit or remove it anytime.'],
            ['trash','10','Trash & restore','Recover removed records or permanently delete unlinked records after password confirmation.']
        ].map(([route,n,title,text])=>`<a class="studio-tile" href="#/${route}"><span>${n}</span><h2>${title}</h2><p>${text}</p><strong>Open editor →</strong></a>`).join('')}</div>`;
    }
    function previewMedia(p) {
        const id=p.file_id;
        if(!/^[a-f0-9]{32}$/.test(id||'')) return '<span class="media-placeholder">No file attached</span>';
        return p.kind==='video' ? `<video controls playsinline preload="metadata" src="/media/${id}"></video>` : p.kind==='document' ? `<a class="media-pdf" href="/media/${id}" target="_blank" rel="noopener">PDF · Open document ↗</a>` : `<img src="/media/${id}" alt="${E(p.alt||p.title)}" loading="lazy">`;
    }
    function uploadFile(file, progress) {
        return new Promise((resolve,reject)=>{
            const xhr=new XMLHttpRequest();xhr.open('POST','/api/media/upload');xhr.setRequestHeader('X-CSRF-Token',user.csrf);
            xhr.upload.onprogress=e=>{if(e.lengthComputable)progress(Math.round(e.loaded/e.total*100));};
            xhr.onerror=()=>reject(new Error('Upload interrupted. Check that the local server is running.'));
            xhr.onload=()=>{let result;try{result=JSON.parse(xhr.responseText);}catch{return reject(new Error('Invalid upload response.'));}if(xhr.status>=200&&xhr.status<300)resolve(result);else reject(new Error(result.detail||'Upload failed.'));};
            const form=new FormData();form.append('file',file);xhr.send(form);
        });
    }
    async function mediaPage() {
        const system=await api('/system/info');
        document.getElementById('content').innerHTML=heading('Media library','Bring your research into view.','Upload first, then edit captions and explicitly approve public sharing.',link('records/sections','Arrange pages & sections','button secondary'))+
        `<section class="panel"><div class="drop-zone" id="media-drop" tabindex="0" role="button" aria-label="Choose media files"><strong>Drop photographs, videos or PDFs here</strong><span>or click to browse your computer</span><small>Images: 20 MB · videos: 80 MB · PDF: 20 MB</small></div><input id="media-files" type="file" accept=".jpg,.jpeg,.png,.webp,.gif,.bmp,.tif,.tiff,.mp4,.webm,.mov,.m4v,.pdf" multiple hidden><div id="upload-progress" aria-live="polite"></div></section><section class="panel"><div class="toolbar"><label class="field grow"><span>Find media</span><input id="media-search" type="search" placeholder="Search title, caption or type"></label></div><div class="media-grid" id="media-grid"></div></section>`;
        document.getElementById('media-drop').insertAdjacentHTML('beforebegin',`<p class="notice">Images: JPEG/JPG, PNG, WebP, GIF, BMP, TIFF (20 MB). Videos: MP4/WebM/MOV (80 MB). PDFs: 20 MB. ${system.ffprobe?'Video validation available.':'Video support missing: run sudo apt install ffmpeg in the terminal.'}</p>`);
        const drop=document.getElementById('media-drop'),input=document.getElementById('media-files');
        const draw=()=>{const q=document.getElementById('media-search').value.toLowerCase();document.getElementById('media-grid').innerHTML=rows('media').filter(p=>[p.title,p.caption,p.kind].join(' ').toLowerCase().includes(q)).map(p=>`<article class="media-tile">${previewMedia(p)}<div><h3>${E(p.title)}</h3><p>${tag(p.visibility)} ${p.approved?'Approved':'Not approved'}</p>${link('edit/media/'+p.id,'Edit information & approval →')} <button class="text-button danger-text" data-trash-record="media/${E(p.id)}">Delete</button></div></article>`).join('')||empty('Your media library is ready.','Upload a file above to get started.');};
        const batch=async files=>{if(working)return;working=true;drop.setAttribute('aria-disabled','true');try{await refresh();for(const file of files){const entry=document.createElement('div');entry.className='upload-progress';entry.innerHTML=`<span>${E(file.name)}</span><progress max="100" value="0"></progress><small>Uploading…</small>`;document.getElementById('upload-progress').appendChild(entry);try{const result=await uploadFile(file,n=>entry.querySelector('progress').value=n);entry.querySelector('small').innerHTML=link('edit/media/'+result.record.id,'Uploaded privately — edit & approve →');}catch(error){entry.querySelector('small').textContent=error.message;entry.classList.add('error');}}await refresh();draw();}finally{working=false;drop.removeAttribute('aria-disabled');input.value='';}};
        drop.addEventListener('click',()=>{if(!working)input.click();});drop.addEventListener('keydown',e=>{if(['Enter',' '].includes(e.key)){e.preventDefault();input.click();}});
        for(const type of ['dragover','dragenter'])drop.addEventListener(type,e=>{e.preventDefault();drop.classList.add('dragging');});
        drop.addEventListener('dragleave',()=>drop.classList.remove('dragging'));drop.addEventListener('drop',e=>{e.preventDefault();drop.classList.remove('dragging');batch([...e.dataTransfer.files]);});input.addEventListener('change',()=>batch([...input.files]));document.getElementById('media-search').addEventListener('input',draw);draw();
    }
    async function publishPage() {
        const config=await api('/publish/status');
        document.getElementById('content').innerHTML=heading('Publish to GitHub','From your workspace to the world.','Review the exact release, then confirm your administrator password for this push.')+
        `<section class="panel"><div class="notice"><strong>Destination:</strong> MPHILL-LAB-TRACKER/MPHILL-research-2026 · <strong>gh-pages</strong><br>Only generated public pages and approved media are published. Your source branch, database and private documents are not staged.</div>${config.ready?`<p class="help">Existing clone: ${E(config.root)}</p>`:`<p class="error">${E(config.detail)}</p>`}<button id="prepare-release" class="button" ${config.ready?'':'disabled'}>Prepare preview</button><div id="release-result" class="release-result" aria-live="polite"></div></section><section class="panel"><h2>One-time setup</h2><p>In the terminal, authenticate GitHub with <code>gh auth login</code> and <code>gh auth setup-git</code>. Your local admin password confirms publication; it is not your GitHub password.</p><p>After the first successful push, set GitHub <strong>Settings → Pages → Deploy from a branch → gh-pages → / (root)</strong>. Keep the local backend running while editing and publishing. A successful push does not mean deployment has finished.</p><div class="inline-links"><a class="button secondary" href="/api/export/bundle" download>Download public website ZIP</a><a class="button secondary" href="/api/export/snapshot" download>Download single HTML snapshot</a></div></section>`;
        document.getElementById('prepare-release').addEventListener('click',async e=>{const b=e.currentTarget;b.disabled=true;b.textContent='Preparing approved files…';try{const release=await api('/publish/prepare',{method:'POST'});document.getElementById('release-result').innerHTML=`<p><strong>Ready to review:</strong> ${release.files} files · ${(release.bytes/1024/1024).toFixed(1)} MB</p><p class="help">Preview expires after 30 minutes. Any public change requires a new preview.</p><div class="inline-links"><a class="button secondary" href="${E(release.preview_url)}" target="_blank" rel="noopener">Open exact website preview ↗</a><button class="button" id="confirm-release">Confirm & publish</button></div>`;document.getElementById('confirm-release').addEventListener('click',()=>confirmPublish(release));}catch(error){showError(error.message);}finally{b.disabled=false;b.textContent='Prepare new preview';}});
    }
    function confirmPublish(release) {
        const dialog=document.createElement('dialog');dialog.className='publish-dialog';dialog.innerHTML=`<form id="publish-password-form"><p class="eyebrow">Administrator confirmation</p><h2>Publish this website?</h2><p>This uploads the reviewed public release to <strong>gh-pages</strong>. Published media can remain in Git history even after removal.</p><label class="field"><span>Your current local administrator password</span><input type="password" name="password" autocomplete="current-password" maxlength="1024" required></label><p class="error" id="publish-error" hidden></p><div class="inline-links"><button class="button" type="submit">Confirm & push to GitHub</button><button class="button secondary" type="button" id="cancel-publish">Cancel</button></div></form>`;document.body.appendChild(dialog);dialog.showModal();dialog.querySelector('input').focus();
        dialog.querySelector('#cancel-publish').addEventListener('click',()=>dialog.close());dialog.addEventListener('close',()=>dialog.remove());
        dialog.querySelector('form').addEventListener('submit',async e=>{e.preventDefault();const button=e.target.querySelector('[type=submit]');button.disabled=true;button.textContent='Publishing…';const password=e.target.elements.password.value;e.target.elements.password.value='';try{const result=await api('/publish/confirm',{method:'POST',body:JSON.stringify({preview_id:release.id,password})});dialog.close();document.getElementById('release-result').innerHTML=`<div class="notice"><strong>Push succeeded.</strong><p>Commit: <code>${E(result.commit)}</code></p><p>${E(result.message)}</p><a href="${E(result.website)}" target="_blank" rel="noopener">Open public website ↗</a></div>`;}catch(error){const box=dialog.querySelector('#publish-error');box.textContent=error.message;box.hidden=false;button.disabled=false;button.textContent='Confirm & push to GitHub';}});
    }

    // V5 management: reversible deletion, linked contacts/fields and visual appearance.
    const imageAccept = '.jpg,.jpeg,.png,.webp,.gif,.bmp,.tif,.tiff';
    const allAccept = imageAccept + ',.mp4,.m4v,.mov,.webm,.pdf';
    async function trashRecord(collection, rid) {
        try {
            const record=await api('/records/'+collection+'/'+rid);
            const refs=await api('/references/'+collection+'/'+rid);
            if(!confirm('Move “'+titleOf(collection,record)+'” to Trash? It will disappear from the local public website; publish afterward to update GitHub. You can restore it. '+(refs.references.length ? refs.references.length+' existing links will remain saved, but public links to this item are hidden.':'')))return;
            const result=await api('/records/'+collection+'/'+rid+'/trash',{method:'POST',body:JSON.stringify({_version:record._version})});
            dirty=false;await refresh();notify(result.message);
            if(location.hash.startsWith('#/edit/'))location.hash='/records/'+collection;else await render();
        } catch(error){showError(error.message);}
    }
    async function trashPage() {
        const items=await api('/trash');
        document.getElementById('content').innerHTML=heading('Recoverable removal','Trash & restore.','Restore an item as a private draft, or permanently delete an unlinked item after confirming your password.')+
            `<div class="notice">Removing an item locally does not recall earlier website copies. Publish a new release to update GitHub. Permanent deletion does not erase earlier Git commits, private backups or downloaded files.</div><section class="panel">${items.length?`<div class="table-scroll"><table><thead><tr><th>Record</th><th>Removed</th><th>Actions</th></tr></thead><tbody>${items.map(p=>`<tr><td><strong>${E(p.label)}</strong><small class="help">${E(state.schemas[p.collection]?.label || p.collection)}</small></td><td>${E(p.deleted_at)}<small class="help">${E(p.deleted_by)}</small></td><td><button class="button secondary" data-restore="${E(p.collection+'/'+p.id)}">Restore privately</button> <button class="button danger" data-purge="${E(p.collection+'/'+p.id)}">Delete permanently</button></td></tr>`).join('')}</tbody></table></div>`:empty('Trash is empty.','Use Delete / move to Trash from a record or media file.')}</section>`;
        document.querySelectorAll('[data-restore]').forEach(button=>button.onclick=async()=>{const p=items.find(x=>x.collection+'/'+x.id===button.dataset.restore);try{await api('/trash/'+button.dataset.restore+'/restore',{method:'POST',body:JSON.stringify({_version:p._version})});await refresh();await trashPage();notify('Restored as a private draft. Review links and approve before publishing.');}catch(e){showError(e.message);}});
        document.querySelectorAll('[data-purge]').forEach(button=>button.onclick=()=>{
            const p=items.find(x=>x.collection+'/'+x.id===button.dataset.purge);
            const dialog=document.createElement('dialog');dialog.className='publish-dialog';dialog.innerHTML=`<form><p class="eyebrow">Permanent deletion</p><h2>Delete ${E(p.label)}?</h2><p>Removes this record, its attached upload files and its saved revision values from this installation. Linked records must be detached first. Earlier backups and Git history remain.</p><label class="field"><span>Type DELETE</span><input name="confirmation" autocomplete="off" required pattern="DELETE"></label><label class="field"><span>Current administrator password</span><input name="password" type="password" autocomplete="current-password" required maxlength="1024"></label><p class="error" hidden></p><div class="inline-links"><button type="submit" class="button danger">Delete permanently</button><button type="button" class="button secondary" data-cancel>Cancel</button></div></form>`;document.body.append(dialog);dialog.showModal();dialog.querySelector('[data-cancel]').onclick=()=>dialog.close();dialog.addEventListener('close',()=>dialog.remove());
            dialog.querySelector('form').onsubmit=async e=>{e.preventDefault();const form=e.target,submit=form.querySelector('[type=submit]');submit.disabled=true;const password=form.elements.password.value;form.elements.password.value='';try{await api('/trash/'+button.dataset.purge+'/purge',{method:'POST',body:JSON.stringify({_version:p._version,password,confirmation:form.elements.confirmation.value})});dialog.close();await refresh();await trashPage();notify('Deleted from this installation. Publish to update the public website.');}catch(error){const box=dialog.querySelector('.error');box.textContent=error.message;box.hidden=false;submit.disabled=false;}};
        });
    }
    function valueFrom(form,f) {
        const input=form.elements[f.key];
        if(f.type==='multi-choice')return [...form.querySelectorAll('[data-choice-group="'+f.key+'"] input:checked')].map(x=>x.value);
        return f.type==='multi'?[...input.selectedOptions].map(x=>x.value):['lines','urls'].includes(f.type)?input.value.split(/\r?\n/).map(x=>x.trim()).filter(Boolean):f.type==='checkbox'?input.checked:['number','year','weight','percent','money'].includes(f.type)?(input.value===''?null:Number(input.value)):input.value;
    }
    function setupV5Editor(collection,p,isNew,readOnly) {
        const form=document.getElementById('record-form');
        form.querySelectorAll('[data-clear-field]').forEach(button=>button.onclick=()=>{const input=form.elements[button.dataset.clearField];if(!input)return;if(input.tagName==='SELECT'&&input.multiple){[...input.options].forEach(x=>x.selected=false);}else if(input.type==='checkbox')input.checked=false;else input.value='';input.dispatchEvent(new Event('change',{bubbles:true}));dirty=true;});
        form.querySelectorAll('[data-multi-key]').forEach(box=>box.onchange=()=>{const select=form.elements[box.dataset.multiKey];const option=[...select.options].find(x=>x.value===box.value);if(option)option.selected=box.checked;dirty=true;});
        form.querySelectorAll('[data-choice-up],[data-choice-down]').forEach(button=>button.onclick=()=>{const row=button.closest('.choice-row'),parent=row.parentElement;if(button.hasAttribute('data-choice-up')&&row.previousElementSibling)parent.insertBefore(row,row.previousElementSibling);else if(button.hasAttribute('data-choice-down')&&row.nextElementSibling)parent.insertBefore(row.nextElementSibling,row);dirty=true;});
        const params=new URLSearchParams((location.hash.split('?')[1]||''));
        if(collection==='fields') {
            const select=form.elements.target_collection,target=form.elements.target_id;
            const draw=()=>{const before=target.value||p.target_id||params.get('target_id');target.innerHTML='<option value="">Select a record…</option>'+rows(select.value).map(x=>`<option value="${E(x.id)}"${x.id===before?' selected':''}>${E(titleOf(select.value,x))}</option>`).join('');};
            select.addEventListener('change',draw);draw();
        }
        if(readOnly)return;
        if(admin()&&!isNew&&!['settings','theme'].includes(collection)) {
            const actions=form.querySelector('.form-actions');actions.insertAdjacentHTML('beforeend','<button class="button danger" type="button" id="trash-this-record">Delete / move to Trash</button>');
            document.getElementById('trash-this-record').onclick=()=>trashRecord(collection,p.id);
        }
        if(admin()){
            if(collection!=='theme')form.insertAdjacentHTML('afterbegin',`<div class="editor-shortcuts"><strong>Quick controls</strong>${form.elements.media_items?'<button type="button" class="button secondary" data-jump-uploads>Photos, videos & files ↓</button>':''}${form.elements.hidden_fields?'<button type="button" class="button secondary" data-jump-hidden>Hide / clear fields ↓</button>':''}${!isNew&&collection==='people'?link('new/contacts?researcher_id='+p.id,'Add contact','button secondary'):''}${!isNew&&!['fields','contacts','media','theme'].includes(collection)?link('new/fields?target_collection='+collection+'&target_id='+p.id,'Add custom field','button secondary'):''}${!isNew&&!['settings','theme'].includes(collection)?'<button type="button" class="button danger" data-top-delete>Delete record</button>':''}</div>`);
            form.querySelector('[data-jump-uploads]')?.addEventListener('click',()=>form.elements.media_items.closest('.field').scrollIntoView({behavior:'smooth',block:'start'}));
            form.querySelector('[data-jump-hidden]')?.addEventListener('click',()=>form.querySelector('[data-choice-group=hidden_fields]').closest('.field').scrollIntoView({behavior:'smooth',block:'start'}));
            form.querySelector('[data-top-delete]')?.addEventListener('click',()=>trashRecord(collection,p.id));
        }
        const mediaSelect=form.elements.media_items;
        if(mediaSelect && admin()) {
            const box=mediaSelect.closest('.field');
            box.insertAdjacentHTML('beforeend',`<div class="attachment-upload"><h3>Upload photos, videos & files here</h3><p class="help">This is separate from the dedicated PDF field. New files can be attached before the record is saved.</p><div class="drop-zone compact" data-record-drop tabindex="0" role="button" aria-label="Drop attachments or browse"><strong>Drop files here or browse</strong><span>JPEG/JPG, PNG, WebP, GIF, BMP, TIFF · MP4, WebM, MOV · PDF</span></div><input type="file" data-attachment-files accept="${allAccept}" multiple hidden><label class="checkbox"><input type="checkbox" data-approve-attachments> Approve these uploads for public sharing (only select when permission is confirmed)</label><div data-attachment-progress role="status"></div></div>`);
            const drop=box.querySelector('[data-record-drop]'),input=box.querySelector('[data-attachment-files]'),progress=box.querySelector('[data-attachment-progress]');
            const upload=async files=>{if(working)return;working=true;try{for(const file of files){progress.textContent='Uploading / checking '+file.name+'…';const result=await uploadFile(file,n=>progress.textContent=file.name+' · '+n+'% transferred; checking/converting…');let record=result.record;if(box.querySelector('[data-approve-attachments]').checked){const body={...record,visibility:'public',approved:true};delete body._updated_at;record=await api('/records/media/'+record.id,{method:'PUT',body:JSON.stringify(body)});}const option=new Option(record.title,record.id,true,true);mediaSelect.add(option);const checks=box.querySelector('.multi-checks');if(checks){const label=document.createElement('label');const checkbox=document.createElement('input');checkbox.type='checkbox';checkbox.checked=true;checkbox.onchange=()=>{option.selected=checkbox.checked;dirty=true;};label.append(checkbox,document.createTextNode(record.title+' · '+record.visibility));checks.append(label);}dirty=true;}await refresh();progress.textContent='Files uploaded and selected. Save this record to attach them. Public files still require Publish to GitHub.';}catch(error){progress.textContent=error.message;showError(error.message);}finally{working=false;input.value='';}};
            drop.onclick=()=>input.click();drop.onkeydown=e=>{if(['Enter',' '].includes(e.key)){e.preventDefault();input.click();}};drop.ondragover=e=>{e.preventDefault();drop.classList.add('dragging');};drop.ondragleave=()=>drop.classList.remove('dragging');drop.ondrop=e=>{e.preventDefault();drop.classList.remove('dragging');upload([...e.dataTransfer.files]);};input.onchange=()=>upload([...input.files]);
        }
        if(!isNew && admin() && !['fields','contacts','media','theme'].includes(collection)) {
            const fields=rows('fields').filter(x=>x.target_collection===collection&&x.target_id===p.id);
            const contacts=collection==='people'?rows('contacts').filter(x=>x.researcher_id===p.id):[];
            document.getElementById('content').insertAdjacentHTML('beforeend',`<section class="panel"><div class="panel-heading"><h2>Custom fields & assigned information</h2>${link('new/fields?target_collection='+collection+'&target_id='+p.id,'Add custom field','button secondary')}</div><p class="help">Add, edit, hide or delete your own labelled values without changing application code. Private values are never published.</p>${fields.map(x=>`<p>${link('edit/fields/'+x.id,x.label)} · ${E(x.value)} ${tag(x.visibility)}</p>`).join('')||'<p>No custom fields yet.</p>'}${collection==='people'?`<h3>Assigned contact information</h3>${contacts.map(x=>`<p>${link('edit/contacts/'+x.id,x.label)} · ${E(x.value)} ${tag(x.visibility)}</p>`).join('')}${link('new/contacts?researcher_id='+p.id,'Add contact for this researcher','button secondary')}`:''}</section>`);
        }
        if(collection==='theme')setupThemeEditor(form);
    }
    function setupThemeEditor(form) {
        const presets={
            'Forest & cream':{primary:'#244d3e',accent:'#a88451',background:'#f5f3eb',surface:'#ffffff',text_color:'#1d3028',muted_color:'#616c63',border_color:'#d9dfd4'},
            'Clinical blue':{primary:'#164f80',accent:'#157c80',background:'#f1f6fa',surface:'#ffffff',text_color:'#172b3a',muted_color:'#526675',border_color:'#cedce8'},
            'Burgundy & ivory':{primary:'#7c263a',accent:'#936515',background:'#faf5ee',surface:'#ffffff',text_color:'#35212a',muted_color:'#705b61',border_color:'#e2d4d6'},
            'Midnight':{primary:'#a0dbcc',accent:'#e2c38e',background:'#132323',surface:'#1c3232',text_color:'#eef7f4',muted_color:'#bbd1ca',border_color:'#44625b'}
        };
        form.insertAdjacentHTML('afterbegin',`<section class="theme-studio"><div><p class="eyebrow">Theme studio</p><h2>Style the public website.</h2><div class="inline-links">${Object.keys(presets).map(name=>`<button type="button" class="button secondary" data-preset="${E(name)}">${E(name)}</button>`).join('')}</div><p class="help">Presets change the colour controls below. Save when ready. Homepage blocks can be hidden or reordered; custom sections stay editable separately.</p></div><div id="theme-sample" class="theme-sample"><small>LIVE COLOUR SAMPLE</small><h3>Your laboratory.<br>Your visual identity.</h3><p>Research, people and ideas — in your chosen style.</p><span id="sample-button">Explore research →</span><p id="contrast-check"></p></div></section>`);
        const sample=document.getElementById('theme-sample');
        const contrast=(a,b)=>{const lum=hex=>{const values=[1,3,5].map(i=>parseInt(hex.slice(i,i+2),16)/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);return values[0]*.2126+values[1]*.7152+values[2]*.0722;};const x=lum(a),y=lum(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05);};
        const draw=()=>{const value=k=>form.elements[k].value;sample.style.backgroundColor=value('background');sample.style.color=value('text_color');sample.style.borderColor=value('border_color');sample.querySelector('h3').style.color=value('primary');sample.style.fontFamily=value('body_font')==='serif'?'Georgia,serif':'system-ui,sans-serif';sample.querySelector('h3').style.fontFamily=value('heading_font')==='serif'?'Georgia,serif':'system-ui,sans-serif';sample.style.borderRadius=value('corner_radius')+'px';const button=document.getElementById('sample-button');button.style.backgroundColor=value('primary');button.style.color=contrast(value('primary'),'#ffffff')>=contrast(value('primary'),'#000000')?'#ffffff':'#000000';const ratio=contrast(value('text_color'),value('background'));document.getElementById('contrast-check').textContent='Text/background contrast: '+ratio.toFixed(2)+':1'+(ratio<4.5?' — increase contrast for readability.':'');};
        form.querySelectorAll('[data-preset]').forEach(button=>button.onclick=()=>{for(const [key,value]of Object.entries(presets[button.dataset.preset]))form.elements[key].value=value;dirty=true;draw();});form.addEventListener('input',draw);form.addEventListener('change',draw);draw();
    }

    async function render() {
        const hash = location.hash || (admin() ? '#/studio' : '#/dashboard');
        if (dirty && hash !== lastHash && !confirm('Leave this form and discard unsaved changes?')) {
            history.replaceState(null, '', lastHash);
            return;
        }
        dirty = false;
        lastHash = hash;
        const parts = hash.split('?')[0].replace(/^#\/?/, '').split('/');
        const route = parts[0] || 'dashboard';
        document.getElementById('sidebar').classList.remove('open');
        document.getElementById('mobile-menu').setAttribute('aria-expanded', 'false');
        document.querySelectorAll('.sidebar nav a').forEach(a => { if (a.hash === hash)
            a.setAttribute('aria-current', 'page');
        else
            a.removeAttribute('aria-current'); });
        if (!admin() && ['users', 'audit', 'export', 'board','studio','media','publish','trash'].includes(route)) {
            document.getElementById('content').innerHTML = heading('Restricted', 'Administrator access required.');
            return;
        }
        try {
            if (route === 'studio') studio();
            else if(route==='media') await mediaPage();
            else if(route==='trash') await trashPage();
            else if(route==='publish' || route==='export') await publishPage();
            else if (route === 'dashboard')
                dashboard();
            else if (route === 'records')
                records(parts[1]);
            else if (route === 'edit')
                await edit(parts[1], parts[2]);
            else if (route === 'new')
                await edit(parts[1]);
            else if (route === 'board')
                board();
            else if (route === 'progress')
                progress();
            else if (route === 'export')
                exportPage();
            else if (route === 'users')
                await usersPage();
            else if (route === 'audit')
                await auditPage();
            else if (route === 'password')
                passwordPage();
            else
                dashboard();
            document.title = (document.querySelector('#content h1')?.textContent || 'Workspace') + ' | TED²';
            window.scrollTo(0, 0);
        }
        catch (e) {
            showError(e.message);
        }
    }
    window.addEventListener('beforeunload', e => { if (dirty) {
        e.preventDefault();
        e.returnValue = '';
    } });
    async function init() { try {
        const session = await api('/session');
        user = session.user;
        if (!user) {
            loginScreen();
            return;
        }
        if (location.pathname === '/login') {
            location.replace(user.role === 'researcher' ? '/workspace' : '/admin');
            return;
        }
        await refresh();
        shell();
        await render();
        window.addEventListener('hashchange', render);
    }
    catch (e) {
        app.innerHTML = `<main class="login-panel"><section class="login-card"><h1>The workspace is unavailable.</h1><p class="error">${E(e.message)}</p><a href="/login">Return to sign in</a></section></main>`;
    } }
    app.addEventListener('click',e=>{const b=e.target.closest('[data-trash-record]');if(b){const [collection,id]=b.dataset.trashRecord.split('/');trashRecord(collection,id);}});
    init();
})();
