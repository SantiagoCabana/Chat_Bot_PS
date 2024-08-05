#structure_message_ui.py
import os
from PyQt5.QtWidgets import QMessageBox, QScrollArea, QPushButton, QVBoxLayout, QHBoxLayout, QGraphicsView, QGraphicsScene, QGraphicsItem
from PyQt5.QtCore import Qt, QPointF, QRectF,QLineF
from PyQt5.QtGui import QPainter, QPen, QPainterPath, QBrush, QColor, QWheelEvent
import random
import xml.etree.ElementTree as ET
from functions.f_structure import guardar_pos_flujo, cargar_pos_flujo

class MovableWidget(QGraphicsItem):
    def __init__(self, MainUI, color, can_delete=True, widget_id=None):
        super().__init__()
        self.MainUI = MainUI
        self.color = QColor(color)
        self.can_delete = can_delete
        self.widget_id = widget_id
        self.opciones = []
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

            # Verificar colisiones con otros widgets
            for item in self.scene().items():
                if item is not self and isinstance(item, MovableWidget):  # Solo verificar colisiones con otros widgets
                    # Crear un rectángulo de colisión en la nueva posición
                    new_rect = self.boundingRect().translated(new_pos)
                    if new_rect.intersects(item.boundingRect().translated(item.pos())):
                        return self.pos()  # Si hay colisión, no mover el widget

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
        self.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        #llamada a la funcion para crear un fondo cuadriculado
        self.setBackgroundBrush(QBrush(Qt.white))


    #funcion para crear un fondo cuadriculado fondo oscuro y encima lineas claras y cuadros semi grandes para mejor visualizacion, griss claro y lineas semi oscuras las lineas no se deben de crusar uno encima de otro pero deben de mantener su patron cuadrado
    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        # Aumentar el tamaño de la cuadrícula
        grid_size = 100
        # Establecer el color de fondo a un gris más claro
        painter.fillRect(rect, QColor(200, 200, 200))
        left = int(rect.left()) - (int(rect.left()) % grid_size)
        top = int(rect.top()) - (int(rect.top()) % grid_size)
        lines = []
        for x in range(left, int(rect.right()), grid_size):
            lines.append(QLineF(x, rect.top(), x, rect.bottom()))
        for y in range(top, int(rect.bottom()), grid_size):
            lines.append(QLineF(rect.left(), y, rect.right(), y))
        # Establecer el color de las líneas de la cuadrícula a un gris más oscuro
        painter.setPen(QPen(QColor(150, 150, 150), 1))
        painter.drawLines(lines)

    #agregar limites para el zoom y deszoom
    def wheelEvent(self, event: QWheelEvent):
        zoom_factor = 1.5
        max_zoom = 1.0  # Límite máximo de zoom
        min_zoom = 0.15  # Límite mínimo de zoom
    
        current_transform = self.transform()
        current_scale = current_transform.m11()  # Obtener el factor de escala actual
    
        if event.angleDelta().y() > 0:  # Zoom in
            if current_scale * zoom_factor <= max_zoom:
                self.scale(zoom_factor, zoom_factor)
        else:  # Zoom out
            if current_scale / zoom_factor >= min_zoom:
                self.scale(1 / zoom_factor, 1 / zoom_factor)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.centerOn(0, 0)

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

    save_button = QPushButton("Guardar")
    save_button.clicked.connect(lambda: guardar_pos_flujo('DATA/resource/xml/flujo.xml', MainUI.widgets))
    button_layout.addWidget(save_button)

    reset_button = QPushButton("Eliminar Todo")
    reset_button.clicked.connect(lambda: reiniciar_todo(MainUI))
    button_layout.addWidget(reset_button)

    undo_button = QPushButton("Deshacer Cambios")
    undo_button.clicked.connect(lambda: MainUI.undo_changes(MainUI))
    button_layout.addWidget(undo_button)

    MainUI.scene = QGraphicsScene(MainUI)
    MainUI.scene.setSceneRect(0, 0, 2000, 2000)
    MainUI.view = ZoomableGraphicsView(MainUI.scene)
    MainUI.view.setSceneRect(0, 0, 2000, 2000)
    main_layout.addWidget(MainUI.view)
    central_widget = QScrollArea() 
    central_widget.setLayout(main_layout)

    MainUI.cargar_flujo(MainUI)


    return central_widget

