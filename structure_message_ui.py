#structure_message_ui.py
import sys, os
from PyQt5.QtWidgets import QListWidget, QMessageBox, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QGraphicsView, QGraphicsScene, QGraphicsItem
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QPainter, QPen, QPainterPath, QBrush, QColor, QWheelEvent
import random
from functions.f_structure import cargar_datos_xml

class MovableWidget(QGraphicsItem):
    def __init__(self, MainUI, color, can_delete=True, widget_id=None):
        super().__init__()
        self.MainUI = MainUI
        self.color = QColor(color)
        self.can_delete = can_delete
        self.widget_id = widget_id
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

    def boundingRect(self):
        return QRectF(0, 0, 50, 50)

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(Qt.black, 2))
        painter.setBrush(QBrush(self.color))
        painter.drawRect(0, 0, 50, 50)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            rect = self.scene().sceneRect()
            new_pos = value
            new_pos.setX(min(rect.right() - self.boundingRect().width(), max(new_pos.x(), rect.left())))
            new_pos.setY(min(rect.bottom() - self.boundingRect().height(), max(new_pos.y(), rect.top())))
            if self.scene():
                self.MainUI.update_connections(self.MainUI)  # Pasar MainUI como argumento
            return new_pos
        return super().itemChange(change, value)

class ZoomableGraphicsView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setDragMode(QGraphicsView.ScrollHandDrag)

    def wheelEvent(self, event: QWheelEvent):
        zoom_factor = 1.2
        if event.angleDelta().y() > 0:
            self.scale(zoom_factor, zoom_factor)
        else:
            self.scale(1 / zoom_factor, 1 / zoom_factor)

def container_estructure(MainUI):
    main_layout = QVBoxLayout()

    button_layout = QHBoxLayout()
    main_layout.addLayout(button_layout)

    add_button = QPushButton("Agregar Widget")
    add_button.clicked.connect(lambda: MainUI.add_widget(MainUI))
    button_layout.addWidget(add_button)

    delete_button = QPushButton("Eliminar Último Widget")
    delete_button.clicked.connect(lambda: MainUI.delete_last_widget(MainUI))
    button_layout.addWidget(delete_button)

    MainUI.scene = QGraphicsScene(MainUI)
    MainUI.scene.setSceneRect(-20, 0, 2000, 2000)
    MainUI.view = ZoomableGraphicsView(MainUI.scene)
    main_layout.addWidget(MainUI.view)

    # Añadir el primer widget (principal)
    MainUI.add_widget(MainUI, can_delete=False, color='black')
    MainUI.view.fitInView(MainUI.scene.sceneRect(), Qt.KeepAspectRatio)

    central_widget = QWidget()
    central_widget.setLayout(main_layout)
    
    return central_widget

def add_widget(MainUI, can_delete=True, color=None):
    if color is None:
        color = generate_unique_color(MainUI)  # Pasar MainUI como argumento
    
    if not MainUI.widgets:
        # Primer widget
        new_widget = MovableWidget(MainUI, color, can_delete=False, widget_id=None)
    else:
        # Widgets subsecuentes
        widget_id = MainUI.next_widget_id
        new_widget = MovableWidget(MainUI, color, can_delete=True, widget_id=widget_id)
        MainUI.next_widget_id += 1
    
    MainUI.scene.addItem(new_widget)
    new_widget.setPos(50 + len(MainUI.widgets) * 60, 50)
    MainUI.widgets.append(new_widget)
    MainUI.update_connections(MainUI)
    print(f"Widget añadido: {new_widget.widget_id}, can_delete: {new_widget.can_delete}")

def generate_unique_color(MainUI):
    while True:
        color = QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        if color not in [widget.color for widget in MainUI.widgets]:
            return color

def delete_last_widget(MainUI):
    #Mensaje de Confirmacion
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Question)
    msg.setText("¿Estas seguro de eliminar el ultimo widget?")
    msg.setWindowTitle("Eliminar Widget")
    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    # si es si continua con la eliminacion pero si es no no hace nada
    if msg.exec() == QMessageBox.No:
        return
        
    if len(MainUI.widgets) > 1:
        # Buscar el widget con el ID más alto que sea eliminable
        widget_to_delete = None
        for widget in MainUI.widgets:
            if widget.can_delete and (widget_to_delete is None or widget.widget_id > widget_to_delete.widget_id):
                widget_to_delete = widget
        
        if widget_to_delete:
            MainUI.widgets.remove(widget_to_delete)
            MainUI.scene.removeItem(widget_to_delete)
            MainUI.update_connections(MainUI)
            print(f"Widget eliminado: {widget_to_delete.widget_id}")
        else:
            print("No hay widgets eliminables.")
    else:
        print("No hay suficientes widgets para eliminar.")

def update_connections(MainUI):
    for connection in MainUI.connections:
        MainUI.scene.removeItem(connection)
    MainUI.connections.clear()

    for i in range(1, len(MainUI.widgets)):
        path = create_connection_path(MainUI.widgets[i-1], MainUI.widgets[i])  # Pasar los argumentos correctamente
        connection = MainUI.scene.addPath(path, QPen(Qt.black, 2))
        MainUI.connections.append(connection)

def create_connection_path(widget1, widget2):  # Asegurarse de que la función acepte los argumentos correctos
    w1_pos = widget1.pos()
    w2_pos = widget2.pos()
    
    # Determine which sides to connect
    if abs(w1_pos.x() - w2_pos.x()) > abs(w1_pos.y() - w2_pos.y()):
        # Connect horizontal sides
        if w1_pos.x() < w2_pos.x():
            start = w1_pos + QPointF(50, 25)
            end = w2_pos + QPointF(0, 25)
        else:
            start = w1_pos + QPointF(0, 25)
            end = w2_pos + QPointF(50, 25)
    else:
        # Connect vertical sides
        if w1_pos.y() < w2_pos.y():
            start = w1_pos + QPointF(25, 50)
            end = w2_pos + QPointF(25, 0)
        else:
            start = w1_pos + QPointF(25, 0)
            end = w2_pos + QPointF(25, 50)

    path = QPainterPath()
    path.moveTo(start)

    # Calculate control points
    ctrl1 = QPointF((start.x() + end.x()) / 2, start.y())
    ctrl2 = QPointF((start.x() + end.x()) / 2, end.y())

    path.cubicTo(ctrl1, ctrl2, end)
    return path

def load_names_xml(MainUI):
    #se cargaran solo los nombres de los xml en la carpeta data/xml en una lista lista selecionable
    lista_xml = os.listdir('data/xml')
    return lista_xml