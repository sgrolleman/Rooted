from PySide6.QtWidgets import (
    QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsPolygonItem,
    QGraphicsItem, QGraphicsTextItem, QMenu
)
from PySide6.QtGui import QBrush, QColor, QPen, QPolygonF
from PySide6.QtCore import QPointF, Qt
import uuid
from .dialogs.properties_dialogs import BlockPropertiesDialog
from .connection_item import ConnectionItem


class BlockMixin:
    def init_block(self, name="Nieuw blok", color=QColor("yellow"), schema="default", uid=None):
        self.name = name
        self.color = color
        self.schema = schema
        self.uid = uid or str(uuid.uuid4())
        self.connections = []
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)

    def contextMenuEvent(self, event):
        menu = QMenu()
        prop_action = menu.addAction("Eigenschappen")
        duplicate_action = menu.addAction("Dupliceren")
        delete_action = menu.addAction("Verwijderen")
        action = menu.exec(event.screenPos())

        if action == prop_action:
            dialog = BlockPropertiesDialog(self)
            if dialog.exec():
                dialog.apply_changes()
        elif action == duplicate_action:
            clone = self.clone()
            clone.setPos(self.pos() + QPointF(30, 30))
            scene = self.scene()
            scene.addItem(clone)
            view = scene.views()[0].parent()
            if hasattr(view, "temp_template_json"):
                view.temp_template_json["blocks"].append(clone.to_json())
        elif action == delete_action:
            self.delete_item()

    def mouseDoubleClickEvent(self, event):
        dialog = BlockPropertiesDialog(self)
        if dialog.exec():
            dialog.apply_changes()
        super().mouseDoubleClickEvent(event)

    def delete_item(self):
        scene = self.scene()
        for connection in list(self.connections):
            scene.removeItem(connection)
            if connection.source_item and connection in connection.source_item.connections:
                connection.source_item.connections.remove(connection)
            if connection.target_item and connection in connection.target_item.connections:
                connection.target_item.connections.remove(connection)
        scene.removeItem(self)
        view = scene.views()[0].parent()
        if hasattr(view, "temp_template_json"):
            view.temp_template_json["blocks"] = [
                b for b in view.temp_template_json["blocks"]
                if b["uid"] != self.uid
            ]
            view.temp_template_json["connections"] = [
                c for c in view.temp_template_json["connections"]
                if c["source_id"] != self.uid and c["target_id"] != self.uid
            ]

    def is_valid(self):
        return True  # voor latere validatie-uitbreiding


