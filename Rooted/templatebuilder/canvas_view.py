from uuid import uuid4

from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter, QWheelEvent
from PySide6.QtWidgets import QGraphicsView, QApplication, QGraphicsTextItem, QMenu

from .block_items import (
    TaskItem,
    WaitItem,
    PopupItem,
    SubTemplateItem,
    AnswerFilterItem,
    EndTaskItem
)
from .connection_item import ConnectionItem
from .dialogs.properties_dialogs import BlockPropertiesDialog


class CanvasView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.line_start_item = None
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.scale_factor = 1.15
        self.grid_size = 100

        self.setDragMode(QGraphicsView.RubberBandDrag)

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        grid_size = self.grid_size
        left = int(rect.left()) - (int(rect.left()) % grid_size)
        top = int(rect.top()) - (int(rect.top()) % grid_size)

        painter.setPen(Qt.lightGray)
        for x in range(left, int(rect.right()), grid_size):
            painter.drawLine(x, rect.top(), x, rect.bottom())
        for y in range(top, int(rect.bottom()), grid_size):
            painter.drawLine(rect.left(), y, rect.right(), y)

    def wheelEvent(self, event: QWheelEvent):
        if event.angleDelta().y() > 0:
            self.scale(self.scale_factor, self.scale_factor)
        else:
            self.scale(1 / self.scale_factor, 1 / self.scale_factor)

    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())

        # Zorg dat je geen QGraphicsTextItem pakt
        if isinstance(item, QGraphicsTextItem) and item.parentItem():
            item = item.parentItem()

        if event.button() == Qt.RightButton:
            if hasattr(item, "show_context_menu"):
                item.show_context_menu(self.mapToGlobal(event.pos()))
                return

        elif event.button() == Qt.LeftButton:
            modifiers = QApplication.keyboardModifiers()
            if modifiers == Qt.ShiftModifier:
                # Alleen verbinding maken met Shift
                if isinstance(item, QGraphicsTextItem) and item.parentItem():
                    item = item.parentItem()

                if isinstance(item, (TaskItem, WaitItem, PopupItem, SubTemplateItem, AnswerFilterItem, EndTaskItem)):
                    if self.line_start_item is None:
                        self.line_start_item = item
                    else:
                        if item != self.line_start_item:
                            conn = ConnectionItem(self.line_start_item, item)
                            self.scene().addItem(conn)

                            # Voeg ook toe aan template_json als aanwezig
                            view = self.parent()
                            if hasattr(view, 'temp_template_json'):
                                view.temp_template_json["connections"].append(conn.to_json())

                        self.line_start_item = None
            else:
                # Zonder shift = reset
                self.line_start_item = None

        super().mousePressEvent(event)

    def update_connections_for_item(self, item):
        for obj in self.scene().items():
            if hasattr(obj, 'update_position'):
                if getattr(obj, 'source_item', None) is item or getattr(obj, 'target_item', None) is item:
                    obj.update_position()

    def contextMenuEvent(self, event):
        pos = self.mapToScene(event.pos())
        items = self.scene().items(pos)

        if not items:
            # Rechtsklik op canvas: nieuw blok toevoegen
            menu = QMenu()
            add_task = menu.addAction("Taak toevoegen")
            add_wait = menu.addAction("Wachttijd toevoegen")
            add_popup = menu.addAction("Popup toevoegen")
            add_sub = menu.addAction("Sub-template toevoegen")
            add_end = menu.addAction("Eindtaak toevoegen")
            add_filter = menu.addAction("Filtertaak toevoegen")

            action = menu.exec(event.globalPos())
            block = None
            if action == add_task:
                block = TaskItem(uid=str(uuid4()))
            elif action == add_wait:
                block = WaitItem(uid=str(uuid4()))
            elif action == add_popup:
                block = PopupItem(uid=str(uuid4()))
            elif action == add_sub:
                block = SubTemplateItem(uid=str(uuid4()))
            elif action == add_end:
                block = EndTaskItem(uid=str(uuid4()))
            elif action == add_filter:
                block = AnswerFilterItem(uid=str(uuid4()))

            if block:
                block.setPos(pos)
                self.scene().addItem(block)
                if hasattr(self.parent(), 'temp_template_json'):
                    self.parent().temp_template_json['blocks'].append(block.to_json())

        else:
            target = items[0]
            # Laat blok zelf zijn contextmenu afhandelen
            for item in items:
                if isinstance(item, QGraphicsTextItem):
                    if item.parentItem():
                        item = item.parentItem()
                if hasattr(item, 'contextMenuEvent'):
                    if hasattr(item, "show_context_menu"):
                        item.show_context_menu(self.mapToGlobal(event.pos()))
                    return
            super().contextMenuEvent(event)

    def show_context_menu(self, global_pos):
        menu = QMenu()
        prop_action = menu.addAction("Eigenschappen")
        duplicate_action = menu.addAction("Dupliceren")
        delete_action = menu.addAction("Verwijderen")
        action = menu.exec(global_pos)

        if action == prop_action:
            dialog = BlockPropertiesDialog(self)
            if dialog.exec():
                dialog.apply_changes()
        elif action == duplicate_action:
            clone = self.clone()
            clone.setPos(self.pos() + QPointF(30, 30))
            self.scene().addItem(clone)
            view = self.scene().views()[0].parent()
            if hasattr(view, "temp_template_json"):
                view.temp_template_json["blocks"].append(clone.to_json())
        elif action == delete_action:
            self.delete_item()