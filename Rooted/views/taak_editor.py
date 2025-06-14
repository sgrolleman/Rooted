# views/taak_editor.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QTextEdit, QSpinBox, QDateEdit, QPushButton
)
from PySide6.QtCore import QDate
import sqlite3
import uuid

DATABASE_PATH = "data/rooted.db"

class TaakEditor(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nieuwe Taak Toevoegen")
        self.resize(400, 500)

        layout = QVBoxLayout(self)

        # Project dropdown (editable combobox)
        layout.addWidget(QLabel("Project:"))
        self.project_combo = QComboBox()
        self.project_combo.setEditable(True)
        self.load_projects()
        layout.addWidget(self.project_combo)

        # Naam
        layout.addWidget(QLabel("Naam:"))
        self.naam_edit = QLineEdit()
        layout.addWidget(self.naam_edit)

        # Deadline
        layout.addWidget(QLabel("Deadline:"))
        self.deadline_edit = QDateEdit()
        self.deadline_edit.setDate(QDate.currentDate())
        self.deadline_edit.setCalendarPopup(True)
        layout.addWidget(self.deadline_edit)

        # Verwachte duur
        layout.addWidget(QLabel("Verwachte duur (minuten):"))
        self.duur_spin = QSpinBox()
        self.duur_spin.setRange(1, 10000)
        layout.addWidget(self.duur_spin)

        # Prioriteit
        layout.addWidget(QLabel("Prioriteit (1-5):"))
        self.prioriteit_spin = QSpinBox()
        self.prioriteit_spin.setRange(1, 5)
        layout.addWidget(self.prioriteit_spin)

        # Deadline type
        layout.addWidget(QLabel("Deadline type:"))
        self.deadline_type_combo = QComboBox()
        self.deadline_type_combo.addItems(["harde", "zachte", "advies", "geen"])
        layout.addWidget(self.deadline_type_combo)

        # Status
        layout.addWidget(QLabel("Status:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["open", "in behandeling", "afgerond"])
        layout.addWidget(self.status_combo)

        # Tijdschema
        layout.addWidget(QLabel("Tijdschema:"))
        self.tijdschema_combo = QComboBox()
        self.tijdschema_combo.addItems(["werk", "thuis", "beide"])
        layout.addWidget(self.tijdschema_combo)

        # Beschrijving
        layout.addWidget(QLabel("Beschrijving:"))
        self.beschrijving_edit = QTextEdit()
        layout.addWidget(self.beschrijving_edit)

        # Opslaan-knop
        btn_opslaan = QPushButton("Opslaan")
        btn_opslaan.clicked.connect(self.opslaan)
        layout.addWidget(btn_opslaan)

    def load_projects(self):
        """Laadt de projecten in de combobox als 'id - naam'."""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, naam FROM project ORDER BY naam;")
        projecten = cursor.fetchall()
        conn.close()
        for p in projecten:
            self.project_combo.addItem(f"{p[0]} - {p[1]}")
        # Optioneel: placeholder toevoegen
        self.project_combo.setCurrentIndex(-1)

    def opslaan(self):
        # Project ID uit combobox (eerste deel vóór de '-')
        project_text = self.project_combo.currentText()
        if "-" in project_text:
            project_id = int(project_text.split("-")[0].strip())
        else:
            project_id = 0  # fallback

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        taak_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO taak
            (id, project_id, naam, beschrijving, deadline, verwachte_duur, prioriteit,
             deadline_type, deadline_group, status, tijdschema)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, '', ?, ?)
        """, (
            taak_id,
            project_id,
            self.naam_edit.text(),
            self.beschrijving_edit.toPlainText(),
            self.deadline_edit.date().toString("yyyy-MM-dd"),
            int(self.duur_spin.value()),
            int(self.prioriteit_spin.value()),
            self.deadline_type_combo.currentText(),
            self.status_combo.currentText(),
            self.tijdschema_combo.currentText(),
        ))
        conn.commit()
        conn.close()
        self.accept()
