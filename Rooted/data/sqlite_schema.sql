-- Database schema voor Rooted v1.0

-- Tabel voor projecten
CREATE TABLE IF NOT EXISTS project (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    naam TEXT NOT NULL,
    projectcode TEXT,
    startdatum DATE,
    einddatum DATE,
    status TEXT DEFAULT 'open',
    beschrijving TEXT
);

-- Tabel voor taken
CREATE TABLE IF NOT EXISTS taak (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    naam TEXT NOT NULL,
    beschrijving TEXT,
    deadline DATE,
    verwachte_duur INTEGER,
    prioriteit INTEGER,
    deadline_type TEXT,
    deadline_group TEXT,
    status TEXT DEFAULT 'open',
    tijdschema TEXT,
    template_id INTEGER,
    blocked_by TEXT,
    risk_factor REAL,
    leftover INTEGER,
    ingepland_vanaf TEXT,
    type TEXT DEFAULT 'taak',  -- ✅ deze regel toevoegen
    FOREIGN KEY (project_id) REFERENCES project(id),
    FOREIGN KEY (template_id) REFERENCES template(id)
);

-- Tabel voor templates
CREATE TABLE IF NOT EXISTS template (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    naam TEXT NOT NULL,
    beschrijving TEXT
);

-- Tabel voor stappen in een template
CREATE TABLE IF NOT EXISTS template_stap (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    volgorde INTEGER,       -- volgorde of visuele index
    type TEXT,              -- taak, wachttijd, popup
    naam TEXT NOT NULL,
    duur INTEGER,           -- duur in minuten of wachttijd
    blocked_by TEXT,        -- CSV van stap-IDs die deze blokkeren
    FOREIGN KEY (template_id) REFERENCES template(id)
);

-- Tabel voor dag-afsluiting (reflectie/controle aan het einde van de dag)
CREATE TABLE IF NOT EXISTS dag_afsluiting (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    datum DATE UNIQUE NOT NULL,
    opmerkingen TEXT,
    bevestigde_tijd TIME,                -- tijdstip van afsluiten
    analyses_bevestigd BOOLEAN DEFAULT 0 -- 0: nee, 1: ja
);

-- Indexen voor sneller zoeken
CREATE INDEX IF NOT EXISTS idx_projectcode ON project(projectcode);
CREATE INDEX IF NOT EXISTS idx_taak_deadline ON taak(deadline);
CREATE INDEX IF NOT EXISTS idx_taak_status ON taak(status);
