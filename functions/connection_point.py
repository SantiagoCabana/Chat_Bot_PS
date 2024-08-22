from PyQt5.QtWidgets import QGraphicsItem, QMenu, QAction, QWidget, QVBoxLayout, QPushButton,QLayout
from PyQt5.QtCore import QRectF, Qt, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QColor, QBrush, QPen, QPolygonF
from PyQt5.QtCore import QPointF


class ConnectionPoint(QGraphicsItem):
    def __init__(self, parent, side, index):
        super().__init__(parent)
        self.side = side
        self.index = index
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self.rect = QRectF(-5, -5, 10, 10)
        self.connected_to = None

    def boundingRect(self):
        return self.rect

    def paint(self, painter, option, widget):
        painter.setPen(QPen(Qt.black, 1))
        painter.setBrush(QBrush(Qt.red if self.connected_to else Qt.yellow))
        painter.drawEllipse(self.rect)

class DesplegableArea(QWidget):
    def __init__(self, title, content, parent=None):
        super().__init__(parent)
        
        self.title = title
        self.content = content
        
        # Layout principal
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Botón para desplegar/ocultar
        self.toggle_button = QPushButton(self.title)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)
        self.toggle_button.clicked.connect(self.toggle_area)
        self.main_layout.addWidget(self.toggle_button)
        
        # Área desplegable
        self.expandable_area = QWidget()
        self.expandable_area.setMaximumHeight(0)
        self.expandable_layout = QVBoxLayout(self.expandable_area)
        self.expandable_layout.setContentsMargins(0, 0, 0, 0)
        
        # Agrega el contenido al área desplegable
        self.add_content(self.content)
        
        # Añade el área desplegable al layout principal
        self.main_layout.addWidget(self.expandable_area)
        
        # Configura la animación
        self.animation = QPropertyAnimation(self.expandable_area, b"maximumHeight")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        
    def add_content(self, content):
        if isinstance(content, QWidget):
            self.expandable_layout.addWidget(content)
        elif isinstance(content, QLayout):
            self.expandable_layout.addLayout(content)
        elif isinstance(content, (list, tuple)):
            for item in content:
                self.add_content(item)
        else:
            raise TypeError("El contenido debe ser un QWidget, QLayout o una lista/tupla de estos.")

    def toggle_area(self):
        try:
            if self.toggle_button.isChecked():
                self.animation.setStartValue(0)
                self.animation.setEndValue(self.expandable_area.sizeHint().height())
            else:
                self.animation.setStartValue(self.expandable_area.height())
                self.animation.setEndValue(0)
            
            self.animation.start()
        except Exception as e:
            print(f"Error al desplegar el área: {e}")

