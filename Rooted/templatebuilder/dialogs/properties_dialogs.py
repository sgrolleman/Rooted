from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout, QFormLayout, QLineEdit, QSpinBox,
    QPushButton, QMessageBox, QColorDialog, QDateEdit, QListWidget, QListWidgetItem,
    QInputDialog, QComboBox, QLabel, QTextEdit
)
from PySide6.QtGui import QClipboard, QGuiApplication
import sqlite3


class BlockPropertiesDialog(QDialog):
    def __init__(self, block):
        super().__init__()
        from templatebuilder.block_items import AnswerFilterItem, PopupItem, SubTemplateItem
        self.block = block
        self.setWindowTitle("Blok eigenschappen")

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        # Naam
        self.name_edit = QLineEdit(block.name)
        form.addRow("Naam:", self.name_edit)

        # Schema
        self.schema_edit = QLineEdit(block.schema)
        form.addRow("Schema:", self.schema_edit)

        # UID zichtbaar in readonly modus + kopieerknop
        uid_layout = QHBoxLayout()
        self.uid_edit = QLineEdit(self.block.uid)
        self.uid_edit.setReadOnly(True)
        uid_layout.addWidget(self.uid_edit)
        self.copy_uid_btn = QPushButton("Kopieer UID")
        self.copy_uid_btn.clicked.connect(self.kopieer_uid)
        uid_layout.addWidget(self.copy_uid_btn)
        form.addRow("UID:", uid_layout)

        # -------------------------
        # Filtertaken
        # -------------------------
        if isinstance(block, AnswerFilterItem):
            self.uid_target_combo = QComboBox()
            self.uid_target_combo.setEditable(False)
            self.uid_target_combo.setMinimumWidth(200)

            scene = self.block.scene()
            view = scene.views()[0].parent() if scene and scene.views() else None
            self.popup_map = {}
            if view and hasattr(view, "temp_template_json"):
                for b in view.temp_template_json.get("blocks", []):
                    if b.get("type") == "popup":
                        label = f"{b.get('question', '')} ({b['uid'][:6]})"
                        self.popup_map[label] = b["uid"]
                        self.uid_target_combo.addItem(label)

            for label, uid in self.popup_map.items():
                if uid == block.filter_uid:
                    self.uid_target_combo.setCurrentText(label)
                    break

            form.addRow("Filter op vraag:", self.uid_target_combo)

            self.operator_combo = QComboBox()
            self.operator_combo.addItems(["=", "≠", ">", "<"])
            self.operator_combo.setCurrentText(getattr(block, "operator", "="))
            form.addRow("Vergelijking:", self.operator_combo)

            self.filter_value_combo = QComboBox()
            self.filter_value_combo.setEditable(True)
            form.addRow("Waarde:", self.filter_value_combo)

            if getattr(block, 'filter_waarde', None):
                self.filter_value_combo.addItem(block.filter_waarde)
                self.filter_value_combo.setCurrentText(block.filter_waarde)

        # -------------------------
        # Duur of vertraging
        # -------------------------
        if hasattr(block, "duration"):
            self.duration_spin = QSpinBox()
            self.duration_spin.setMaximum(10000)
            self.duration_spin.setValue(block.duration)
            form.addRow("Duur (minuten):", self.duration_spin)
        elif hasattr(block, "delay"):
            self.delay_spin = QSpinBox()
            self.delay_spin.setMaximum(10000)
            self.delay_spin.setValue(block.delay)
            form.addRow("Vertraging (dagen):", self.delay_spin)

        # -------------------------
        # Vraag en antwoordtype (PopupItem / StartItem)
        # -------------------------
        from templatebuilder.block_items import AnswerFilterItem as _Filter
        if hasattr(block, "question") and not isinstance(block, _Filter):
            self.question_edit = QLineEdit(block.question)
            form.addRow("Vraag:", self.question_edit)

            self.answer_type_combo = QComboBox()
            self.answer_type_combo.addItems(["keuze", "tekst", "datum"])
            self.answer_type_combo.setCurrentText(getattr(block, "answer_type", "keuze"))
            self.answer_type_combo.currentTextChanged.connect(self.toggle_options_visibility)
            form.addRow("Antwoordtype:", self.answer_type_combo)

            self.options_list = QListWidget()
            if getattr(block, "options", None):
                for opt in block.options:
                    self.options_list.addItem(QListWidgetItem(opt))
            form.addRow("Opties:", self.options_list)

            self.add_option_btn = QPushButton("Optie toevoegen")
            self.add_option_btn.clicked.connect(self.add_option)
            form.addRow(self.add_option_btn)

            self.default_date_edit = QDateEdit()
            self.default_date_edit.setCalendarPopup(True)
            self.default_date_edit.setDate(QDate.currentDate())
            form.addRow("Standaarddatum:", self.default_date_edit)

            self.toggle_options_visibility(self.answer_type_combo.currentText())

        # -------------------------
        # Afhankelijke blokken tonen bij popupvraag
        # -------------------------
        if isinstance(block, PopupItem):
            scene = self.block.scene()
            antwoord_overzicht = QTextEdit()
            antwoord_overzicht.setReadOnly(True)
            antwoord_overzicht.setMaximumHeight(100)

            conn_texts = []
            for item in scene.items():
                if hasattr(item, "source_item") and item.source_item == block:
                    label = getattr(item, "label", "")
                    doel = getattr(item, "target_item", None)
                    doelnaam = getattr(doel, "name", "(onbekend)") if doel else "?"
                    conn_texts.append(f"{label} → {doelnaam}")
            if conn_texts:
                antwoord_overzicht.setPlainText("\n".join(conn_texts))
                layout.addWidget(QLabel("Verbindingen vanuit deze vraag:"))
                layout.addWidget(antwoord_overzicht)

        # -------------------------
        # Subtemplate preview
        # -------------------------
        if isinstance(block, SubTemplateItem):
            from os.path import basename
            preview = QLabel()
            preview.setText(f"Ingesloten bestand:\n{basename(block.file_path) if block.file_path else '(geen bestand)'}")
            layout.addWidget(preview)

        # -------------------------
        # OK & Annuleren
        # -------------------------
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Annuleren")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(ok_btn)
        layout.addWidget(cancel_btn)

    def toggle_options_visibility(self, answer_type):
        is_keuze = (answer_type == "keuze")
        is_datum = (answer_type == "datum")

        self.options_list.setVisible(is_keuze)
        self.add_option_btn.setVisible(is_keuze)
        self.default_date_edit.setVisible(is_datum)

    def add_option(self):
        text, ok = QInputDialog.getText(self, "Optie toevoegen", "Optie:")
        if ok and text:
            self.options_list.addItem(QListWidgetItem(text))

    def kopieer_uid(self):
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self.uid_edit.text())

    def apply_changes(self):
        from templatebuilder.block_items import AnswerFilterItem

        self.block.set_block_name(self.name_edit.text())
        self.block.schema = self.schema_edit.text()

        # ⏱️ Duur of vertraging
        if hasattr(self.block, "duration") and hasattr(self, "duration_spin"):
            self.block.duration = self.duration_spin.value()
        elif hasattr(self.block, "delay") and hasattr(self, "delay_spin"):
            self.block.delay = self.delay_spin.value()

        # ❓ Vraag + antwoordtype
        if hasattr(self.block, "question") and hasattr(self, "question_edit"):
            self.block.question = self.question_edit.text()

        if hasattr(self.block, "answer_type") and hasattr(self, "answer_type_combo"):
            self.block.answer_type = self.answer_type_combo.currentText()

            if self.block.answer_type == "keuze" and hasattr(self, "options_list"):
                self.block.options = [
                    self.options_list.item(i).text()
                    for i in range(self.options_list.count())
                ]
            elif self.block.answer_type == "datum" and hasattr(self, "default_date_edit"):
                self.block.default_date = self.default_date_edit.date().toString("yyyy-MM-dd")

        # 🔍 Filtereigenschappen
        if isinstance(self.block, AnswerFilterItem):
            if hasattr(self, "uid_target_combo"):
                label = self.uid_target_combo.currentText()
                self.block.filter_uid = self.popup_map.get(label, "")
            if hasattr(self, "filter_value_combo"):
                self.block.filter_waarde = self.filter_value_combo.currentText()
            if hasattr(self, "operator_combo"):
                self.block.operator = self.operator_combo.currentText()

            # Validatie
            if not self.block.filter_uid.strip():
                QMessageBox.warning(self, "Fout", "Filtertaak heeft geen gekoppelde vraag.")
                return
            if not self.block.filter_waarde.strip():
                QMessageBox.warning(self, "Fout", "Filtertaak heeft geen filterwaarde.")
                return

        # 🔁 Update tijdelijke JSON in builder_view
        block_json = self.block.to_json()
        scene = self.block.scene()
        view = scene.views()[0].parent() if scene and scene.views() else None
        if view and hasattr(view, "temp_template_json"):
            blocks = view.temp_template_json.get("blocks", [])
            for i, b in enumerate(blocks):
                if b.get("uid") == self.block.uid:
                    blocks[i] = block_json
                    break
