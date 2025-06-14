from PySide6.QtWidgets import QGraphicsPathItem, QGraphicsTextItem, QMenu, QInputDialog, QMessageBox
from PySide6.QtGui import QPen, QColor, QPainterPath, QPainter, QBrush
from PySide6.QtCore import Qt, QPointF

class ConnectionItem(QGraphicsPathItem):
    def __init__(self, source_item, target_item, label="Label", parent=None):
        super().__init__(parent)
        self.source_item = source_item
        self.target_item = target_item
        self.active_for_options = []
        self.label = label

        self.source_item.connections.append(self)
        self.target_item.connections.append(self)

        self.setZValue(-1)
        self.pen = QPen(QColor("red"), 4)
        self.setPen(self.pen)

        self.label_item = QGraphicsTextItem(self.label, self)
        self.label_item.setDefaultTextColor(Qt.darkBlue)
        self.label_item.setZValue(1)
        self.label_item.setTextWidth(100)
        self.label_item.setDefaultTextColor(Qt.darkBlue)

        self.update_position()
        self._sync_to_json()

    def update_position(self):
        source_center = self.source_item.sceneBoundingRect().center()
        target_center = self.target_item.sceneBoundingRect().center()
        middle_point = QPointF(target_center.x(), source_center.y())

        path = QPainterPath(source_center)
        path.lineTo(middle_point)
        path.lineTo(target_center)
        self.setPath(path)

        self.label_item.setPos((source_center + target_center) / 2 - QPointF(50, 10))

    def paint(self, painter: QPainter, option, widget=None):
        painter.setPen(self.pen)
        painter.drawPath(self.path())
        self.draw_arrow(painter)

    def draw_arrow(self, painter: QPainter):
        path = self.path()
        if path.elementCount() < 2:
            return
        p1 = path.pointAtPercent(1.0)
        p2 = path.pointAtPercent(0.9)
        dx = p1.x() - p2.x()
        dy = p1.y() - p2.y()
        length = (dx**2 + dy**2)**0.5
        if length == 0:
            return
        dx /= length
        dy /= length
        arrow_size = 10
        left = QPointF(p1.x() - arrow_size * (dx + dy), p1.y() - arrow_size * (dy - dx))
        right = QPointF(p1.x() - arrow_size * (dx - dy), p1.y() - arrow_size * (dy + dx))
        painter.setBrush(QColor("black"))
        arrow_path = QPainterPath()
        arrow_path.moveTo(p1)
        arrow_path.lineTo(left)
        arrow_path.lineTo(right)
        arrow_path.closeSubpath()
        painter.drawPath(arrow_path)

    def contextMenuEvent(self, event):
        menu = QMenu()
        edit_label_action = menu.addAction("Label aanpassen")
        edit_props_action = menu.addAction("Eigenschappen aanpassen")
        split_action = menu.addAction("Voeg blok in tussen connectie")
        delete_action = menu.addAction("Verwijderen")

        action = menu.exec(event.screenPos())

        if action == edit_label_action:
            self.edit_label()
        elif action == edit_props_action:
            from .dialogs.properties_dialogs import ConnectionPropertiesDialog
            dialog = ConnectionPropertiesDialog(self)
            if dialog.exec():
                dialog.accept()
        elif action == split_action:
            self.split_connection()
        elif action == delete_action:
            self.delete_connection()

    def show_context_menu(self, global_pos):
        menu = QMenu()
        edit_label_action = menu.addAction("Label aanpassen")
        edit_props_action = menu.addAction("Eigenschappen aanpassen")
        split_action = menu.addAction("Voeg blok in tussen connectie")
        delete_action = menu.addAction("Verwijderen")

        action = menu.exec(global_pos)

        if action == edit_label_action:
            self.edit_label()
        elif action == edit_props_action:
            from .dialogs.properties_dialogs import ConnectionPropertiesDialog
            dialog = ConnectionPropertiesDialog(self)
            if dialog.exec():
                dialog.accept()
        elif action == split_action:
            self.split_connection()
        elif action == delete_action:
            self.delete_connection()

    def delete_connection(self):
        try:
            scene = self.scene()
            view = scene.views()[0]
            builder = view.parent()
            if hasattr(builder, 'temp_template_json'):
                conns = builder.temp_template_json.get('connections', [])
                conns = [
                    c for c in conns
                    if not (c['source_id'] == self.source_item.uid and
                            c['target_id'] == self.target_item.uid and
                            c['label'] == self.label)
                ]
                builder.temp_template_json['connections'] = conns
        except Exception:
            pass

        scene = self.scene()
        if scene:
            scene.removeItem(self)
            if self.source_item and self in self.source_item.connections:
                self.source_item.connections.remove(self)
            if self.target_item and self in self.target_item.connections:
                self.target_item.connections.remove(self)

    def edit_label(self):
        text, ok = QInputDialog.getText(None, "Label aanpassen", "Label:", text=self.label)
        if ok:
            self.label = text
            self.label_item.setPlainText(text)
            self._sync_to_json()

    def split_connection(self):
        scene = self.scene()
        if not scene:
            return

        from .block_items import TaskItem, WaitItem, AnswerFilterItem, PopupItem

        types = {
            "Taak": TaskItem,
            "Wachttijd": WaitItem,
            "Filtertaak": AnswerFilterItem,
            "Popuptaak": PopupItem
        }

        selected, ok = QInputDialog.getItem(
            None,
            "Kies type blok",
            "Welk blok wil je invoegen?",
            list(types.keys()),
            0,
            False
        )
        if not ok or selected not in types:
            return

        self.delete_connection()
        block_cls = types[selected]
        new_block = block_cls(name=f"Ingevoegd: {selected}")
        new_block.setPos((self.source_item.pos() + self.target_item.pos()) / 2)
        scene.addItem(new_block)

        conn1 = ConnectionItem(self.source_item, new_block, label=f"via {self.label}")
        conn2 = ConnectionItem(new_block, self.target_item, label=self.label)
        scene.addItem(conn1)
        scene.addItem(conn2)

        # Voeg toe aan tijdelijke template json als aanwezig
        view = scene.views()[0].parent()
        if hasattr(view, "temp_template_json"):
            view.temp_template_json["blocks"].append(new_block.to_json())
            view.temp_template_json["connections"].append(conn1.to_json())
            view.temp_template_json["connections"].append(conn2.to_json())

    def _sync_to_json(self):
        try:
            scene = self.scene()
            view = scene.views()[0]
            builder = view.parent()
            if hasattr(builder, 'temp_template_json'):
                conns = builder.temp_template_json.get('connections', [])
                for i, c in enumerate(conns):
                    if c['source_id'] == self.source_item.uid and c['target_id'] == self.target_item.uid:
                        conns[i] = self.to_json()
                        break
                else:
                    conns.append(self.to_json())
        except Exception:
            pass

    def to_json(self):
        return {
            "source_id": self.source_item.uid,
            "target_id": self.target_item.uid,
            "label": self.label,
            "active_for_options": self.active_for_options,
            "missing_label": not bool(self.label.strip())
        }
