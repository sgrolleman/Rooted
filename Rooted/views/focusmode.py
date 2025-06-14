# views/focusmode.py
from datetime import datetime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PySide6.QtCore import Qt, QSize


class FocusMode(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Rooted Focusmode")
        self.resize(1200, 800)

        layout = QVBoxLayout(self)

        # Banner
        banner = QLabel(f"<h1>Focusmode</h1><p>{datetime.now().strftime('%A %d-%m-%Y')}</p>")
        banner.setAlignment(Qt.AlignCenter)
        banner.setStyleSheet(
            "background-color: #b7d8c5; font-size: 14px; font-weight: bold; padding: 3px;"
        )
        banner.setFixedHeight(self.height() // 6)  # 1/6e van het scherm
        layout.addWidget(banner)

        # Hoofd-grid: 2 rijen van 3 vakken
        for i in range(2):
            rij_layout = QHBoxLayout()
            for j in range(3):
                vak = QFrame()
                vak.setFrameShape(QFrame.StyledPanel)
                vak_layout = QVBoxLayout(vak)

                # Speciaal voor vak 1.2
                if i == 0 and j == 1:
                    self.create_task_buttons(vak_layout)

                # Zijkant-vakken smaller maken
                if j == 0 or j == 2:
                    vak.setFixedWidth(250)

                # Onderste vakken 2.1, 2.2, 2.3
                if i == 1:
                    vak.setFixedHeight(200)  # Pas dit getal aan voor andere hoogte

                rij_layout.addWidget(vak)
            layout.addLayout(rij_layout)

        # Afrondknop (bijvoorbeeld voor de dag afsluiten, placeholder)
        afsluit_knop = QPushButton("Dag afsluiten")
        afsluit_knop.clicked.connect(self.dag_afsluiten)
        layout.addWidget(afsluit_knop)

    def create_task_buttons(self, layout):
        from PySide6.QtGui import QIcon

        # Bovenste info-layout (gecentreerd)
        info_layout = QVBoxLayout()
        info_layout.setAlignment(Qt.AlignCenter)

        # Projectnaam (groot, geen label)
        projectnaam = "Algemene taken"  # fallback
        self.project_label = QLabel("📁 Algemene taken")
        self.project_label.setAlignment(Qt.AlignCenter)
        self.project_label.setStyleSheet("font-size: 26px;")
        info_layout.addWidget(self.project_label)

        # Taaknaam (kleiner, bold, geen label)
        self.taak_label = QLabel("📝 Taaknaam")
        self.taak_label.setAlignment(Qt.AlignCenter)
        self.taak_label.setStyleSheet("font-weight: bold; font-size: 20px;")
        info_layout.addWidget(self.taak_label)

        # Verwachte duur (alleen getal of 'duur onbekend')
        self.duur_label = QLabel("⏳ duur onbekend")
        self.duur_label.setAlignment(Qt.AlignCenter)
        self.duur_label.setStyleSheet("font-size: 14px; color: #555;")
        info_layout.addWidget(self.duur_label)

        layout.addLayout(info_layout)

        # Knoppen-grid
        for row in range(4):
            rij_layout = QHBoxLayout()
            for col in range(6):
                # Rij 1+2, kolom 2-5: grote 'Afronden'-knop
                if (row == 0 or row == 1) and 1 <= col <= 4:
                    if row == 0 and col == 1:
                        afronden_btn = QPushButton()
                        afronden_btn.setText("")  # Geen tekst
                        afronden_btn.setStyleSheet("background-color: #4CAF50;")
                        afronden_btn.setFixedHeight(60)
                        afronden_btn.setFixedWidth(300)
                        afronden_btn.setIconSize(QSize(48, 48))
                        rij_layout.addWidget(afronden_btn)
                    continue  # overslaan: wordt samengevoegd

                btn = QPushButton(f"K{row + 1}.{col + 1}")
                rij_layout.addWidget(btn)
            layout.addLayout(rij_layout)

    def dag_afsluiten(self):
        print("[Rooted] 🛑 Dag wordt afgesloten (placeholder).")
        self.accept()