class MovableWidget(QGraphicsItem):
    def __init__(self, parent, color, widget_id, can_delete, opciones, connections, tipo="rectangle",nombre=None):
        super().__init__()
        self.parent = parent
        self.nombre = nombre
        self.color = QColor(color)
        self.widget_id = widget_id
        self.can_delete = can_delete
        self.opciones = opciones
        self.connections = connections
        self.connections = []  # Agregamos este atributo para mantener las conexiones
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        self.setZValue(1)
        self.connected_widgets = set()
        self.tipo = tipo
        self.crear_tipo(tipo)
        self.connection_points = {"left": [], "right": [], "top": [], "bottom": []}

    def add_connection_point(self, side):
        point = ConnectionPoint(self, side, len(self.connection_points[side]))
        self.connection_points[side].append(point)
        self.update_connection_point_position(side)
        print(f"Added connection point on {side} side")
        return point

    def crear_tipo(self, tipo):
        if tipo == "rectangle":
            # Rectángulo más grande y con forma más rectangular
            self.rect = QRectF(-50, -75, 100, 150)
        elif tipo == "triangle":
            # Triángulo rotado 90 grados a la derecha
            self.polygon = QPolygonF([QPointF(-50, -50), QPointF(50, 0), QPointF(-50, 50)])
            self.rect = QRectF(-50, -50, 100, 100)  # Bounding box cuadrada
        elif tipo == "square":
            self.rect = QRectF(-50, -50, 100, 100)
        elif tipo == "pentagon":
            # Pentágono
            self.polygon = QPolygonF([
                QPointF(0, -50), QPointF(47, -15), QPointF(29, 40),
                QPointF(-29, 40), QPointF(-47, -15)
            ])
            self.rect = QRectF(-50, -50, 100, 100)  # Bounding box cuadrada

    def update_connection_point_position(self, side):
        if side in self.connection_points:
            points = self.connection_points[side]
            bounding_rect = self.boundingRect()
            center = bounding_rect.center()
            
            if self.tipo == "triangle" or self.tipo == "pentagon":
                total_points = len(points)
                for i, point in enumerate(points):
                    if side == 'left':
                        y_offset = (bounding_rect.height() / (total_points + 1)) * (i + 1)
                        point.setPos(bounding_rect.left(), bounding_rect.top() + y_offset)
                    elif side == 'right':
                        y_offset = (bounding_rect.height() / (total_points + 1)) * (i + 1)
                        point.setPos(bounding_rect.right(), bounding_rect.top() + y_offset)
                    elif side == 'top':
                        x_offset = (bounding_rect.width() / (total_points + 1)) * (i + 1)
                        point.setPos(bounding_rect.left() + x_offset, bounding_rect.top())
                    elif side == 'bottom':
                        x_offset = (bounding_rect.width() / (total_points + 1)) * (i + 1)
                        point.setPos(bounding_rect.left() + x_offset, bounding_rect.bottom())
            else:
                total_points = len(points)
                width = bounding_rect.width()
                height = bounding_rect.height()
                for i, point in enumerate(points):
                    if side == 'left':
                        y_offset = (height / (total_points + 1)) * (i + 1)
                        point.setPos(bounding_rect.left(), bounding_rect.top() + y_offset)
                    elif side == 'right':
                        y_offset = (height / (total_points + 1)) * (i + 1)
                        point.setPos(bounding_rect.right(), bounding_rect.top() + y_offset)
                    elif side == 'top':
                        x_offset = (width / (total_points + 1)) * (i + 1)
                        point.setPos(bounding_rect.left() + x_offset, bounding_rect.top())
                    elif side == 'bottom':
                        x_offset = (width / (total_points + 1)) * (i + 1)
                        point.setPos(bounding_rect.left() + x_offset, bounding_rect.bottom())
            self.update()

    def update_all_connection_points(self):
        for side in self.connection_points:
            self.update_connection_point_position(side)

    def remove_connection_points(self, specific_point=None):
        if specific_point:
            if specific_point.connected_to:
                self.scene().removeItem(specific_point.connected_to)
                specific_point.connected_to = None
            self.scene().removeItem(specific_point)
            for points in self.connection_points.values():
                if specific_point in points:
                    points.remove(specific_point)
                    break
        else:
            for points in self.connection_points.values():
                for point in points:
                    if point.connected_to:
                        self.scene().removeItem(point.connected_to)
                        point.connected_to = None
                    self.scene().removeItem(point)
            self.connection_points.clear()

    def boundingRect(self):
        return self.rect

    def paint(self, painter, option, widget):
        # Dibujar las líneas de conexión detrás del widget
        for side, points in self.connection_points.items():
            for point in points:
                painter.setPen(QPen(Qt.black, 1, Qt.DashLine))
                painter.drawLine(point.pos(), self.boundingRect().center())

        painter.setBrush(QBrush(self.color))
        painter.setPen(QPen(Qt.black, 2))
        
        if self.tipo == "triangle" or self.tipo == "pentagon":
            painter.drawPolygon(self.polygon)
        elif self.tipo == "rectangle" or self.tipo == "square":
            painter.drawRoundedRect(self.rect, 10, 10)
        
        painter.setPen(QPen(Qt.black))
        painter.drawText(self.boundingRect(), Qt.AlignCenter, str(self.nombre))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.parent.connecting_widget:
                self.parent.connect_widgets(self.parent.connecting_widget, self)
                self.parent.connecting_widget = None
                self.parent.view.setCursor(Qt.ArrowCursor)
                return
            else:
                self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)
        event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setCursor(Qt.ArrowCursor)
        super().mouseReleaseEvent(event)
        event.accept()

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            rect = self.scene().sceneRect()
            new_pos = value
            new_pos.setX(min(rect.right() - self.boundingRect().width(), max(new_pos.x(), rect.left())))
            new_pos.setY(min(rect.bottom() - self.boundingRect().height(), max(new_pos.y(), rect.top())))

            for item in self.scene().items():
                if item is not self and isinstance(item, MovableWidget):
                    new_rect = self.boundingRect().translated(new_pos)
                    if new_rect.intersects(item.boundingRect().translated(item.pos())):
                        return self.pos()

            for side in self.connection_points:
                self.update_connection_point_position(side)
            if self.parent:
                self.parent.update_connections()
            return new_pos
        return super().itemChange(change, value)

    def contextMenuEvent(self, event):
        menu = QMenu()

        # Opciones básicas
        edit_action = QAction("Editar", self.parent)
        edit_action.triggered.connect(lambda: self.parent.show_edit_layout(self))
        menu.addAction(edit_action)

        delete_action = QAction("Eliminar", self.parent)
        delete_action.triggered.connect(lambda: self.parent.delete_widget(self))
        menu.addAction(delete_action)

        connect_action = QAction("Conectar", self.parent)
        connect_action.triggered.connect(lambda: self.parent.start_connecting(self))
        menu.addAction(connect_action)

        # Solo agregar la opción de "Eliminar Conexión" si hay conexiones
        if self.connected_widgets:
            remove_conn_submenu = menu.addMenu("Eliminar Conexión")
            for connected_widget in self.connected_widgets:
                action = QAction(f"Con Widget {connected_widget.widget_id}", self.parent)
                action.triggered.connect(lambda checked, w=connected_widget: self.parent.remove_connection(self, w))
                remove_conn_submenu.addAction(action)

        menu.exec(event.screenPos())

def crear_widget(parent, color, widget_id, tipo):
    widget = MovableWidget(parent, color, widget_id, tipo)
    
    # Dependiendo del tipo, se agregan puntos de conexión en diferentes lados
    if tipo == "rectangle" or tipo == "square":
        widget.add_connection_point("left")
        widget.add_connection_point("right")
        widget.add_connection_point("top")
        widget.add_connection_point("bottom")
    elif tipo == "triangle":
        widget.add_connection_point("left")
        widget.add_connection_point("top")
        widget.add_connection_point("bottom")
    elif tipo == "scuare":
        widget.add_connection_point("left")
        widget.add_connection_point("right")
        widget.add_connection_point("top")
        widget.add_connection_point("bottom")
    
    return widget
