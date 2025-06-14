import sqlite3
import uuid

def maak_starttaak(template_id: str, project_id: str, db_path: str):
    """
    Maakt een starttaak aan, markeert deze als afgerond,
    en triggert direct verwerking van de vervolgstap.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Haal de template-informatie op
    cursor.execute("""
        SELECT name, duration, schema, type
        FROM templates
        WHERE template_id = ? AND project_id = ?
    """, (template_id, project_id))
    row = cursor.fetchone()

    if not row:
        print(f"[❌] Template {template_id} niet gevonden voor project {project_id}")
        conn.close()
        return None

    name, duration, schema, taak_type = row

    task_id = str(uuid.uuid4())

    # Voeg taak toe met status 'afgerond'
    cursor.execute("""
        INSERT INTO taken (
            task_id, template_id, project_id, task_name,
            duration, schema, stage,
            start_date, deadline_date, deadline_type,
            status, type
        ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, ?, ?)
    """, (
        task_id,
        template_id,
        project_id,
        name,
        duration or 15,
        schema or "default",
        "init",
        "afgerond",  # ← direct afronden
        taak_type or "taak"
    ))
    conn.commit()
    conn.close()

    print(f"[🆕] Starttaak aangemaakt én afgerond: {name} (template_id={template_id})")

    # Verwerk vervolgtaken automatisch
    from utils.task_manager import verwerk_afgeronde_taak
    verwerk_afgeronde_taak(task_id, db_path)

    return task_id