class TaskItem(QGraphicsRectItem, BlockMixin):
    def __init__(self, name="Nieuwe Taak", duration=30, priority="Normaal", category="Algemeen",
                 project_id=None, template_id=None, deadline=None,
                 planned_start=None, planned_end=None, notes="",
                 color=QColor("yellow"), schema="default", uid=None):
        # Rechthoekig blok 100x60
        super().__init__(-50, -30, 100, 60)

        # Basisgegevens
        self.name = name
        self.duration = duration  # minuten

        # Context
        self.priority = priority
        self.category = category
        self.project_id = project_id
        self.template_id = template_id

        # Planning
        self.deadline = deadline
        self.planned_start = planned_start
        self.planned_end = planned_end

        # Metadata
        self.notes = notes

        # Algemene blok-instellingen (kleur, schema, uid, connecties, flags)
        self.init_block(name, color, schema, uid)

    # ----------------------------
    # Tekenen van het blok
    # ----------------------------
    def paint(self, painter, option, widget):
        painter.setBrush(QBrush(self.color))
        painter.setPen(QPen(Qt.black, 2))
        painter.drawRect(self.rect())

        # Tekst samenstellen
        lines = [self.name]
        if self.duration:
            lines.append(f"{self.duration} min")
        if self.priority:
            lines.append(self.priority)

        # Tekst centreren
        painter.drawText(self.rect(), Qt.AlignCenter, "\n".join(lines))

    # ----------------------------
    # Contextmenu (rechtermuisklik)
    # ----------------------------
    def contextMenuEvent(self, event):
        menu = QMenu()
        prop_action = menu.addAction("Eigenschappen")
        duplicate_action = menu.addAction("Dupliceren")
        delete_action = menu.addAction("Verwijderen")
        action = menu.exec(event.screenPos())

        if action == prop_action:
            dialog = BlockPropertiesDialog(self)
            if dialog.exec():
                dialog.apply_changes()
        elif action == duplicate_action:
            clone = self.clone()
            clone.setPos(self.pos() + QPointF(30, 30))
            scene = self.scene()
            scene.addItem(clone)
            view = scene.views()[0].parent()
            if hasattr(view, "temp_template_json"):
                view.temp_template_json["blocks"].append(clone.to_json())
        elif action == delete_action:
            self.delete_item()

    # ----------------------------
    # Dubbelklik
    # ----------------------------
    def mouseDoubleClickEvent(self, event):
        dialog = BlockPropertiesDialog(self)
        if dialog.exec():
            dialog.apply_changes()
        super().mouseDoubleClickEvent(event)

    # ----------------------------
    # JSON-export
    # ----------------------------
    def to_json(self):
        return {
            "type": "taak",
            "name": self.name,
            "duration": self.duration,
            "priority": self.priority,
            "category": self.category,
            "project_id": self.project_id,
            "template_id": self.template_id,
            "deadline": self.deadline,
            "planned_start": self.planned_start,
            "planned_end": self.planned_end,
            "notes": self.notes,
            "color": self.color.name() if hasattr(self.color, "name") else self.color,
            "schema": self.schema,
            "pos": [self.pos().x(), self.pos().y()],
            "uid": self.uid
        }

    @classmethod
    def from_json(cls, data):
        item = cls(
            name=data.get("name", "Taak"),
            duration=data.get("duration", 30),
            priority=data.get("priority", "Normaal"),
            category=data.get("category", "Algemeen"),
            project_id=data.get("project_id"),
            template_id=data.get("template_id"),
            deadline=data.get("deadline"),
            planned_start=data.get("planned_start"),
            planned_end=data.get("planned_end"),
            notes=data.get("notes", ""),
            color=QColor(data.get("color", "#ffff00")),
            schema=data.get("schema", "default"),
            uid=data.get("uid")
        )
        item.setPos(*data.get("pos", [0, 0]))
        return item

    # ----------------------------
    # Kopiëren
    # ----------------------------
    def clone(self):
        return TaskItem(
            name=self.name,
            duration=self.duration,
            priority=self.priority,
            category=self.category,
            project_id=self.project_id,
            template_id=self.template_id,
            deadline=self.deadline,
            planned_start=self.planned_start,
            planned_end=self.planned_end,
            notes=self.notes,
            color=self.color,
            schema=self.schema,
            uid=str(uuid.uuid4())
        )

class WaitItem(QGraphicsPolygonItem, BlockMixin):
    def __init__(self, name="Wachttijd", delay=1, color=QColor("orange"), schema="default", uid=None):
        points = [QPointF(0, -30), QPointF(-30, 30), QPointF(30, 30)]
        polygon = QPolygonF(points)
        super().__init__(polygon)
        self.delay = delay
        self.init_block(name, color, schema, uid)

    def paint(self, painter, option, widget):
        painter.setBrush(QBrush(self.color))
        painter.setPen(QPen(Qt.black, 2))
        painter.drawPolygon(self.polygon())

    def show_context_menu(self, global_pos):
        menu = QMenu()
        prop_action = menu.addAction("Eigenschappen")
        delete_action = menu.addAction("Verwijderen")
        action = menu.exec(global_pos)
        if action == prop_action:
            dialog = BlockPropertiesDialog(self)
            if dialog.exec():
                dialog.apply_changes()
        elif action == delete_action:
            self.delete_item()

    def mouseDoubleClickEvent(self, event):
        dialog = BlockPropertiesDialog(self)
        if dialog.exec():
            dialog.apply_changes()
        super().mouseDoubleClickEvent(event)

    def to_json(self):
        return {
            "type": "wachttijd",
            "name": self.name,
            "delay": self.delay,
            "color": self.color.name() if hasattr(self.color, "name") else self.color,
            "schema": self.schema,
            "pos": [self.pos().x(), self.pos().y()],
            "uid": self.uid
        }

    @classmethod
    def from_json(cls, data):
        item = cls(
            name=data.get("name", "Wachttijd"),
            delay=data.get("delay", 1),
            color=QColor(data.get("color", "#ffa500")),
            schema=data.get("schema", "default"),
            uid=data.get("uid")
        )
        item.setPos(*data.get("pos", [0, 0]))
        return item

    def clone(self):
        return WaitItem(
            name=self.name,
            delay=self.delay,
            color=self.color,
            schema=self.schema,
            uid=str(uuid.uuid4())
        )

