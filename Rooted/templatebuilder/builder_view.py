import json
import copy
from uuid import uuid4
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QToolBar,
    QFileDialog, QInputDialog, QMessageBox
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
from .block_items import (TaskItem, WaitItem, PopupItem, SubTemplateItem, StartItem, AnswerFilterItem, EndTaskItem)
from .connection_item import ConnectionItem
from .canvas_view import CanvasView


class TemplateBuilderWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.default_schema = "default"
        self.setWindowTitle("Template Builder")
        self.setGeometry(100, 100, 1200, 800)

        self.scene = QGraphicsScene(self)
        self.temp_template_json = {"blocks": [], "connections": []}
        self.view = CanvasView(self.scene, self)
        self.setCentralWidget(self.view)

        self.current_file = None

        self.create_menu()
        self.create_toolbar()

    def create_menu(self):
        menubar = self.menuBar()

        # Instellingen
        settings_menu = menubar.addMenu("Instellingen")
        schema_action = QAction("Standaardschema instellen", self)
        schema_action.triggered.connect(self.set_default_schema)
        settings_menu.addAction(schema_action)

        # Bestand
        file_menu = menubar.addMenu("Bestand")
        new_action = QAction("Nieuw template", self)
        new_action.triggered.connect(self.new_template)
        file_menu.addAction(new_action)

        load_action = QAction("Template laden", self)
        load_action.triggered.connect(self.load_template)
        file_menu.addAction(load_action)

        save_action = QAction("Opslaan", self)
        save_action.triggered.connect(self.save_template)
        file_menu.addAction(save_action)

        save_as_action = QAction("Opslaan als...", self)
        save_as_action.triggered.connect(self.save_template_as)
        file_menu.addAction(save_as_action)

        export_action = QAction("Exporteer als project", self)
        export_action.triggered.connect(self.export_as_project)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("Afsluiten", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Hulpmiddelen
        tools_menu = menubar.addMenu("Hulpmiddelen")
        sim_action = QAction("Simuleer template", self)
        sim_action.triggered.connect(self.simulate_template)
        tools_menu.addAction(sim_action)

        sync_action = QAction("Update subtemplates", self)
        sync_action.triggered.connect(self.update_subtemplates)
        tools_menu.addAction(sync_action)

    def create_toolbar(self):
        toolbar = QToolBar("Canvas Controls", self)
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        self.action_pan = QAction("Verplaats Canvas", self)
        self.action_pan.setCheckable(True)
        self.action_pan.toggled.connect(self.toggle_pan_mode)
        toolbar.addAction(self.action_pan)

        self.action_snap = QAction("Snapping aan/uit", self)
        self.action_snap.setCheckable(True)
        self.action_snap.toggled.connect(self.toggle_snap)
        toolbar.addAction(self.action_snap)

        zoom_in = QAction("Zoom In", self)
        zoom_in.triggered.connect(lambda: self.view.scale(1.2, 1.2))
        toolbar.addAction(zoom_in)

        zoom_out = QAction("Zoom Uit", self)
        zoom_out.triggered.connect(lambda: self.view.scale(1 / 1.2, 1 / 1.2))
        toolbar.addAction(zoom_out)

        toolbar.addSeparator()

        for label, method in [
            ("Taak toevoegen", self.add_task_block),
            ("Wachttijd toevoegen", self.add_wait_block),
            ("Popup toevoegen", self.add_popup_block),
            ("Filtertaak toevoegen", self.add_filter_block),
            ("Eindtaak toevoegen", self.add_endtask_block),
            ("Sub-template toevoegen", self.add_subtemplate_block),
        ]:
            action = QAction(label, self)
            action.triggered.connect(method)
            toolbar.addAction(action)

        action_refresh = QAction("Verbindingen updaten", self)
        action_refresh.triggered.connect(self.refresh_connections)
        toolbar.addAction(action_refresh)

    def toggle_pan_mode(self, checked):
        self.view.setDragMode(QGraphicsView.ScrollHandDrag if checked else QGraphicsView.NoDrag)

    def toggle_snap(self, checked):
        self.snap_to_grid = checked

    def _add_block(self, block):
        self.scene.addItem(block)
        block.setPos(0, 0)
        self.temp_template_json["blocks"].append(block.to_json())

    def add_task_block(self):
        self._add_block(TaskItem(schema=self.default_schema, uid=str(uuid4())))

    def add_wait_block(self):
        self._add_block(WaitItem(schema=self.default_schema, uid=str(uuid4())))

    def add_popup_block(self):
        self._add_block(PopupItem(schema=self.default_schema, uid=str(uuid4())))

    def add_filter_block(self):
        self._add_block(AnswerFilterItem(schema=self.default_schema, uid=str(uuid4())))

    def add_endtask_block(self):
        self._add_block(EndTaskItem(schema=self.default_schema, uid=str(uuid4())))

    def add_subtemplate_block(self):
        self._add_block(SubTemplateItem(schema=self.default_schema, uid=str(uuid4())))

    def new_template(self):
        self.scene.clear()
        self.temp_template_json = {"blocks": [], "connections": []}
        start = StartItem(schema=self.default_schema, uid=str(uuid4()))
        self.scene.addItem(start)
        start.setPos(0, 0)
        self.temp_template_json["blocks"].append(start.to_json())

    def save_template(self):
        if not self.validate_template():
            return
        if self.current_file:
            self._write_json(self.current_file)
        else:
            self.save_template_as()

    def save_template_as(self):
        if not self.validate_template():
            return
        path, _ = QFileDialog.getSaveFileName(self, "Sla template op als", "", "JSON Files (*.json)")
        if path:
            self.current_file = path
            self._write_json(path)

    def export_as_project(self):
        stripped = {
            "blocks": [b for b in self.temp_template_json["blocks"]],
            "connections": [c for c in self.temp_template_json["connections"]]
        }
        path, _ = QFileDialog.getSaveFileName(self, "Exporteer projectstructuur", "", "JSON Files (*.json)")
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(stripped, f, indent=2)

    def _write_json(self, path):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.temp_template_json, f, indent=2)

    def load_template(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open template", "", "JSON Files (*.json)")
        if not path:
            return
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.load_from_json(data)
        self.current_file = path

    def load_from_json(self, data):
        self.scene.clear()
        self.temp_template_json = copy.deepcopy(data)
        id_map = {}
        for b in data.get("blocks", []):
            print(f"🔍 Blok geladen uit JSON: {b}")
            cls = {
                'taak': TaskItem,
                'wachttijd': WaitItem,
                'popup': PopupItem,
                'endtask': EndTaskItem,
                'start': StartItem,
                'subtemplate': SubTemplateItem,
                'filter': AnswerFilterItem,
            }.get(b['type'], None)
            print(f"➡️ Gevonden klasse voor type '{b.get('type')}': {cls}")

            if not cls:
                continue
            if hasattr(cls, 'from_json'):
                item = cls.from_json(b)
            else:
                QMessageBox.critical(self, "Fout", f"Blokklasse '{cls.__name__}' heeft geen from_json()-methode.")
                continue
            item.setPos(*b.get('pos', [0, 0]))
            self.scene.addItem(item)
            id_map[b['uid']] = item
        for c in data.get("connections", []):
            src = id_map.get(c['source_id'])
            tgt = id_map.get(c['target_id'])
            if src and tgt:
                conn = ConnectionItem(src, tgt, label=c.get('label', ''))
                self.scene.addItem(conn)
                self.temp_template_json["connections"].append(conn.to_json())

    def refresh_connections(self):
        for it in self.scene.items():
            if hasattr(it, 'connections'):
                for conn in it.connections:
                    conn.update_position()

    def set_default_schema(self):
        text, ok = QInputDialog.getText(self, "Standaardschema", "Geef het standaardschema op:", text=self.default_schema)
        if ok and text:
            self.default_schema = text

    def validate_template(self):
        blocks = self.temp_template_json.get("blocks", [])
        uids = set(b["uid"] for b in blocks)
        has_start = any(b["type"] == "start" for b in blocks)
        if not has_start:
            QMessageBox.warning(self, "Validatie", "Template bevat geen startblok.")
            return False

        for b in blocks:
            if b["type"] == "answerfilter":
                if not b.get("filter_uid") or not b.get("filter_waarde"):
                    QMessageBox.warning(self, "Validatie", f"Filtertaak '{b['name']}' is incompleet.")
                    return False

        return True

    def simulate_template(self):
        QMessageBox.information(self, "Simulatie", "Simulatiemodus nog niet geïmplementeerd.")

    def update_subtemplates(self):
        QMessageBox.information(self, "Subtemplates", "Subtemplate-sync volgt in een latere versie.")


if __name__ == '__main__':
    app = QApplication([])
    win = TemplateBuilderWindow()
    win.show()
    app.exec()
