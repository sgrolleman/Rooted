import sqlite3
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QHBoxLayout
)
class TakenDashboard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("<h2>Actieve Taken</h2>"))

        self.table = QTableWidget()
        self.table.setColumnCount(6)  # 1 extra kolom voor de knop
        self.table.setHorizontalHeaderLabels([
            "Taaknaam", "Project", "Deadline", "Duur (min)", "Schema", "Actie"
        ])
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

        self.load_taken()

    def load_taken(self):
        """Laadt alle actieve taken van type 'taak' uit de database."""
        conn = sqlite3.connect("data/rooted.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT task_id, task_name, project_id, deadline_date, duration, schema
            FROM taken
            WHERE type = 'taak' AND status != 'afgerond'
            ORDER BY deadline_date ASC;
        """)
        taken = cursor.fetchall()
        conn.close()

        self.table.setRowCount(len(taken))
        for row, taak in enumerate(taken):
            taak_id, naam, project_id, deadline, duur, schema = taak
            self.table.setItem(row, 0, QTableWidgetItem(naam))
            self.table.setItem(row, 1, QTableWidgetItem(project_id or ""))
            self.table.setItem(row, 2, QTableWidgetItem(deadline or "Geen deadline"))
            self.table.setItem(row, 3, QTableWidgetItem(str(duur)))
            self.table.setItem(row, 4, QTableWidgetItem(schema or "Onbekend"))

            afrond_knop = QPushButton("✅ Afronden")
            afrond_knop.clicked.connect(lambda _, taak_id=taak_id: self.afronden(taak_id))
            self.table.setCellWidget(row, 5, afrond_knop)

    def afronden(self, taak_id):
        """Markeert de taak als afgerond en verwerkt vervolg."""
        print(f"[Rooted] ➡️ Afronden van taak ID {taak_id}...")
        handle_task_completion(taak_id)
        self.load_taken()