class SubTemplateItem(QGraphicsRectItem, BlockMixin):
    def __init__(self, name="Sub-template", file_path=None, color=QColor("lightgray"), schema="default", uid=None):
        super().__init__(-60, -30, 120, 60)
        self.file_path = file_path
        self.init_block(name, color, schema, uid)

    def paint(self, painter, option, widget):
        painter.setBrush(QBrush(self.color))
        painter.setPen(QPen(Qt.darkGray, 2, Qt.DashLine))
        painter.drawRect(self.rect())
        if self.file_path:
            painter.drawText(self.rect(), Qt.AlignBottom | Qt.AlignHCenter,
                             f"({self.file_path.split('/')[-1]})")

    def show_context_menu(self, global_pos):
        menu = QMenu()
        prop_action = menu.addAction("Eigenschappen")
        delete_action = menu.addAction("Verwijderen")
        action = menu.exec(global_pos)
        if action == prop_action:
            dialog = BlockPropertiesDialog(self)
            if dialog.exec():
                dialog.apply_changes()
        elif action == delete_action:
            self.delete_item()

    def to_json(self):
        return {
            "type": "subtemplate",
            "name": self.name,
            "file_path": self.file_path,
            "color": self.color.name() if hasattr(self.color, "name") else self.color,
            "schema": self.schema,
            "pos": [self.pos().x(), self.pos().y()],
            "uid": self.uid
        }

    @classmethod
    def from_json(cls, data):
        item = cls(
            name=data.get("name", "Subtemplate"),
            file_path=data.get("file_path"),
            color=QColor(data.get("color", "#d3d3d3")),
            schema=data.get("schema", "default"),
            uid=data.get("uid")
        )
        item.setPos(*data.get("pos", [0, 0]))
        return item

    def mouseDoubleClickEvent(self, event):
        from .dialogs.properties_dialogs import BlockPropertiesDialog
        dialog = BlockPropertiesDialog(self)
        if dialog.exec():
            dialog.apply_changes()
        super().mouseDoubleClickEvent(event)

    def clone(self):
        return SubTemplateItem(
            name=self.name,
            file_path=self.file_path,
            color=self.color,
            schema=self.schema,
            uid=str(uuid.uuid4())
        )
