CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS messages (
 id TEXT PRIMARY KEY, receipt_hash TEXT NOT NULL, researcher_id TEXT NOT NULL,
 subject TEXT NOT NULL, message TEXT NOT NULL, nickname TEXT NOT NULL,
 consent_public INTEGER NOT NULL DEFAULT 0, reply TEXT NOT NULL DEFAULT '',
 status TEXT NOT NULL DEFAULT 'pending', created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS messages_status ON messages(status,updated_at);
CREATE TABLE IF NOT EXISTS limits (key TEXT PRIMARY KEY, count INTEGER NOT NULL, expires INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS used_challenges (key TEXT PRIMARY KEY, expires INTEGER NOT NULL);
