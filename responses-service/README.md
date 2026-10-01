# Optional always-online visitor responses

GitHub Pages serves static public files; it cannot store an anonymous visitor message itself. This original Worker/D1 service supplies a small separate inbox without exposing the local PHP administrator or copying the laboratory database. The PHP site can also receive responses directly when hosted publicly behind HTTPS.

## One-time setup

Use the **installed V7 repository**, not the extracted upgrade folder. You need a Cloudflare account, permission to create Workers and D1, and current supported Node.js/npm (Node 20.19+ or 22.12+). Review the provider's current quotas, terms and any costs; no free or unlimited-service guarantee is made.

```bash
bash responses-service/setup.sh
```

Type `DEPLOY`, choose a unique lowercase service name and approve the browser login. The script uses the Wrangler 4 CLI, looks for an existing matching database, creates one only when absent, applies an idempotent schema, generates a private administrator key and deploys the Worker. The Worker is closed until the owner configures it. Reusing the same name recovers its database; do not choose a new name merely to retry a temporary connection error.

Copy the printed HTTPS `workers.dev` address and private key into **Visitor inbox → Connection & deployment settings**. Select **Save & connect**. The backend synchronizes the exact public website origin, enabled flag and published researcher labels. A loopback preview origin is permitted for your local form; no wildcard origin is used. The current version accepts standard `service.account.workers.dev` addresses, not arbitrary custom domains.

Republish the public website once. Visit its **Connect** page, submit a test question, save the reply key, answer from Visitor inbox and verify the reply as a visitor. This end-to-end live check is necessary; deployment success alone does not prove the endpoint was published correctly.

## Security and control

- No account is required for the visitor. Message and reply stay private unless the visitor grants public sharing and an administrator approves it.
- A cryptographically random response key grants access to that one conversation; store it like a password. Only its hash is stored. Keys never enter URLs, localStorage or Git.
- Administrative access uses a server-held bearer key. Never paste this key into a public form, issue, Git file or browser theme setting. Generated keys/configuration stay under ignored `var/community-deploy/`.
- Signed one-use challenges, a honeypot, bounded JSON bodies, prepared SQL, exact-origin CORS and per-client rate limits reduce abuse. These measures are not a full bot-detection or anti-DDoS guarantee.
- Messages contain no collected IP, email or account identity. Short-lived IP-derived limiter keys expire. Hosting providers can still process network metadata; free text may identify a visitor. This is not a promise of absolute anonymity.
- The inbox is capped at 5,000 messages, with latest 200 listed. Establish retention and export/backup policy through the provider before production use. Deleting a record does not erase provider backups or a visitor's saved copies.
- No patient data or sensitive laboratory results should be submitted. This is not a clinical consultation service.

## Updates and recovery

Changing researcher labels or enabling/disabling responses requires **Synchronize public researcher options**. Changing the endpoint also requires a new public website publication. Existing local messages are not moved into the cloud database. The original local inbox reappears when the gateway endpoint is cleared.

Run setup again with the same name to update source/schema without replacing existing D1 messages. Keep a private backup of the key and configuration. To rotate a compromised key, replace `ADMIN_TOKEN` with Wrangler and update the local stored service key; public visitors never need that administrator key. Redeploy/rotate only as an explicit owner action.

The exact supported commands are documented at https://developers.cloudflare.com/workers/wrangler/commands/d1/ . D1 `list` and `info` support `--json`; `create` does not. See also https://developers.cloudflare.com/d1/get-started/ .

The package tests exercise the Worker handler with real SQLite SQL locally. They do not claim that your Cloudflare account has been connected or that a Worker is already online.
