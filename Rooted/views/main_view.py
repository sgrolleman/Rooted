# views/main_view.py
from datetime import datetime
from templatebuilder.builder_view import TemplateBuilderWindow
from views.focusmode import FocusMode
from utils.project_generator import run_project_creator
from views.taken import TakenDashboard
from data.database import reset_database
from views.taak_editor import TaakEditor
from PySide6.QtWidgets import (
    QMainWindow, QLabel, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QFileDialog, QInputDialog, QMessageBox
)
from PySide6.QtCore import Qt
import os
import json

class RootedApp(QMainWindow):
    def open_taak_editor(self):
        editor = TaakEditor(self)
        editor.exec()

    def open_project_creator(self):
        run_project_creator()
    def open_template_builder(self):
        builder_window = TemplateBuilderWindow()
        builder_window.show()
        # Zorgen dat het niet direct sluit
        self.template_builder_window = builder_window

    def open_focusmode(self):
        popup = FocusMode(self)
        popup.exec()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rooted v1.0")
        self.resize(1000, 600)

        # Hoofd-widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # Hoofd-layout
        main_layout = QVBoxLayout(main_widget)

        # Banner bovenaan
        banner = QLabel(f"<h1>Rooted 🌳</h1><p>{datetime.now().strftime('%A %d-%m-%Y')}</p>")
        banner.setAlignment(Qt.AlignCenter)
        banner.setStyleSheet("background-color: #b7d8c5; font-size: 20px; font-weight: bold;")
        main_layout.addWidget(banner)

        # Hoofdgedeelte: links menu, rechts dashboard
        content_layout = QHBoxLayout()
        main_layout.addLayout(content_layout)

        # Zijmenu
        menu_frame = QFrame()
        menu_frame.setFrameShape(QFrame.StyledPanel)
        menu_layout = QVBoxLayout(menu_frame)
        bovenste_knoppen_layout = QHBoxLayout()
        btn_toevoegen_taak = QPushButton("+ Taak")
        btn_toevoegen_project = QPushButton("+ Project")
        bovenste_knoppen_layout.addWidget(btn_toevoegen_taak)
        bovenste_knoppen_layout.addWidget(btn_toevoegen_project)
        btn_toevoegen_project.clicked.connect(self.open_project_creator)
        menu_layout.addLayout(bovenste_knoppen_layout)

        btn_toevoegen_taak.clicked.connect(self.open_taak_editor)

        # Menu label
        menu_layout.addWidget(QLabel("<b>Menu</b>"))

        # Overige functionaliteiten (optioneel later nog koppelen)
        for func in ["Projecten", "Taken", "Planner", "Focusmode", "Instellingen"]:
            btn = QPushButton(func)
            menu_layout.addWidget(btn)

            if func == "Focusmode":
                btn.clicked.connect(self.open_focusmode)

            if func == "Taken":
                btn.clicked.connect(self.show_taken_dashboard)

        btn_template_builder = QPushButton("Template Builder")
        menu_layout.addWidget(btn_template_builder)
        btn_template_builder.clicked.connect(self.open_template_builder)

        btn_reset_db = QPushButton("⚠️ Reset DB")
        btn_reset_db.clicked.connect(self.reset_database_prompt)
        menu_layout.addWidget(btn_reset_db)

        menu_layout.addStretch()

        # Dashboard
        dashboard_frame = QFrame()
        dashboard_frame.setFrameShape(QFrame.StyledPanel)
        self.dashboard_layout = QVBoxLayout(dashboard_frame)  # self. toegevoegd!
        dashboard_label = QLabel("Dashboard (nog leeg)")
        dashboard_label.setAlignment(Qt.AlignCenter)
        self.dashboard_layout.addWidget(dashboard_label)

        # Voeg toe aan content layout
        content_layout.addWidget(menu_frame, 1)
        content_layout.addWidget(dashboard_frame, 3)

    def show_taken_dashboard(self):
        """
        Toont het sorteerbare Taken-dashboard in het dashboard-frame.
        """
        # Eerst alle widgets uit het dashboard-layout verwijderen
        for i in reversed(range(self.dashboard_layout.count())):
            widget = self.dashboard_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        # Voeg het Taken-dashboard toe
        taken_dashboard = TakenDashboard(self)
        self.dashboard_layout.addWidget(taken_dashboard)

    def reset_database_prompt(self):
        antwoord = QMessageBox.question(
            self, "Reset database?",
            "Weet je zeker dat je alle data wilt verwijderen?",
            QMessageBox.Yes | QMessageBox.No
        )
        if antwoord == QMessageBox.Yes:
            reset_database()
            QMessageBox.information(self, "Reset voltooid", "Alle data is verwijderd.")