# función para cargar los flujo
def cargar_flujo(MainUI):
    if os.path.exists('DATA/resource/xml/flujo.xml'):
        widgets = cargar_pos_flujo('DATA/resource/xml/flujo.xml')
        if widgets:
            for widget in widgets:
                new_widget = MovableWidget(MainUI, widget['color'], 
                                           can_delete=widget['can_delete'],
                                           widget_id=widget['id'])
                new_widget.setPos(widget['x'], widget['y'])
                MainUI.scene.addItem(new_widget)
                MainUI.widgets.append(new_widget)
                for opcion in widget['opciones']:
                    new_widget.opciones.append(opcion)
            
            # Check if there are any non-None widget_ids
            non_none_ids = [widget.widget_id for widget in MainUI.widgets if widget.widget_id is not None]
            
            if non_none_ids:
                # If there are non-None ids, set next_widget_id to max + 1
                MainUI.next_widget_id = max(non_none_ids) + 1
            else:
                # If all ids are None, set next_widget_id to 1
                MainUI.next_widget_id = 1
            
            MainUI.update_connections(MainUI)
    else:
        MainUI.add_widget(MainUI, can_delete=False, color='black')
        guardar_pos_flujo('DATA/resource/xml/flujo.xml', MainUI.widgets, confiramcion=False)

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

#funcion para contar cuantos widgets con id hay en el flujo.xml
def count_widgets(path='DATA/resource/xml/flujo.xml'):
    count = 0
    if os.path.exists(path):
        tree = ET.parse(path)
        root = tree.getroot()
        for widget in root.findall('widget'):
            if widget.get('id') != 'None':
                count += 1
    return count

#funcion para eliminar el ultimo widget pero debe de contar cuantos widget hay en el flujo.xml para poder eliminar el ultimo
def delete_last_widget(MainUI):
    widget_count = count_widgets()
    print(f"Número de widgets en el XML: {widget_count}")
    print(f"Número de widgets en MainUI.widgets: {len(MainUI.widgets)}")

    print("Widgets actuales:")
    for widget in MainUI.widgets:
        print(f"ID: {widget.widget_id}, Can delete: {widget.can_delete}")

    if len(MainUI.widgets) > 1:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Question)
        msg.setText("¿Estás seguro de eliminar el último widget?")
        msg.setWindowTitle("Eliminar Widget")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        
        if msg.exec() == QMessageBox.No:
            return
        
        # Buscar el widget con el ID más alto que sea eliminable
        widget_to_delete = None
        for widget in MainUI.widgets:
            if widget.can_delete:
                if widget_to_delete is None or (widget.widget_id is not None and widget_to_delete.widget_id is not None and widget.widget_id > widget_to_delete.widget_id):
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

#funcion para deshacer todos los cambios realizados osea eliminar todos los widgets y cargar los widgets del flujo.xml
def undo_changes(MainUI):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Question)
    msg.setText("¿Estás seguro de deshacer todos los cambios?")
    msg.setWindowTitle("Deshacer Cambios")
    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    
    if msg.exec() == QMessageBox.No:
        return
    
    for widget in MainUI.widgets:
        MainUI.scene.removeItem(widget)
    MainUI.widgets.clear()
    MainUI.next_widget_id = 1
    MainUI.update_connections(MainUI)
    MainUI.cargar_flujo(MainUI)

#funcion para eliminar todos los widgets y el flujos.xml el cual al eliminar todos los widgets y sus conexiones creara el principal
def reiniciar_todo(MainUI):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Question)
    msg.setText("¿Estás seguro de eliminar todos los widgets?")
    msg.setWindowTitle("Eliminar Todo")
    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    
    if msg.exec() == QMessageBox.No:
        return
    
    for widget in MainUI.widgets:
        MainUI.scene.removeItem(widget)
    MainUI.widgets.clear()
    MainUI.next_widget_id = 1
    MainUI.update_connections(MainUI)
    
    # Eliminar el archivo XML
    if os.path.exists('DATA/resource/xml/flujo.xml'):
        os.remove('DATA/resource/xml/flujo.xml')
    
    # Añadir el primer widget
    MainUI.add_widget(MainUI, can_delete=False, color='black')

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
    #se cargaran solo los nombres de los xml en la carpeta DATA/resource/xml en una lista lista selecionable
    lista_xml = os.listdir('DATA/resource/xml')
    return lista_xml
