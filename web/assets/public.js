/* Public SPA: all dynamic text is escaped; external links are protocol-checked. */
'use strict';
(() => {
    const cfg = window.TED2_CONFIG || { live: false, apiBase: '' };
    let data = window.TED2_DATA || {};
    const main = document.getElementById('main'), nav = document.getElementById('primary-nav');
    const E = v => String(v ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
    const rows = c => data[c] || [];
    const one = (c, id) => rows(c).find(p => p.id === id);
    const safeURL = u => { try {
        const v = new URL(u);
        return ['http:', 'https:'].includes(v.protocol) ? v.href : '';
    }
    catch {
        return '';
    } };
    const external = (u, label, cls = '') => safeURL(u) ? `<a class="${E(cls)}" href="${E(safeURL(u))}" target="_blank" rel="noopener noreferrer">${E(label)} ↗</a>` : '';
    const profileSlugs = {'denis-bouman':'denise-bouman','manelia-halweendo':'maneria-halweendo','charity-mepa':'charity-maepa','nonku-phiri':'nonku-phili','jaydine-feris':'jaydine-jeris'};
    const publicPath = path => path.replace(/^profiles\/([^?]+)/, (match, id) => 'profiles/' + (profileSlugs[id] || id));
    const link = (path, label, cls = '') => `<a class="${E(cls)}" href="#/${E(publicPath(path))}">${E(label)}</a>`;
    const initials = n => n.replace(/^(Prof|Dr|Ms|Mr|Mrs)\.?\s+/i, '').split(/\s+/).filter(Boolean).slice(0, 2).map(x => x[0]).join('');
    const portrait = p => { const v = p.photo_url || ''; return safeURL(v) || (v.startsWith('data:image/jpeg;base64,') ? v : ''); };
    function avatar(p, size = '') { const u = portrait(p); return `<span class="avatar ${E(size)}" aria-label="${u ? 'Portrait from attributed source' : 'Initials for'} ${E(p.name)}"><span aria-hidden="true">${E(initials(p.name))}</span>${u ? `<img class="profile-image" src="${E(u)}" alt="${E(p.name)}" loading="lazy" referrerpolicy="no-referrer">` : ''}</span>`; }
    const empty = (title, text) => `<div class="empty-state"><strong>${E(title)}</strong>${E(text)}</div>`;
    const nice = v => String(v || '').replace(/-/g, ' ').replace(/^\w/, c => c.toUpperCase());
    const tags = items => `<div class="chips">${(items || []).map(t => `<span class="chip">${E(t)}</span>`).join('')}</div>`;
    const head = (label, title, intro = '') => `<section class="page-heading"><div class="container"><div class="breadcrumbs">${link('', 'Home')} <span>/</span> ${E(label)}</div><p class="eyebrow">${E(label)}</p><h1>${E(title)}</h1>${intro ? `<p class="lead">${E(intro)}</p>` : ''}</div></section>`;
    const side = () => `<aside class="side-nav"><p class="side-title">Research directory</p><nav>${[['researchers', 'Researchers'], ['activity', 'Activity & alerts'], ['publications', 'Publications'], ['research', 'Active research'], ['pipeline', 'Manuscript pipeline'], ['collaborators', 'Collaborations'], ['funders', 'Funders'], ['sources', 'Sources & credits']].map(([u, t]) => link(u, t)).join('')}</nav><p class="side-note">Only approved public information is shown here. Private milestones, reviewer notes and draft files remain in the researcher workspace.</p></aside>`;
    const page = (label, title, intro, html, sidebar = false) => head(label, title, intro) + `<section class="container page-body ${sidebar ? 'directory-layout' : ''}">${sidebar ? side() : ''}<div>${html}</div></section>`;
    function toast(text) { const t = document.getElementById('toast'); t.textContent = text; t.hidden = false; setTimeout(() => t.hidden = true, 3500); }
    function personCard(p) { return `<article class="person-card">${avatar(p)}<p class="eyebrow">${E(p.group)}</p><h2>${link('profiles/' + p.id, p.name)}</h2><p>${E(p.role)}</p>${tags(p.topics)}${link('profiles/' + p.id, 'Profile & selected work →', 'text-link')}</article>`; }
    function pubCard(p) { const url = p.doi ? 'https://doi.org/' + p.doi : p.source_url; return `<article class="publication-card" id="pub-${E(p.id)}"><div class="publication-meta"><span class="record-type ${p.type !== 'peer-reviewed' ? 'limited' : ''}">${E(nice(p.type))}</span><span>${E(p.year)}</span><span>${E(p.venue)}</span></div><h3>${external(url, p.title) || E(p.title)}</h3><p class="authors">${E((p.authors || []).join('; '))}</p><p class="pub-summary">${E(p.summary)}</p><div class="pub-actions">${external(p.source_url, 'Source record')}${p.doi ? external('https://doi.org/' + p.doi, 'DOI') : ''}${p.document_url ? external(p.document_url, 'Approved PDF') : ''}<button class="copy-button" data-copy="${E(p.id)}">Copy citation</button></div>${p.note ? `<details><summary>Evidence & attribution</summary><p>${E(p.note)}</p></details>` : ''}</article>`; }
    function projectCard(p) { const val = Number.isFinite(Number(p.public_progress)) && p.public_progress !== null ? Math.max(0, Math.min(100, Number(p.public_progress))) : null; return `<article class="record-card"><span class="chip">${E(nice(p.stage))}</span><h3>${link('research/' + p.id, p.title)}</h3><p>${E(p.summary)}</p>${val !== null ? `<progress value="${val}" max="100" aria-label="Approved public progress"></progress><p class="progress-label">${val}% · approved public progress</p>` : ''}<div class="actions">${link('research/' + p.id, 'View research →', 'text-link')}</div></article>`; }
    function manuscriptCard(p) { return `<article class="record-card"><span class="chip">${E(nice(p.stage))}</span><h3>${E(p.title)}</h3><p>${E(p.summary)}</p>${p.journal ? `<p>${E(p.journal)}</p>` : ''}${tags((p.people || []).map(id => one('people', id)?.name).filter(Boolean))}${p.doi ? external('https://doi.org/' + p.doi, 'Published DOI') : ''}</article>`; }
    function collabCard(p) { return `<article class="record-card"><p class="eyebrow">${E(p.partner)}</p><h3>${link('collaborations/' + p.id, p.title)}</h3><p>${E(p.summary)}</p><div class="actions">${link('collaborations/' + p.id, 'Collaboration details →', 'text-link')}</div></article>`; }
    // Date-only notices are compared in Namibia time; no UTC-midnight day shift.
    function today() {
        const parts = new Intl.DateTimeFormat('en-GB', { timeZone: 'Africa/Windhoek', year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(new Date());
        const part = kind => parts.find(x => x.type === kind).value;
        return `${part('year')}-${part('month')}-${part('day')}`;
    }
    function dates(start, end) {
        if (!start) return 'Dates to be announced';
        const a = new Date(start + 'T12:00:00'), b = new Date((end || start) + 'T12:00:00');
        if (Number.isNaN(+a) || Number.isNaN(+b)) return 'Date awaiting confirmation';
        const fmt = (d, opts) => d.toLocaleDateString('en-GB', opts);
        if (!end || end === start) return fmt(a, { day: 'numeric', month: 'long', year: 'numeric' });
        if (start.slice(0, 7) === end.slice(0, 7)) return `${a.getDate()}–${b.getDate()} ${fmt(a, { month: 'long', year: 'numeric' })}`;
        return `${fmt(a, { day: 'numeric', month: 'short', year: 'numeric' })} – ${fmt(b, { day: 'numeric', month: 'short', year: 'numeric' })}`;
    }
    const upcoming = a => !(a.end_date || a.start_date) || (a.end_date || a.start_date) >= today();
    const byDate = (a, b) => (a.start_date || '9999').localeCompare(b.start_date || '9999') || a.title.localeCompare(b.title);
    const dateEvidence = a => a.date_status === 'date-conflict' ? 'Date confirmation pending' : a.date_status === 'date-to-be-announced' ? 'Coming soon' : a.date_status === 'lab-supplied' ? 'Laboratory schedule' : 'Conference dates confirmed';
    function dateTile(a) {
        if (!a.start_date) return '<div class="event-date undated"><span>Coming</span><strong>soon</strong></div>';
        const start = new Date(a.start_date + 'T12:00:00');
        const sameMonth = a.end_date && a.end_date.slice(0, 7) === a.start_date.slice(0, 7);
        return `<div class="event-date"><span>${E(start.toLocaleDateString('en-GB', { month: 'short' }))}</span><strong>${start.getDate()}${sameMonth && a.end_date !== a.start_date ? '–' + Number(a.end_date.slice(8)) : ''}</strong><small>${E(a.start_date.slice(0, 4))}</small></div>`;
    }
    function announcementCard(a, compact = false) {
        return `<article class="event-card" data-event="${E(a.id)}">${dateTile(a)}<div class="event-copy"><p class="eyebrow">${E(a.kind === 'conference' ? 'Conference presentation' : nice(a.kind))}${!upcoming(a) ? ' · Past activity' : ''}</p><h3>${link('activity/' + a.id, a.title)}</h3><p class="event-range">${E(dates(a.start_date, a.end_date))}</p><span class="event-badge ${a.date_status === 'date-conflict' ? 'date-warning' : ''}">${E(dateEvidence(a))}</span>${compact ? '' : `<p>${E(a.description)}</p><details class="event-evidence"><summary>Date & participation evidence</summary><p>${E(a.evidence_note)}</p></details>`}<div class="event-links">${link('activity/' + a.id, 'Read activity details →')}${external(a.official_url, 'Official host page')}</div></div></article>`;
    }
    function homeAlerts() {
        const all = rows('announcements').filter(a => a.homepage && upcoming(a));
        if (!all.length) return '';
        const conferences = all.filter(a => a.kind === 'conference').sort(byDate);
        const other = all.filter(a => a.kind !== 'conference').sort(byDate);
        const conflict = conferences.find(a => a.date_status === 'date-conflict');
        return `<section class="section alerts-section" id="alerts" aria-labelledby="alerts-heading"><div class="container"><div class="section-head"><div><p class="eyebrow alert-eyebrow"><span aria-hidden="true"></span> Alerts</p><h2 id="alerts-heading">Upcoming conference<br>presentations.</h2></div>${link('activity', 'All laboratory activity →', 'text-link')}</div><div class="alerts-grid"><div class="event-list">${conferences.map(a => announcementCard(a, true)).join('') || empty('No upcoming conference presentations.', 'Seminar and laboratory notices appear alongside this schedule.')}${conflict ? `<div class="date-discrepancy"><strong>NCRST date check.</strong> The laboratory supplied <strong>${E(dates(conflict.start_date, conflict.end_date))}</strong>; the organiser’s available call lists <strong>${E(dates(conflict.official_start_date, conflict.official_end_date))}</strong>. Please confirm the date with NCRST. ${external(conflict.official_url, 'Official organiser notice')}</div>` : ''}</div><aside class="seminar-stack" aria-label="Coming soon">${other.map(a => `<article class="seminar-notice"><p class="eyebrow">Coming soon · ${E(nice(a.kind))} series</p><span class="seminar-index" aria-hidden="true">TED² / EXCHANGE</span><h3>${E(a.title)}</h3><p>${E(a.description.replace(/^Coming soon:\s*/i, '').replace(/^./, c => c.toUpperCase()))}</p><p class="seminar-note">${E(a.evidence_note)}</p><div class="actions">${link('activity/' + a.id, 'Series announcement →', 'button secondary')}</div></article>`).join('')}</aside></div></div></section>`;
    }
    function certificateButton(a) {
        if (!a.document_url) return '';
        if (a.document_url.startsWith('data:application/pdf;base64,')) return `<button class="button secondary" type="button" data-certificate="${E(a.id)}">Download participation certificate (PDF)</button>`;
        return external(a.document_url, 'Participation certificate (PDF)', 'button secondary');
    }
    function achievementCard(a, teaser = false) {
        const researcher = one('people', a.researcher_id);
        const preview = a.certificate_preview && /^data:image\/(jpeg|png);base64,/.test(a.certificate_preview) ? a.certificate_preview : '';
        if (teaser) return `<article class="recognition-teaser"><div><p class="eyebrow">Researcher recognition · ${E(dates(a.date))}</p><h3>${E(a.title)}</h3><p>${E(a.summary)}</p>${link('profiles/' + a.researcher_id + '?section=recognition', 'Read the achievement & view the certificate →', 'text-link')}</div>${preview ? `<a class="certificate-thumb" href="#/profiles/${E(a.researcher_id)}?section=recognition" aria-label="View ${E(researcher?.name || '')}’s certificate"><img src="${E(preview)}" alt="Falling Walls participation certificate supplied by the researcher" loading="lazy"></a>` : ''}</article>`;
        return `<article class="achievement-card" id="achievement-${E(a.id)}"><p class="eyebrow">${E(dates(a.date))}</p><h3>${E(a.title)}</h3><p>${E(a.summary)}</p><div class="certificate-layout">${preview ? `<figure class="certificate-preview"><img src="${E(preview)}" alt="Participation certificate naming Paulus Hamutenya, Falling Walls Lab Windhoek, Namibia, 25 August 2026" loading="lazy"><figcaption>Preview of the supplied certificate. The PDF preserves the original document.</figcaption></figure>` : ''}<div class="certificate-info"><h4>Participation certificate</h4><p>${E(a.evidence_note)}</p><div class="actions">${certificateButton(a)}</div></div></div></article>`;
    }
    function homeRecognition() {
        const selected = rows('achievements').filter(a => a.homepage);
        return selected.length ? `<section class="section recognition-section" id="recognition"><div class="container">${selected.map(a => achievementCard(a, true)).join('')}</div></section>` : '';
    }
    function activity(id) {
        if (id) {
            const a = one('announcements', id);
            if (!a) return notFound();
            const team = (a.people || []).map(pid => one('people', pid)).filter(Boolean);
            return page('Laboratory activity', a.title, dates(a.start_date, a.end_date), `<div class="activity-detail">${announcementCard(a)}${a.host ? `<p class="activity-host"><strong>Host:</strong> ${E(a.host)}${a.location ? `<br><strong>Location:</strong> ${E(a.location)}` : ''}</p>` : ''}${a.date_status === 'date-conflict' ? `<div class="date-discrepancy"><strong>Date discrepancy:</strong> laboratory schedule ${E(dates(a.start_date, a.end_date))}; host-published call ${E(dates(a.official_start_date, a.official_end_date))}. Confirmation remains pending.</div>` : ''}${team.length ? `<section class="content-section"><h2>Presenting researchers</h2><div class="person-grid">${team.map(personCard).join('')}</div></section>` : ''}${link('activity', '← All activity', 'text-link')}</div>`, true);
        }
        const future = rows('announcements').filter(upcoming).sort(byDate), past = rows('announcements').filter(a => !upcoming(a)).sort((a, b) => byDate(b, a));
        return page('Laboratory activity', 'Presentations, exchange & recognition.', 'Upcoming presentations, seminar announcements and documented researcher milestones.', `<section class="content-section"><h2>Upcoming activities</h2><div class="event-list">${future.map(a => announcementCard(a)).join('') || empty('No upcoming activities published.', 'New approved notices will appear here.')}</div></section>${past.length ? `<section class="content-section"><h2>Past activity</h2><div class="event-list">${past.map(a => announcementCard(a)).join('')}</div></section>` : ''}${rows('achievements').length ? `<section class="content-section"><h2>Researcher recognition</h2>${rows('achievements').map(a => achievementCard(a, true)).join('')}</section>` : ''}`, true);
    }

    function updateCard(p) { return `<article class="record-card"><p class="eyebrow">${E(p.date)} · ${E(nice(p.kind))}</p><h3>${E(p.title)}</h3><p class="profile-text">${E(p.text)}</p></article>`; }
    function publicBioSection(title, html, id) { return `<section class="content-section" id="${E(id)}"><h2>${E(title)}</h2>${html}</section>`; }
    function home() {
        const s = rows('settings')[0] || {};
        const caps = [...rows('capabilities')].sort((a, b) => (a.order || 0) - (b.order || 0));
        const capCards = list => list.map((r, i) => `<article class="research-card" id="${E(r.id)}"><span class="research-number">${String(r.order || i + 1).padStart(2, '0')}</span><h3>${E(r.title)}</h3><p>${E(r.text)}</p></article>`).join('');
        const roster = group => rows('people').filter(p => p.group === group).map(p => `<a class="roster-link" href="#/profiles/${E(profileSlugs[p.id] || p.id)}">${avatar(p, 'small')}<span>${E(p.name)}</span><span class="arrow" aria-hidden="true">↗</span></a>`).join('');
        return `<section class="hero"><div class="container hero-grid"><div><p class="eyebrow">TED² · University of Namibia</p><h1>${E(s.hero_title || 'Engineering better biomedical solutions.')}</h1><p class="lead">${E(s.hero_intro)}</p><div class="actions">${link('researchers', 'Meet our researchers →', 'button')}${link('research', 'Explore research', 'button secondary')}</div><div class="hero-meta"><span><strong>Research.</strong> Translation.</span><span><strong>Biomedical</strong> innovation.</span></div></div><div class="hero-visual"><div class="hero-photo media-frame image-failed"><div class="media-fallback"><img src="${E(window.TED2_WORDMARK)}" alt=""><span>Tissue engineering · drug development · collaborative research</span></div>${safeURL(s.hero_image_url) ? `<img class="remote-image hero-remote" src="${E(s.hero_image_url)}" alt="Pipetting at a laboratory bench, from the reference laboratory website" fetchpriority="high">` : ''}</div><div class="photo-label"><div><small>From cells to therapeutic platforms</small><br><strong>Research with purpose.</strong></div><span class="photo-number">TED²</span></div></div></div></section>
    <nav class="section-nav" aria-label="Homepage sections"><div class="container"><span>Explore</span><a href="#/?section=alerts">Alerts & events</a><a href="#/?section=research">Research capabilities</a><a href="#/?section=interactions">Cell–material interactions</a><a href="#/?section=scaffolds">Scaffolds & applications</a><a href="#/?section=people">Our people</a></div></nav>
    ${homeAlerts()}
    <section class="section" id="research"><div class="container"><div class="section-head"><div><p class="eyebrow">01 / Research capabilities</p><h2>Understanding life.<br>Designing what comes next.</h2></div></div><div class="research-grid">${capCards(caps.slice(0, 5))}</div></div></section>
    <section class="section section-cream" id="interactions"><div class="container feature-grid"><div class="feature-typeset"><div><p class="eyebrow">02 / Cell–material interactions</p><h2>Better materials.<br>Closer to biology.</h2></div><div class="feature-rule"><span class="feature-mark">2D / 3D</span><p>Adhesion · proliferation · differentiation</p></div></div><div class="topic-list">${caps.slice(5, 9).map(r => `<article class="topic-row"><h3>${E(r.title)}</h3><p>${E(r.text)}</p></article>`).join('')}</div></div></section>
    <section class="section" id="scaffolds"><div class="container"><div class="section-head"><div><p class="eyebrow">03 / Scaffolds & applications</p><h2>Materials designed<br>around biology.</h2></div></div><div class="research-grid">${capCards(caps.slice(9))}</div><div class="split-images">${[[s.materials_image_url, 'Illustrative materials photograph from the reference website.'], [s.microscopy_image_url, 'Illustrative microscopy from the reference website; not TED² experimental data.']].filter(([u]) => safeURL(u)).map(([u, caption]) => `<figure><div class="feature-image media-frame image-failed"><div class="media-fallback"><img src="${E(window.TED2_WORDMARK)}" alt=""><span>Reference photograph unavailable.</span></div><img class="remote-image hero-remote" src="${E(u)}" alt="${E(caption)}" loading="lazy"></div><figcaption class="feature-caption">${E(caption)} ${link('sources', 'Image credits')}</figcaption></figure>`).join('')}</div></div></section>
    <section class="section section-cream" id="people"><div class="container"><div class="section-head"><div><p class="eyebrow">04 / Our people</p><h2>The people behind the questions.</h2><p class="lead">Open an individual profile for selected work, publications and approved research activity.</p></div></div><div class="people-home-grid"><div class="roster-panel"><div class="roster-panel-header"><h3>Researchers</h3><span>${rows('people').filter(p => p.group === 'researcher').length} profiles</span></div>${roster('researcher')}</div><div><div class="roster-panel"><div class="roster-panel-header"><h3>Collaborators</h3><span>${rows('people').filter(p => p.group === 'collaborator').length} profiles</span></div>${roster('collaborator')}</div><div class="directory-callout"><h4>Research has a story.</h4><p>Follow approved active research and manuscript stages, with individual researchers at the centre.</p>${link('pipeline', 'View the manuscript pipeline →', 'text-link')}</div></div></div></div></section>${homeRecognition()}${contact(true)}`;
    }
    function contact(section = false) { const s = rows('settings')[0] || {}; const inner = `<section class="section contact-section" id="contact"><div class="container contact-grid"><div><p class="eyebrow">Visit & connect</p><h2>Good research starts<br>with a conversation.</h2><p>Research enquiries, collaboration discussions and laboratory information.</p></div><dl class="contact-list"><div><dt>Laboratory</dt><dd>${E(s.title)}</dd></div><div><dt>Public contact</dt><dd>${E(s.contact_name)}<br>${s.contact_email ? `<a class="mail-link" href="mailto:${E(s.contact_email)}">${E(s.contact_email)}</a>` : ''}</dd></div><div><dt>Location</dt><dd class="profile-text">${E(s.address)}</dd></div></dl></div></section>`; return section ? inner : head('Contact', 'Connect with the laboratory.') + inner; }
    function researchers() { return page('People', 'Researchers & collaborators.', 'Find a researcher, then explore their work, outputs and published activity.', `<div class="toolbar"><div class="search-control"><label for="directory-search">Search name, role or research interest</label><input id="directory-search" type="search"></div><div class="filter-control"><label for="directory-group">Directory</label><select id="directory-group"><option value="">Everyone</option><option value="researcher">Researchers</option><option value="collaborator">Collaborators</option></select></div></div><p class="results-count" id="results-count"></p><div class="person-grid" id="directory-results"></div>`, true); }
    function publications() { return page('Research outputs', 'Selected publications.', 'Publisher-checked articles and clearly labelled university research records. A selected bibliography, not a complete publication count.', `<div class="toolbar"><div class="search-control"><label for="pub-search">Title, author, year or DOI</label><input id="pub-search" type="search"></div><div class="filter-control"><label for="pub-person">Researcher</label><select id="pub-person"><option value="">All researchers</option>${rows('people').map(p => `<option value="${E(p.id)}">${E(p.name)}</option>`).join('')}</select></div><div class="filter-control"><label for="pub-type">Record type</label><select id="pub-type"><option value="">All records</option>${['peer-reviewed', 'author-listed', 'catalogued', 'preprint', 'chapter'].map(t => `<option value="${E(t)}">${E(nice(t))}</option>`).join('')}</select></div></div><p class="results-count" id="results-count"></p><div id="pub-results"></div>`, true); }
    function profile(id) {
        id = ({'mbotarai-vevangapi':'vevangapi-mbatara','denise-bouman':'denis-bouman','maneria-halweendo':'manelia-halweendo','charity-maepa':'charity-mepa','nonku-phili':'nonku-phiri','jaydine-jeris':'jaydine-feris'})[id] || id;
        const p = one('people', id);
        if (!p)
            return notFound();
        const pubs = rows('publications').filter(x => (x.people || []).includes(id)), projects = rows('projects').filter(x => x.lead_id === id || (x.people || []).includes(id)), manuscripts = rows('manuscripts').filter(x => (x.people || []).includes(id)), collabs = rows('collaborations').filter(x => (x.people || []).includes(id)), updates = rows('updates').filter(x => x.researcher_id === id), notices = rows('announcements').filter(x => (x.people || []).includes(id)).sort(byDate), recognition = rows('achievements').filter(x => x.researcher_id === id);
        return `<section class="page-heading"><div class="container"><div class="breadcrumbs">${link('researchers', 'People')} <span>/</span> Profile</div><div class="profile-top">${avatar(p, 'large')}<div><p class="eyebrow">${E(p.group)} · TED² roster</p><h1>${E(p.name)}</h1><p class="lead">${E(p.role)}</p>${tags(p.topics)}<div class="profile-links">${external(p.scholar_url, 'Google Scholar')}${external(p.researchgate_url, 'ResearchGate')}${external(p.orcid_url, 'ORCID')}${external(p.linkedin_url, 'LinkedIn source')}</div></div></div>${portrait(p) ? `<p class="photo-credit">Portrait: ${E(p.photo_credit)} ${external(p.photo_source_url, 'Attribution source')}${p.photo_permission !== 'approved' ? ' Reuse permission has not been documented.' : ''}</p>` : ''}</div></section>
    <section class="container page-body directory-layout">${side()}<div><nav class="profile-subnav" aria-label="Profile sections">${[['bio', 'Biography'], ['publications', 'Publications'], ['research', 'Active research'], ['pipeline', 'Manuscripts'], ['activity', 'Activity'], ...(recognition.length ? [['recognition', 'Recognition']] : [])].map(([a, t]) => link('profiles/' + id + '?section=' + a, t)).join('')}</nav>
    ${publicBioSection('Biography', `<p class="profile-text">${E(p.bio)}</p>${p.work ? `<h3 style="margin-top:24px">Selected work</h3><p class="profile-text">${E(p.work)}</p>` : ''}${p.note ? `<details class="notice"><summary>Evidence note</summary><p>${E(p.note)}</p></details>` : ''}`, 'bio')}
    ${recognition.length ? publicBioSection('Recognition & certificates', recognition.map(a => achievementCard(a)).join(''), 'recognition') : ''}
    ${publicBioSection('Publications', pubs.length ? pubs.sort((a, b) => b.year - a.year).map(pubCard).join('') : empty('No verified publications added yet.', 'A profile without listed publications is not evidence that the researcher has no outputs.'), 'publications')}
    ${publicBioSection('Active research', projects.length ? `<div class="record-grid">${projects.map(projectCard).join('')}</div>` : empty('No public project updates yet.', 'Private project information is visible only in the authenticated workspace.'), 'research')}
    ${publicBioSection('Manuscript pipeline', manuscripts.length ? `<div class="record-grid">${manuscripts.map(manuscriptCard).join('')}</div>` : empty('No manuscript status published.', 'Drafts and reviewer correspondence are private unless an administrator approves a public status.'), 'pipeline')}
    ${publicBioSection('Collaborations', collabs.length ? `<div class="record-grid">${collabs.map(collabCard).join('')}</div>` : empty('No collaboration record assigned.', 'Verified relationships can be added by a laboratory administrator.'), 'collaborations')}
    ${publicBioSection('Research activity', (notices.length || updates.length) ? `<div class="event-list">${notices.map(a => announcementCard(a)).join('')}</div>` + (updates.length ? `<div class="record-grid">${updates.sort((a, b) => (b.date || '').localeCompare(a.date || '')).map(updateCard).join('')}</div>` : '') : empty('No public activity posts yet.', 'Approved updates will appear here as the researcher’s work progresses.'), 'activity')}
    </div></section>`;
    }
    function research(id) {
        if (!id)
            return page('Research in progress', 'Active research.', 'Approved projects, research teams and progress updates.', rows('projects').length ? `<div class="record-grid">${rows('projects').map(projectCard).join('')}</div>` : empty('The project directory is ready.', 'No active project or progress percentage has been published. Administrators can create projects and assign researchers in the management area.'), true);
        const p = one('projects', id);
        if (!p)
            return notFound();
        const team = [...new Set([p.lead_id, ...(p.people || [])])].map(id => one('people', id)).filter(Boolean);
        const milestones = rows('milestones').filter(m => m.project_id === id);
        const funds = (p.funders || []).map(id => one('funders', id)).filter(Boolean);
        const collabs = (p.collaborators || []).map(id => one('collaborations', id)).filter(Boolean);
        return page('Research project', p.title, p.summary, `${projectCard(p)}${publicBioSection('Research team', `<div class="person-grid">${team.map(personCard).join('')}</div>`, 'team')}${publicBioSection('Approved milestones', milestones.length ? milestones.map(m => `<article class="record-card"><span class="chip">${E(nice(m.status))}</span><h3>${E(m.title)}</h3><p>${E(m.summary)}</p></article>`).join('') : empty('No public milestones.', 'Detailed task tracking is maintained in the private workspace.'), 'milestones')}${publicBioSection('Collaborations', collabs.length ? collabs.map(collabCard).join('') : empty('None published.', 'No collaboration has been linked to this project.'), 'partners')}${publicBioSection('Funding acknowledgements', funds.length ? funds.map(funderCard).join('') : empty('None published.', 'No funder has been linked to this project.'), 'funding')}`, true);
    }
    function pipeline() { const all = rows('manuscripts'); return page('Research outputs in progress', 'The manuscript pipeline.', 'Only approved titles and statuses appear here. Review notes, submission references and draft PDFs are never part of this public view.', all.length ? `<div class="stage-board">${[['Preparation', ['idea', 'drafting', 'internal-review']], ['Submitted & under review', ['submitted', 'under-review']], ['Revisions', ['revisions']], ['Accepted & published', ['accepted', 'published']]].map(([name, stages]) => { const ps = all.filter(p => stages.includes(p.stage)); return `<section class="stage-column"><h2>${E(name)}</h2><p class="stage-count">${ps.length} manuscript${ps.length === 1 ? '' : 's'}</p>${ps.map(manuscriptCard).join('')}</section>`; }).join('')}</div>` : empty('No manuscript statuses published yet.', 'The preparation, submission, review, revision and publication stages become visible as approved records are added.')); }
    function collaborations(id) {
        if (!id)
            return page('Collaboration', 'Working across disciplines.', 'Documented laboratory relationships and collaborator profiles; historical reports are labelled as such.', `<div class="record-grid">${rows('collaborations').map(collabCard).join('')}</div><section class="content-section"><h2>Collaborator profiles</h2><div class="person-grid">${rows('people').filter(p => p.group === 'collaborator').map(personCard).join('')}</div></section>`, true);
        const p = one('collaborations', id);
        if (!p)
            return notFound();
        return page('Collaboration', p.title, p.partner, `<div class="body-copy"><p class="eyebrow">${E(p.period)}</p><p>${E(p.summary)}</p><p class="profile-text">${E(p.detail)}</p><p class="notice">${E(p.note)}</p>${external(p.source_url, 'Read the source report')}<h2>Named researchers</h2><div class="person-grid">${(p.people || []).map(id => one('people', id)).filter(Boolean).map(personCard).join('')}</div></div>`, true);
    }
    function funderCard(f) { return `<article class="record-card"><p class="eyebrow">Funding acknowledgement</p><h3>${E(f.name)}</h3><p>${E(f.summary)}</p>${f.award_reference ? `<p>${E(f.award_reference)}</p>` : ''}<div class="actions">${external(f.website, 'Funder website')}${external(f.source_url, 'Evidence')}</div></article>`; }
    function funders() { return page('Research support', 'Funders & acknowledgements.', 'Approved funding relationships and acknowledgements, linked to the research they support.', rows('funders').length ? `<div class="record-grid">${rows('funders').map(funderCard).join('')}</div>` : empty('No current funder records published.', 'Historical funding mentioned in collaboration reports has not been converted into a current grant or sponsorship claim.'), true); }
    function sources() { return page('Provenance', 'Sources & image credits.', 'Researcher attribution, bibliographic evidence and image provenance.', `<div class="notice"><strong>Content review: ${E(rows('settings')[0]?.reviewed || 'not recorded')}.</strong> Eleven portraits, team roles and postgraduate research topics were supplied in Team.pptx (slides 2–4). The photographs are bundled locally and embedded in the public snapshot. Prof Nailoke Pauline Kadhila is not pictured in that presentation; her existing remotely linked portrait is retained. Owner-supplied photographs do not imply an open reuse licence.</div><section class="source-row" id="image-cells"><h2>Cell photograph removed</h2><p>The previously displayed grayscale cell photograph has been removed. The homepage now uses a typographic cell–material research panel instead.</p></section><section class="source-row"><h2>Logos and laboratory photography</h2><p>TED² and UNAM marks were extracted from the owner-supplied document, not redrawn. They remain subject to institutional brand permissions. The homepage and supporting materials/microscopy photographs link to the original reference website and may be unavailable offline. The supporting images are illustrative, not claimed to be TED² experimental results.</p>${external(rows('settings')[0]?.hero_image_source, 'Reference photograph source')}<p>${E(rows('settings')[0]?.materials_image_credit)}</p><p>${E(rows('settings')[0]?.microscopy_image_credit)}</p></section>${rows('people').filter(p => portrait(p)).map(p => `<section class="source-row"><h2>${E(p.name)} — portrait</h2><p>${E(p.photo_credit)} Permission: ${E(nice(p.photo_permission))}.</p>${external(p.photo_source_url, 'Named source page')}</section>`).join('')}${rows('sources').map(s => `<section class="source-row" id="source-${E(s.id)}"><h2>${E(s.title)}</h2><p>${E(s.kind)} · ${E(s.note)}</p>${external(s.url, 'Open source')}</section>`).join('')}`, true); }
    function access() {
        const base = safeURL(cfg.apiBase);
        if (cfg.live) {
            const root = base ? base.replace(/\/$/, '') : location.origin;
            return page('Staff access', 'A dedicated research workspace.', 'Sign in to manage approved public content and private research activity.', `<div class="record-grid"><article class="record-card"><p class="eyebrow">Owners & administrators</p><h2>Manage the laboratory website.</h2><p>Profiles, uploads, research projects, funders, publishing controls and researcher assignments.</p><div class="actions">${external(root + '/admin', 'Open administration', 'button')}</div></article><article class="record-card"><p class="eyebrow">Research team</p><h2>Track your own research.</h2><p>Assigned projects, weighted milestones, private manuscript stages and progress updates.</p><div class="actions">${external(root + '/workspace', 'Open researcher workspace', 'button')}</div></article></div>`);
        }
        return page('Staff access', 'Management requires the server application.', 'This is the standalone public edition. It contains no admin password, private drafts or hidden researcher data.', `<div class="notice"><p>The complete website package contains the authenticated management application. Start it with <code>python start.py</code>, create the first owner, then use the local administration page. For a live internet workspace, deploy that application behind HTTPS.</p><p>After deployment, download the <strong>Connected public page</strong> from Administration → Publish & export, and replace this repository’s <code>index.html</code>. Public updates will then load from the server, while the admin accounts and private records remain there.</p></div>`);
    }
    function notFound() { return page('Page not found', 'This page is not available.', 'It may have been unpublished, renamed or not added yet.', link('researchers', 'Browse the researcher directory →', 'button')); }
    function wireImages() { main.querySelectorAll('.profile-image').forEach(img => { const fallback = () => img.remove(); img.addEventListener('error', fallback, { once: true }); if (img.complete && !img.naturalWidth)
        fallback(); }); main.querySelectorAll('.hero-remote').forEach(img => { const show = () => img.closest('.media-frame').classList.remove('image-failed'); img.addEventListener('load', show, { once: true }); if (img.complete && img.naturalWidth)
        show(); }); }
    function bindSearch(path) {
        if (path === 'researchers') {
            const q = document.getElementById('directory-search'), g = document.getElementById('directory-group');
            const update = () => { const text = q.value.toLowerCase(); const found = rows('people').filter(p => (!g.value || p.group === g.value) && [p.name, p.role, ...(p.topics || [])].join(' ').toLowerCase().includes(text)); document.getElementById('directory-results').innerHTML = found.map(personCard).join('') || empty('No matching profiles.', 'Try a different name or research interest.'); document.getElementById('results-count').textContent = `${found.length} profiles`; wireImages(); };
            q.addEventListener('input', update);
            g.addEventListener('change', update);
            update();
        }
        if (path === 'publications') {
            const q = document.getElementById('pub-search'), p = document.getElementById('pub-person'), t = document.getElementById('pub-type');
            const update = () => { const text = q.value.toLowerCase(); const found = rows('publications').filter(x => (!p.value || (x.people || []).includes(p.value)) && (!t.value || x.type === t.value) && [x.title, x.year, x.doi, ...(x.authors || [])].join(' ').toLowerCase().includes(text)).sort((a, b) => b.year - a.year); document.getElementById('pub-results').innerHTML = found.map(pubCard).join('') || empty('No matching records.', 'Change the author or record-type filter.'); document.getElementById('results-count').textContent = `${found.length} publication records`; };
            q.addEventListener('input', update);
            p.addEventListener('change', update);
            t.addEventListener('change', update);
            update();
        }
    }
    function render() {
        const hash = location.hash.replace(/^#\/?/, '');
        const [path, query = ''] = hash.split('?');
        const bits = path.split('/').filter(Boolean);
        const section = new URLSearchParams(query).get('section');
        const route = bits[0] || '';
        nav.innerHTML = [['', 'Home'], ['researchers', 'Researchers'], ['publications', 'Publications'], ['research', 'Research'], ['pipeline', 'Pipeline'], ['activity', 'Activity'], ['collaborators', 'Collaborations']].map(([u, t]) => `<a href="#/${u}"${route === u ? ' aria-current="page"' : ''}>${t}</a>`).join('');
        nav.classList.remove('open');
        document.getElementById('menu-toggle').setAttribute('aria-expanded', 'false');
        main.innerHTML = route === '' ? home() : route === 'researchers' ? researchers() : route === 'publications' ? publications() : ['profiles', 'profile'].includes(route) ? profile(bits[1]) : route === 'research' ? research(bits[1]) : route === 'pipeline' ? pipeline() : route === 'activity' ? activity(bits[1]) : ['collaborations', 'collaborators', 'projects'].includes(route) ? collaborations(bits[1]) : route === 'funders' ? funders() : route === 'sources' ? sources() : route === 'contact' ? contact() : route === 'access' ? access() : notFound();
        wireImages();
        bindSearch(route);
        document.title = (main.querySelector('h1')?.textContent || 'Research') + ' | TED² Laboratory';
        if (section) {
            requestAnimationFrame(() => document.getElementById(section)?.scrollIntoView());
        }
        else
            window.scrollTo(0, 0);
    }
    main.addEventListener('click', e => {
        const button = e.target.closest('[data-certificate]');
        if (!button) return;
        const record = one('achievements', button.dataset.certificate);
        const value = record?.document_url || '';
        if (!value.startsWith('data:application/pdf;base64,')) return;
        try {
            const binary = atob(value.slice('data:application/pdf;base64,'.length));
            const bytes = Uint8Array.from(binary, c => c.charCodeAt(0));
            const url = URL.createObjectURL(new Blob([bytes], {type: 'application/pdf'}));
            const a = document.createElement('a');
            a.href = url;
            a.download = record.certificate_filename || 'participation-certificate.pdf';
            document.body.appendChild(a); a.click(); a.remove();
            setTimeout(() => URL.revokeObjectURL(url), 60000);
        } catch { toast('The certificate could not be opened. Please contact the laboratory.'); }
    });
    main.addEventListener('click', async (e) => { const b = e.target.closest('[data-copy]'); if (!b)
        return; const p = one('publications', b.dataset.copy); if (!p)
        return; const text = `${(p.authors || []).join('; ')} (${p.year}). ${p.title} ${p.venue}${p.volume ? ', ' + p.volume : ''}${p.number ? ', ' + p.number : ''}.${p.doi ? ' https://doi.org/' + p.doi : ''}`; try {
        await navigator.clipboard.writeText(text);
        toast('Citation copied.');
    }
    catch {
        const t = document.createElement('textarea');
        t.value = text;
        main.appendChild(t);
        t.select();
        const ok = document.execCommand('copy');
        t.remove();
        toast(ok ? 'Citation copied.' : 'Clipboard unavailable. Copy the citation from the publication record.');
    } });
    document.getElementById('menu-toggle').addEventListener('click', () => { const open = nav.classList.toggle('open'); document.getElementById('menu-toggle').setAttribute('aria-expanded', String(open)); });
    async function start() { if (cfg.live) {
        try {
            const response = await fetch((cfg.apiBase || '') + '/api/public', { credentials: 'omit', cache: 'no-store', signal: AbortSignal.timeout(15000) });
            if (!response.ok)
                throw Error();
            data = await response.json();
            document.getElementById('freshness').textContent = 'Live public content · refreshed ' + new Date().toLocaleString();
        }
        catch {
            main.innerHTML = page('Connection unavailable', 'The research server could not be reached.', 'Please try again shortly. Private records are not stored in this public file.', `<button class="button" id="retry">Try again</button>`);
            document.getElementById('retry').addEventListener('click', () => location.reload());
            document.getElementById('freshness').textContent = 'Live connection unavailable';
            return;
        }
    }
    else
        document.getElementById('freshness').textContent = 'Public snapshot · content reviewed ' + (rows('settings')[0]?.reviewed || 'not recorded'); render(); window.addEventListener('hashchange', render); }
    start();
})();
