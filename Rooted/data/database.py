import os
import sqlite3

DATABASE_PATH = "data/rooted.db"

class DatabaseHelper:
    @staticmethod
    def init_db():
        # Maak de map 'data' aan als die nog niet bestaat
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # 1. Templates tabel
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS templates (
            template_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            static_score REAL
        )
        """)

        # 2. Taken tabel
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS taken (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_id INTEGER,
            project_id INTEGER,
            priority TEXT,
            deadline DATE,
            category TEXT,
            status TEXT DEFAULT 'open',
            planned_start TIMESTAMP,
            planned_end TIMESTAMP,
            FOREIGN KEY(template_id) REFERENCES templates(template_id)
        )
        """)

        # 3. Focusmode logs
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS focus_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            template_id INTEGER,
            planned_duration INTEGER,
            actual_duration INTEGER,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            interrupted BOOLEAN,
            FOREIGN KEY(task_id) REFERENCES taken(task_id),
            FOREIGN KEY(template_id) REFERENCES templates(template_id)
        )
        """)

        # 4. View: gemiddelde duur per template
        cursor.execute("DROP VIEW IF EXISTS template_durations")
        cursor.execute("""
        CREATE VIEW template_durations AS
        SELECT
            template_id,
            AVG(actual_duration) AS avg_duration,
            COUNT(*) AS n
        FROM focus_logs
        GROUP BY template_id
        """)

        conn.commit()
        conn.close()

# ✅ Nieuwe reset-functie
def reset_database():
    """Verwijdert de hele database en maakt een lege nieuwe aan."""
    if os.path.exists(DATABASE_PATH):
        os.remove(DATABASE_PATH)
    DatabaseHelper.init_db()
