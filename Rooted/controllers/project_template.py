import sqlite3
import uuid
from datetime import date

DB_PATH = "data/rooted.db"

def prepare_project_from_template(template_json):
    """
    🏗️ Zet alle taken en connecties in de database (status='inactief').
    Dit gebeurt direct na het kiezen van de template.
    """

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Taken opslaan
        blocks = template_json["blocks"]
        uid_to_taak_id = {}

        for block in blocks:
            taak_type = block["type"]
            naam = block.get("name", block.get("question", "Onbekend"))
            template_id = block.get("uid")
            verwachte_duur = block.get("duration") if taak_type == "taak" else None
            wachttijd_duur = block.get("delay") if taak_type == "wachttijd" else None

            taak_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO taak (id, naam, type, status, template_id, verwachte_duur, wachttijd_duur)
                VALUES (?, ?, ?, 'inactief', ?, ?, ?)
            """, (taak_id, naam, taak_type, template_id, verwachte_duur, wachttijd_duur))
            taak_id = cursor.lastrowid
            uid_to_taak_id[str(template_id)] = taak_id
            print(f"[Rooted] ✅ {taak_type.capitalize()} '{naam}' toegevoegd (taak_id={taak_id}).")

        # Connecties opslaan
        connections = template_json["connections"]
        for conn_data in connections:
            source_uid = str(conn_data["source_id"])
            target_uid = str(conn_data["target_id"])
            label = conn_data.get("label", "")

            source_taak_id = uid_to_taak_id.get(source_uid)
            target_taak_id = uid_to_taak_id.get(target_uid)
            if not source_taak_id or not target_taak_id:
                continue

            cursor.execute("""
                SELECT id FROM taak_connectie
                WHERE source_taak_id=? AND target_taak_id=?
            """, (source_taak_id, target_taak_id))
            if cursor.fetchone():
                continue

            cursor.execute("""
                INSERT INTO taak_connectie (source_taak_id, target_taak_id, label)
                VALUES (?, ?, ?)
            """, (source_taak_id, target_taak_id, label))
            print(f"[Rooted] 🔗 Connectie: {source_taak_id} ➡️ {target_taak_id} (label='{label}')")

    print("\n[Rooted] ✅ Template-taken en connecties voorbereid. Starttaak kan nu in GUI getoond worden!")


def start_project_from_template(template_json):
    """
    🚀 Wordt pas aangeroepen nadat de starttaak in de GUI beantwoord is.
    Zet op basis van popup_antwoord de projectflow op!
    """

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 1️⃣ Starttaak vinden in JSON
        start_template_id = None
        for block in template_json["blocks"]:
            if block["type"] == "start":
                start_template_id = block["uid"]
                break
        if not start_template_id:
            print("[Rooted] ❌ Geen starttaak gevonden in template – proces gestopt.")
            return
        print(f"[Rooted] ✅ Starttaak gevonden met template_id={start_template_id}.")

        # 2️⃣ Antwoord op starttaak ophalen → projectnaam
        cursor.execute("""
            SELECT antwoord FROM popup_antwoord
            WHERE taak_id=?
            ORDER BY tijdstip DESC
            LIMIT 1
        """, (start_template_id,))
        row = cursor.fetchone()
        if not row:
            print("[Rooted] ❌ Geen antwoord op starttaak gevonden – proces gestopt.")
            return
        project_naam = row["antwoord"]

        # 3️⃣ Project aanmaken
        cursor.execute("""
            INSERT INTO project (naam, startdatum)
            VALUES (?, ?)
        """, (project_naam, str(date.today())))
        project_id = cursor.lastrowid
        print(f"[Rooted] ✅ Project '{project_naam}' aangemaakt (project_id={project_id}).")

        # 4️⃣ Koppel alle taken aan het project_id
        cursor.execute("""
            UPDATE taak SET project_id=?
            WHERE project_id IS NULL
        """, (project_id,))
        conn.commit()
        print("[Rooted] ✅ Alle taken gekoppeld aan het project.")

        # 5️⃣ Starttaak afronden
        cursor.execute("""
            UPDATE taak SET status='afgerond'
            WHERE template_id=? AND project_id=?
        """, (start_template_id, project_id))
        conn.commit()
        print("[Rooted] ✅ Starttaak afgerond.")

        # 6️⃣ Vervolgtaken activeren
        cursor.execute("""
            SELECT target_taak_id FROM taak_connectie
            WHERE source_taak_id=?
        """, (start_template_id,))
        vervolg_ids = [r["target_taak_id"] for r in cursor.fetchall()]
        if not vervolg_ids:
            print("[Rooted] 🎉 Geen vervolgtaken – project direct afgerond.")
            return

        for target_template_id in vervolg_ids:
            cursor.execute("""
                SELECT id, naam, type FROM taak
                WHERE project_id=? AND template_id=?
            """, (project_id, target_template_id))
            next_taak = cursor.fetchone()
            if not next_taak:
                print(f"[Rooted] ⚠️ Geen vervolgtaak gevonden (template_id={target_template_id}).")
                continue

            cursor.execute("""
                UPDATE taak SET status='actief'
                WHERE id=?
            """, (next_taak["id"],))
            conn.commit()
            print(f"[Rooted] ▶️ '{next_taak['naam']}' (type={next_taak['type']}) nu actief.")

            # TODO: Type-specifieke acties aanroepen

    print("\n[Rooted] ✅ Projectflow gestart op basis van popup-antwoord!")

