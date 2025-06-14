import sqlite3
from datetime import datetime
from utils.task_manager import start_vervolgtaak

DATABASE_PATH = "data/rooted.db"

def handle_task_completion(task_id: str, db_path: str = DATABASE_PATH):
    """
    Verwerkt de afronding van een taak:
    - Markeert de taak als afgerond.
    - Zoekt vervolgverbindingen op vanuit de templates.
    - Activeert/verwerkt de vervolgblokken via task_manager.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1️⃣ Markeer taak als afgerond
    cursor.execute("""
        UPDATE taken SET status = 'afgerond'
        WHERE task_id = ?
    """, (task_id,))
    conn.commit()
    print(f"[Rooted] ✅ Taak ID {task_id} gemarkeerd als afgerond.")

    # 2️⃣ Haal bijbehorende template_id en project_id op
    cursor.execute("""
        SELECT template_id, project_id FROM taken
        WHERE task_id = ?
    """, (task_id,))
    row = cursor.fetchone()
    if not row:
        print(f"[⚠️] Geen gegevens gevonden voor taak {task_id}")
        conn.close()
        return

    template_id = row["template_id"]
    project_id = row["project_id"]

    # 3️⃣ Zoek alle connecties vanuit deze template
    cursor.execute("""
        SELECT target_id, label FROM connections
        WHERE source_id = ? AND project_id = ?
    """, (template_id, project_id))
    connections = cursor.fetchall()

    if not connections:
        print("[🎉] Geen vervolgblokken – einde van deze flow.")
        conn.close()
        return

    # 4️⃣ Verwerk elke vervolgtemplate
    for conn_row in connections:
        target_template_id = conn_row["target_id"]
        print(f"[➡️] Start verwerking vervolgblok: {target_template_id}")
        start_vervolgtaak(target_template_id, project_id, db_path)

    conn.close()
