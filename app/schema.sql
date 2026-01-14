BEGIN;

CREATE TABLE IF NOT EXISTS clients (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  external_key TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY,
  client_id INTEGER NOT NULL,
  email TEXT NOT NULL,
  hashed_password TEXT NOT NULL,
  role TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY (client_id) REFERENCES clients(id)
);

CREATE TABLE IF NOT EXISTS documents (
  id INTEGER PRIMARY KEY,
  client_id INTEGER NOT NULL,
  k_number TEXT NOT NULL,
  document_name TEXT NOT NULL,
  document_type TEXT NOT NULL,
  manufacturer_name TEXT NOT NULL,
  manufacturer_address TEXT NOT NULL,
  regulation_number TEXT NOT NULL,
  regulation_name TEXT NOT NULL,
  regulatory_class TEXT NOT NULL,
  product_codes TEXT NOT NULL,
  indications_for_use TEXT NOT NULL,
  version INTEGER NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  full_text TEXT NOT NULL,
  FOREIGN KEY (client_id) REFERENCES clients(id)
);

CREATE TABLE IF NOT EXISTS document_attributes (
  id INTEGER PRIMARY KEY,
  document_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  value_json TEXT NOT NULL,
  FOREIGN KEY (document_id) REFERENCES documents(id)
);

CREATE TABLE IF NOT EXISTS matches (
  id INTEGER PRIMARY KEY,
  query_text TEXT NOT NULL,
  selected_document_id INTEGER NULL,
  candidate_document_ids_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY (selected_document_id) REFERENCES documents(id)
);

CREATE TABLE IF NOT EXISTS audit_events (
  id INTEGER PRIMARY KEY,
  event_type TEXT NOT NULL,
  timestamp TEXT NOT NULL,
  document_id INTEGER NULL,
  match_id INTEGER NULL,
  payload_json TEXT NOT NULL,
  FOREIGN KEY (document_id) REFERENCES documents(id),
  FOREIGN KEY (match_id) REFERENCES matches(id)
);

CREATE TABLE IF NOT EXISTS pdf_files (
  id INTEGER PRIMARY KEY,
  client_id INTEGER NOT NULL,
  file_path TEXT NOT NULL,
  last_modified TEXT NOT NULL,
  document_id INTEGER NOT NULL,
  version INTEGER NOT NULL,
  FOREIGN KEY (client_id) REFERENCES clients(id),
  FOREIGN KEY (document_id) REFERENCES documents(id),
  UNIQUE (client_id, file_path)
);

CREATE TABLE IF NOT EXISTS field_parsing_rules (
  id INTEGER PRIMARY KEY,
  client_id INTEGER NOT NULL,
  field_name TEXT NOT NULL,
  pattern TEXT NOT NULL,
  priority INTEGER NOT NULL,
  FOREIGN KEY (client_id) REFERENCES clients(id)
);

CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
  full_text,
  content='documents',
  content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS documents_ai AFTER INSERT ON documents BEGIN
  INSERT INTO documents_fts(rowid, full_text) VALUES (new.id, new.full_text);
END;

CREATE TRIGGER IF NOT EXISTS documents_au AFTER UPDATE ON documents BEGIN
  INSERT INTO documents_fts(documents_fts, rowid, full_text) VALUES ('delete', old.id, old.full_text);
  INSERT INTO documents_fts(rowid, full_text) VALUES (new.id, new.full_text);
END;

CREATE TRIGGER IF NOT EXISTS documents_ad AFTER DELETE ON documents BEGIN
  INSERT INTO documents_fts(documents_fts, rowid, full_text) VALUES ('delete', old.id, old.full_text);
END;

INSERT OR IGNORE INTO clients (id, name, external_key, created_at)
VALUES (1, 'DemoClient', 'demo-client', datetime('now'));

INSERT OR IGNORE INTO users (id, client_id, email, hashed_password, role, created_at)
VALUES (1, 1, 'demo@client.com', 'not-used', 'editor', datetime('now'));

INSERT OR IGNORE INTO field_parsing_rules (client_id, field_name, pattern, priority)
VALUES
  (1, 'document_name', '^(?:Trade/)?(?:Document|Device) Name\W*(?P<value>.+)$', 1),
  (1, 'k_number', '^(?:510\(k\) Number|Re:)\W*(?P<value>K\d{6}).*$', 1),
  (1, 'regulation_number', '^Regulation Number\W*(?:21\s*CFR\s*)?(?P<value>\d+\.\d+).*$' , 1),
  (1, 'regulation_name', '^Regulation Name\W*(?P<value>.+)$', 1),
  (1, 'regulatory_class', '^Regulatory Class\W*(?P<value>Class\s+[IIVX]+).*$', 1),
  (1, 'product_codes', '^Product Code(?:\(s\))?\W*(?P<value>[A-Z0-9,\s]+).*$' , 1),
  (1, 'manufacturer_name', '^(Sponsor|Applicant|Manufacturer|Submitter Name)\W*(?P<value>.+)$', 1),
  (1, 'manufacturer_name', '^(?P<value>.+?(?:Inc\.?|LLC|Ltd|S\.r\.l\.|S\.A\.|GmbH))$', 2);

COMMIT;
