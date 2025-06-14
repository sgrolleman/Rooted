# database.py
import sqlite3
import os

DATABASE_PATH = "data/rooted.db"
PLANDAGEN = 5  # Aantal dagen vooruit te plannen (nu standaard 5, later uit GUI)
SCHEMA_FILE = "data/sqlite_schema.sql"

class DatabaseHelper:
    def __init__(self, db_path=DATABASE_PATH, schema_file=SCHEMA_FILE):
        self.db_path = db_path
        self.schema_file = schema_file
        self.conn = None

    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Handig: rijen als dicts

    def close(self):
        if self.conn:
            self.conn.close()

    def init_db(self):
        """Maakt database aan met tabellen indien nodig."""
        if not os.path.exists(self.db_path):
            print("[Rooted] 📦 Database nog niet aanwezig. Nieuwe database wordt aangemaakt.")
        else:
            print("[Rooted] 📦 Database aanwezig. Controleren of schema klopt...")

        with open(self.schema_file, "r") as f:
            schema_sql = f.read()

        with self.conn:
            self.conn.executescript(schema_sql)
            print("[Rooted] ✅ Database-structuur gecontroleerd en zo nodig aangemaakt.")

    def check_schema(self):
        """
        Controleert of alle tabellen en kolommen aanwezig zijn.
        Voegt ontbrekende kolommen automatisch toe als failsafe.
        """
        required_tables = ["project", "taak", "template", "template_stap", "dag_afsluiting"]
        cursor = self.conn.cursor()
        for table in required_tables:
            cursor.execute("""
                SELECT name FROM sqlite_master WHERE type='table' AND name=?;
            """, (table,))
            result = cursor.fetchone()
            if not result:
                print(f"[Rooted] ⚠️ Tabel '{table}' ontbreekt! Wordt opnieuw aangemaakt.")
                with open(self.schema_file, "r") as f:
                    self.conn.executescript(f.read())

        # Failsafe: kolom 'ingepland_vanaf' toevoegen aan 'taak' indien nodig
        cursor.execute("PRAGMA table_info(taak);")
        kolommen = [r[1] for r in cursor.fetchall()]
        if "ingepland_vanaf" not in kolommen:
            print("[Rooted] ➕ Kolom 'ingepland_vanaf' ontbreekt, wordt toegevoegd.")
            cursor.execute("ALTER TABLE taak ADD COLUMN ingepland_vanaf TEXT;")
            self.conn.commit()

    def test_project_tabel(self):
        """
        Test of de project-tabel echt beschikbaar is door een simpele SELECT.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM project;")
            aantal = cursor.fetchone()[0]
            print(f"[Rooted] 🟩 Tabel 'project' beschikbaar ({aantal} rijen).")
        except sqlite3.OperationalError as e:
            print(f"[Rooted] ❌ Fout bij toegang tot tabel 'project': {e}")

    def setup(self):
        """Hoofdfunctie om DB te initialiseren en controleren."""
        self.connect()
        self.init_db()
        self.check_schema()
        self.test_project_tabel()  # Nieuw toegevoegd: test of project-tabel echt werkt
        self.close()


def reset_database(db_path="data/rooted.db"):
    """
    Verwijdert alle data uit actieve tabellen voor testdoeleinden.
    De tabellen zelf blijven bestaan.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Zet hier de tabellen die je wél wilt behouden maar leeg wilt maken
    te_resetten_tabellen = [
        "templates",
        "connections",
        "taken",
        "popup_antwoord",
        "projects"
    ]

    for table in te_resetten_tabellen:
        try:
            cursor.execute(f"DELETE FROM {table}")
            print(f"[✅] Gegevens verwijderd uit tabel: {table}")
        except Exception as e:
            print(f"[⚠️] Kon tabel {table} niet wissen: {e}")

    conn.commit()
    conn.close()
    print("[🧹] Database reset voltooid.")