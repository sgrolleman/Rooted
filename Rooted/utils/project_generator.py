# project_generator.py
import os
import uuid
import sqlite3
import json
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QInputDialog, QMessageBox
)

def run_project_creator():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    templates_dir = os.path.join(os.getcwd(), "data", "templates")
    template_path, _ = QFileDialog.getOpenFileName(
        None, "Kies een template", templates_dir, "JSON-bestanden (*.json)"
    )
    if not template_path:
        return

    project_name, ok = QInputDialog.getText(None, "Nieuw Project", "Voer de projectnaam in:")
    if not ok or not project_name.strip():
        QMessageBox.warning(None, "Ongeldig", "Geen geldige projectnaam ingevoerd.")
        return

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            template_json = json.load(f)

        db_path = os.path.join(os.getcwd(), "data", "rooted.db")
        project_id = str(uuid.uuid4())

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 1️⃣ Project toevoegen
        cursor.execute("""
            INSERT INTO projects (project_id, project_name, project_code, status, datum_afgerond)
            VALUES (?, ?, ?, 'lopend', NULL)
        """, (project_id, project_name, template_json.get("project_code", "")))

        # 2️⃣ Blokken uit template toevoegen
        for block in template_json["blocks"]:
            cursor.execute("""
                INSERT INTO templates (
                    project_id, template_id, type, name, question, answer_type,
                    options, duration, delay, schema, pos_x, pos_y, color,
                    set_field, set_target, set_target_uid
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                project_id,
                block.get("uid"),
                block.get("type"),
                block.get("name"),
                block.get("question"),
                block.get("answer_type"),
                json.dumps(block.get("options")) if block.get("options") else None,
                block.get("duration"),
                block.get("delay"),
                block.get("schema"),
                block.get("pos", [None, None])[0],
                block.get("pos", [None, None])[1],
                block.get("color"),
                block.get("set_field"),
                block.get("set_target"),
                block.get("set_target_uid")
            ))

        # 3️⃣ Connecties toevoegen – automatisch dubbele verwijderen
        seen = set()
        for conn_item in template_json.get("connections", []):
            source = conn_item["source_id"]
            target = conn_item["target_id"]
            label = conn_item.get("label", "")
            key = (source, target, label)
            if key in seen:
                continue
            seen.add(key)
            conn_id = f"{project_id}_{source}->{target}"

            cursor.execute("""
                INSERT INTO connections (connection_id, project_id, source_id, target_id, label)
                VALUES (?, ?, ?, ?, ?)
            """, (
                conn_id,
                project_id,
                source,
                target,
                label
            ))

        conn.commit()

        # 4️⃣ Starttaak zoeken
        start_template_id = None
        for block in template_json["blocks"]:
            if block["type"] == "start":
                start_template_id = block["uid"]
                break

        if not start_template_id:
            QMessageBox.critical(None, "Fout", "Geen starttaak gevonden in template.")
            return

        print(f"[🚀] Starttaak gevonden met uid={start_template_id} – verwerken...")

        # 5️⃣ Starttaak toevoegen én direct afronden
        from utils.task_manager import maak_starttaak
        maak_starttaak(start_template_id, project_id, db_path)

        QMessageBox.information(None, "Project aangemaakt",
            f"Project '{project_name}' is succesvol aangemaakt.\n\nProject-ID:\n{project_id}")

    except Exception as e:
        QMessageBox.critical(None, "Fout", f"Er ging iets mis bij het aanmaken van het project:\n{e}")