class PopupItem(QGraphicsEllipseItem, BlockMixin):
    def __init__(self, name="Popup", question="Vraag?", options=None, answer_type="keuze",
                 color=QColor("lightgreen"), schema="default", uid=None):
        super().__init__(-40, -25, 80, 50)
        self.question = question
        self.options = options or []
        self.answer_type = answer_type
        self.default_date = None
        self.set_target = None
        self.set_field = None
        self.set_target_uid = None
        self.init_block(name, color, schema, uid)

    def paint(self, painter, option, widget):
        painter.setBrush(QBrush(self.color))
        painter.setPen(QPen(Qt.black, 2))
        painter.drawEllipse(self.rect())

    def show_context_menu(self, global_pos):
        menu = QMenu()
        generate_filters_action = menu.addAction("Genereer filtertaken")
        prop_action = menu.addAction("Eigenschappen")
        delete_action = menu.addAction("Verwijderen")
        action = menu.exec(global_pos)

        if action == generate_filters_action:
            self.generate_filter_tasks()
        elif action == prop_action:
            dialog = BlockPropertiesDialog(self)
            if dialog.exec():
                dialog.apply_changes()
        elif action == delete_action:
            self.delete_item()

    def mouseDoubleClickEvent(self, event):
        dialog = BlockPropertiesDialog(self)
        if dialog.exec():
            dialog.apply_changes()
        super().mouseDoubleClickEvent(event)

    def to_json(self):
        return {
            "type": "popup",
            "name": self.name,
            "question": self.question,
            "answer_type": self.answer_type,
            "options": self.options,
            "default_date": self.default_date,
            "set_target": self.set_target,
            "set_field": self.set_field,
            "set_target_uid": self.set_target_uid,
            "color": self.color.name() if hasattr(self.color, "name") else self.color,
            "schema": self.schema,
            "pos": [self.pos().x(), self.pos().y()],
            "uid": self.uid
        }

    @classmethod
    def from_json(cls, data):
        item = cls(
            name=data.get("name", "Popup"),
            question=data.get("question", "Vraag?"),
            options=data.get("options", []),
            answer_type=data.get("answer_type", "keuze"),
            color=QColor(data.get("color", "#90ee90")),
            schema=data.get("schema", "default"),
            uid=data.get("uid")
        )
        item.default_date = data.get("default_date")
        item.set_field = data.get("set_field")
        item.set_target = data.get("set_target")
        item.set_target_uid = data.get("set_target_uid")
        item.setPos(*data.get("pos", [0, 0]))
        return item

    def generate_filter_tasks(self):
        if self.answer_type != "keuze":
            return

        for option in self.options:
            filter_task = AnswerFilterItem(
                name=f"Filter: {option}",
                filter_key=self.name,
                filter_value=option,
                schema=self.schema,
                uid=str(uuid.uuid4())
            )
            filter_task.setPos(self.pos() + QPointF(150, 50 * (self.options.index(option) + 1)))
            self.scene().addItem(filter_task)

            # Optioneel: meteen opnemen in een tijdelijke lijst of JSON
            view = self.scene().views()[0].parent()
            if hasattr(view, "temp_template_json"):
                view.temp_template_json["blocks"].append(filter_task.to_json())

            # Maak connectie
            conn = ConnectionItem(self, filter_task)
            self.scene().addItem(conn)

    def clone(self):
        clone = PopupItem(
            name=self.name,
            question=self.question,
            options=list(self.options),
            answer_type=self.answer_type,
            color=self.color,
            schema=self.schema,
            uid=str(uuid.uuid4())
        )
        clone.default_date = self.default_date
        clone.set_target = self.set_target
        clone.set_field = self.set_field
        clone.set_target_uid = self.set_target_uid
        return clone

    def contextMenuEvent(self, event):
        menu = QMenu()
        gen_action = menu.addAction("Genereer antwoordtaken")
        prop_action = menu.addAction("Eigenschappen")
        duplicate_action = menu.addAction("Dupliceren")
        delete_action = menu.addAction("Verwijderen")
        action = menu.exec(event.screenPos())
        if action == gen_action:
            self.generate_answer_blocks()
        elif action == prop_action:
            dialog = BlockPropertiesDialog(self)
            if dialog.exec():
                dialog.apply_changes()
        elif action == duplicate_action:
            clone = self.clone()
            clone.setPos(self.pos() + QPointF(30, 30))
            scene = self.scene()
            scene.addItem(clone)
            view = scene.views()[0].parent()
            if hasattr(view, "temp_template_json"):
                view.temp_template_json["blocks"].append(clone.to_json())
        elif action == delete_action:
            self.delete_item()

    def generate_filter_tasks(self):
        if self.answer_type != "keuze":
            return

        scene = self.scene()
        view = scene.views()[0].parent()
        template_json = getattr(view, "temp_template_json", None)

        for i, option in enumerate(self.options):
            # Maak nieuwe filtertaak aan
            filter_task = AnswerFilterItem(
                name=f"Filter: {option}",
                filter_uid=self.uid,
                filter_waarde=option,
                operator="=",
                schema=self.schema,
                uid=str(uuid.uuid4())
            )

            # Neem context van de parent popup over
            filter_task.set_field = self.set_field
            filter_task.set_target = self.set_target
            filter_task.set_target_uid = self.set_target_uid

            # Zet positie rechts naast de popup
            filter_task.setPos(self.pos() + QPointF(150, 60 * (i + 1)))
            scene.addItem(filter_task)

            # Voeg toe aan JSON
            if template_json is not None:
                template_json["blocks"] = [b for b in template_json["blocks"] if b["uid"] != filter_task.uid]
                template_json["blocks"].append(filter_task.to_json())

            # Verbind popup → filter
            connection = ConnectionItem(self, filter_task, label=option)
            scene.addItem(connection)
            if template_json is not None:
                template_json["connections"].append(connection.to_json())

    def generate_answer_blocks(self):
        from .block_items import AnswerFilterItem
        if not self.options:
            return
        scene = self.scene()
        start_pos = self.pos()
        offset_y = 80
        for i, opt in enumerate(self.options):
            block = AnswerFilterItem(
                name=f"Filter: {opt}",
                question=f"Antwoord is: {opt}",
                schema=self.schema,
                uid=str(uuid.uuid4())
            )
            block.filter_uid = self.uid
            block.filter_waarde = opt
            block.operator = "="
            block.setPos(start_pos.x() + 150, start_pos.y() + i * offset_y)
            scene.addItem(block)
            connection = ConnectionItem(self, block, label=opt)
            scene.addItem(connection)


