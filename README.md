# TED² Research Workspace

**A laboratory website and research-management studio, built with PHP.**

Manage researchers, publications, milestones, methodology-linked procurement and media in one place. Review the public website locally, then publish an approved static release to GitHub Pages. Private research and account data stay in the management application.

## V6.2 highlights

- Photographic header/footer designs, editable branding and shared light, dark or system appearance.
- Searchable administration, grouped public navigation and responsive researcher pages.
- Researcher-owned uploads, editable captions, ordering, contact details and access rights.
- Source-linked research headlines, topic tags and an administrator-reviewed science-quotation collection.
- Public asset caching and automatic invalidation, without caching private pages or submissions.

## Run locally

Requirements: **PHP 8.3+**, SQLite support, Fileinfo, OpenSSL and Argon2 password support. GD or FFmpeg handles images; FFmpeg is required for video processing. Git and GitHub authentication are required for publishing. C++ utilities are optional.

From the application directory:

```bash
bash start.sh
```

Open `http://127.0.0.1:8000/admin`. The first run asks you to create an owner; existing accounts are preserved. The built-in server is for local development, not public production hosting.

## Documentation

[Setup](docs/SETUP.md) · [Upgrade and recovery](docs/UPGRADE-RECOVERY.md) · [Administration and publishing](docs/OPERATIONS.md) · [Research feeds and image rights](docs/FEEDS-AND-RIGHTS.md) · [Testing](docs/TESTING.md)

**Choose your own installation directory.** Upgrade scripts ask for the existing repository path; no personal folder layout is required.

GitHub Pages hosts the generated public site, not PHP or private administration. Automatic external headlines require an explicit source policy. Anonymous online submissions require a publicly hosted PHP service. Publicly shared files may remain in Git history or visitors’ downloads after removal.