class AnswerFilterItem(QGraphicsPolygonItem, BlockMixin):
    def __init__(self, name="Filtertaak", question="Wat is het antwoord?", color=QColor("lightyellow"),
                 schema="default", uid=None, filter_uid="", filter_waarde="", operator="="):
        points = [QPointF(0, -40), QPointF(-40, 0), QPointF(0, 40), QPointF(40, 0)]
        super().__init__(QPolygonF(points))
        self.question = question
        self.filter_uid = filter_uid
        self.filter_waarde = filter_waarde
        self.operator = operator
        self.set_field = None
        self.set_target = None
        self.set_target_uid = None
        self.init_block(name, color, schema, uid)

    def paint(self, painter, option, widget):
        painter.setBrush(QBrush(self.color))
        painter.setPen(QPen(Qt.black, 2))
        painter.drawPolygon(self.polygon())
        text = f"{self.operator} {self.filter_waarde}"
        painter.drawText(self.boundingRect(), Qt.AlignCenter, text)

    def show_context_menu(self, global_pos):
        menu = QMenu()
        prop_action = menu.addAction("Eigenschappen")
        delete_action = menu.addAction("Verwijderen")
        action = menu.exec(global_pos)
        if action == prop_action:
            dialog = BlockPropertiesDialog(self)
            if dialog.exec():
                dialog.apply_changes()
        elif action == delete_action:
            self.delete_item()

    def mouseDoubleClickEvent(self, event):
        dialog = BlockPropertiesDialog(self)
        if dialog.exec():
            dialog.apply_changes()
        super().mouseDoubleClickEvent(event)

    def to_json(self):
        return {
            "type": "filter",
            "name": self.name,
            "question": self.question,
            "filter_uid": self.filter_uid,
            "filter_waarde": self.filter_waarde,
            "operator": self.operator,
            "set_field": self.set_field,
            "set_target": self.set_target,
            "set_target_uid": self.set_target_uid,
            "color": self.color.name() if hasattr(self.color, "name") else self.color,
            "schema": self.schema,
            "pos": [self.pos().x(), self.pos().y()],
            "uid": self.uid
        }

    @staticmethod
    def from_json(data):
        item = AnswerFilterItem(
            name=data.get("name", ""),
            filter_uid=data.get("filter_uid", ""),
            filter_waarde=data.get("filter_waarde", ""),
            operator=data.get("operator", "=")
        )
        item.uid = data.get("uid", str(uuid.uuid4()))
        item.schema = data.get("schema", "")
        item.color = data.get("color", "#ffffe0")
        item.set_target = data.get("set_target")
        item.set_field = data.get("set_field")
        item.set_target_uid = data.get("set_target_uid")
        item.setPos(*data.get("pos", [0, 0]))

        # Voeg toe indien aanwezig (soms is er een overgeërfde 'question')
        if "question" in data:
            item.question = data["question"]

        return item

    def clone(self):
        clone = AnswerFilterItem(
            name=self.name,
            question=self.question,
            color=self.color,
            schema=self.schema,
            uid=str(uuid.uuid4())
        )
        clone.filter_uid = self.filter_uid
        clone.filter_waarde = self.filter_waarde
        clone.operator = self.operator
        return clone

class StartItem(PopupItem):
    def __init__(self, question="Wat is de projectnaam?", color=QColor("lightblue"), schema="default", uid=None):
        super().__init__(
            name="Starttaak",
            question=question,
            options=[],
            answer_type="tekst",
            color=color,
            schema=schema,
            uid=uid
        )

    def show_context_menu(self, global_pos):
        menu = QMenu()
        prop_action = menu.addAction("Eigenschappen")
        delete_action = menu.addAction("Verwijderen")
        action = menu.exec(global_pos)
        if action == prop_action:
            dialog = BlockPropertiesDialog(self)
            if dialog.exec():
                dialog.apply_changes()
        elif action == delete_action:
            self.delete_item()

    def mouseDoubleClickEvent(self, event):
        dialog = BlockPropertiesDialog(self)
        if dialog.exec():
            dialog.apply_changes()
        super().mouseDoubleClickEvent(event)

    def to_json(self):
        base = super().to_json()
        base["type"] = "start"
        return base

    @classmethod
    def from_json(cls, data):
        item = cls(
            question=data.get("question", "Wat is de projectnaam?"),
            color=QColor(data.get("color", "#add8e6")),
            schema=data.get("schema", "default"),
            uid=data.get("uid")
        )
        item.set_block_name(data.get("name", "Starttaak"))
        item.setPos(*data.get("pos", [0, 0]))
        return item

    def clone(self):
        return StartItem(
            question=self.question,
            color=self.color,
            schema=self.schema,
            uid=str(uuid.uuid4())
        )

class EndTaskItem(PopupItem):
    def __init__(self, name="Eindtaak", color=QColor("red"), schema="default", uid=None):
        super().__init__(
            name=name,
            question="Wil je het project afsluiten?",
            options=["ja"],
            answer_type="keuze",
            color=color,
            schema=schema,
            uid=uid
        )

    def show_context_menu(self, global_pos):
        menu = QMenu()
        prop_action = menu.addAction("Eigenschappen")
        delete_action = menu.addAction("Verwijderen")
        action = menu.exec(global_pos)
        if action == prop_action:
            dialog = BlockPropertiesDialog(self)
            if dialog.exec():
                dialog.apply_changes()
        elif action == delete_action:
            self.delete_item()

    def mouseDoubleClickEvent(self, event):
        dialog = BlockPropertiesDialog(self)
        if dialog.exec():
            dialog.apply_changes()
        super().mouseDoubleClickEvent(event)

    def to_json(self):
        base = super().to_json()
        base["type"] = "endtask"
        return base

    @classmethod
    def from_json(cls, data):
        item = cls(
            name=data.get("name", "Eindtaak"),
            color=QColor(data.get("color", "#ff0000")),
            schema=data.get("schema", "default"),
            uid=data.get("uid")
        )
        item.setPos(*data.get("pos", [0, 0]))
        return item

    def clone(self):
        return EndTaskItem(
            name=self.name,
            color=self.color,
            schema=self.schema,
            uid=str(uuid.uuid4())
        )
