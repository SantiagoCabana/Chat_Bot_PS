import os
from PyQt5.QtWidgets import (QLabel, QMessageBox, QScrollArea, QPushButton, QVBoxLayout, QHBoxLayout,
                             QGraphicsView, QGraphicsScene, QGraphicsItem, QMenu, QAction, QGraphicsProxyWidget,
                             QApplication, QLineEdit, QTextEdit, QComboBox, QFileDialog, QLayout,
                             QListWidget, QWidget,QGraphicsLineItem,QGraphicsPathItem, QGraphicsRectItem
                             , QGraphicsTextItem, QGraphicsEllipseItem, QGraphicsWidget, QGraphicsLayoutItem
                             ,QCheckBox,QFrame,QSizePolicy,QScrollArea,QListWidgetItem,QAbstractItemView)

from PyQt5.QtCore import Qt, QPointF, QRectF, QLineF, QSizeF, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPainter, QPen, QPainterPath, QBrush, QColor, QWheelEvent, QMouseEvent
import random
import xml.etree.ElementTree as ET
#importar el area zoomable
from functions.zoom_area import ZoomableGraphicsView
from functions.connection_point import MovableWidget, DesplegableArea
from functions.f_structure import guardar_pos_flujo, cargar_pos_flujo, guardar_datos_xml, cargar_datos_xml

class ConditionWidget:
    def __init__(self, parent_layout, action_names=None, condition_names=None, deletable=True):
        self.frame = QFrame()
        self.frame.setFrameShape(QFrame.Panel)
        self.layout = QVBoxLayout(self.frame)
        self.condition_count = 0
        self.condition_limit = 5
        self.deletable = deletable
        self.parent_layout = parent_layout
        self.action_names = action_names if action_names is not None else []
        self.condition_names = condition_names if condition_names is not None else []

        self.setup_ui()

    def setup_ui(self):
        area_horizontal1 = QHBoxLayout()
        nombre = QLineEdit("Nombre de la condición")

        add_condition_button = QPushButton("➕")
        add_condition_button.clicked.connect(lambda: self.add_condition())

        area_horizontal1.addWidget(nombre)
        area_horizontal1.addWidget(add_condition_button)

        if self.deletable:
            delete_condition_button = QPushButton("❌")
            delete_condition_button.clicked.connect(lambda: self.remove_self())
            area_horizontal1.addWidget(delete_condition_button)

        self.layout.addLayout(area_horizontal1)
        self.area_horizontal2 = QHBoxLayout()
        self.add_condition(deletable=False)

        scroll_area = QScrollArea()
        scroll_content = QWidget()
        scroll_content.setLayout(self.area_horizontal2)

        scroll_area.setWidget(scroll_content)
        scroll_area.setWidgetResizable(True)

        self.layout.addWidget(scroll_area)

        horizontal4 = QHBoxLayout()
        action = QComboBox()
        for name in self.action_names:
            action.addItem(name)
        nombre = QLabel("Acción a disparar:")
        nombre.setMaximumWidth(100)
        horizontal4.addWidget(nombre)
        horizontal4.addWidget(action)
        self.layout.addLayout(horizontal4)

        self.parent_layout.insertWidget(self.parent_layout.count() - 1, self.frame)

    def add_condition(self, deletable=True):
        if self.condition_count >= self.condition_limit:
            return

        Qframe1 = QFrame()
        Qframe1.setFrameShape(QFrame.Panel)
        Qframe1.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        condition_layout = QHBoxLayout()
        condition_edit = QLineEdit()

        condition_layout.addWidget(condition_edit)

        if deletable:
            delete_condition_button = QPushButton("❌")
            delete_condition_button.setMaximumWidth(30)
            delete_condition_button.clicked.connect(lambda: self.remove_condition(Qframe1))
            condition_layout.addWidget(delete_condition_button)

        tipo = QComboBox()
        tipo.addItem("Presente")
        tipo.addItem("No Presente")
        tipo.addItem("Opcional")
        condition_edit.setPlaceholderText("Condicion")

        condition_layout_V = QVBoxLayout()
        condition_layout_V.addWidget(tipo)
        condition_layout_V.addLayout(condition_layout)

        Qframe1.setLayout(condition_layout_V)
        self.area_horizontal2.addWidget(Qframe1)

        self.condition_count += 1

    def remove_condition(self, condition_widget):
        self.area_horizontal2.removeWidget(condition_widget)
        condition_widget.deleteLater()
        self.condition_count -= 1

    def remove_self(self):
        self.parent_layout.removeWidget(self.frame)
        self.frame.deleteLater()

class StructureUI(QWidget):
    def __init__(self, MainUI):
        super().__init__()
        self.MainUI = MainUI
        self.widgets = []
        self.connections = []
        self.connecting_point = None
        self.is_connecting = False
        self.next_widget_id = 1
        self.connecting_widget = None
        self.setup_ui()
        self.add_widget_movable("gray", widget_id=None,tipo="pentagon")
        self.show_structure_area()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)

        self.structure_layout = QVBoxLayout()
        self.setup_structure_area()
        main_layout.addLayout(self.structure_layout)

        self.edit_layout = QVBoxLayout()
        self.setup_edit_area()  # Asegúrate de que esto se llame aquí
        main_layout.addLayout(self.edit_layout)

        self.edit_layout_welcome = QVBoxLayout()
        self.setup_edit_area_welcome()
        main_layout.addLayout(self.edit_layout_welcome)

        self.edit_layout_conditions = QVBoxLayout()
        self.setup_conditions_area_triangle()
        main_layout.addLayout(self.edit_layout_conditions)

    def clear_edit_layout(self):
        self.edit_id_label.setText("")
        self.edit_message.clear()
        self.edit_id_label_w.setText("")
        self.edit_message_w.clear()
        self.quick_response_name.clear()

    def ocultar_areas(self):
        self.structure_widget.hide()
        self.edit_widget.hide()
        self.edit_widget_welcome.hide()
        self.conditions_area_widget.hide()

    def show_edit_layout_welcome(self):
        self.ocultar_areas()
        self.edit_widget_welcome.show()
    
    def show_edit_layout_conditions(self):
        self.ocultar_areas()
        self.conditions_area_widget.show()
    
    def show_structure_area(self):
        self.ocultar_areas()
        self.structure_widget.show()

    def show_edit_layout(self, widget):
        self.clear_edit_layout()
        self.ocultar_areas()
        
        if widget.widget_id is None:
            # Colocar el id en el QLineEdit que será el id del widget
            self.edit_id_label_w.setText("Nuevo Widget")
            self.edit_message_w.setPlainText("Aquí va la configuración especial")
            self.show_edit_layout_welcome()
        elif widget.tipo == "triangle":
            self.edit_id_label.setText("Editando Widget triangle")
            self.edit_message.setPlainText("Aquí va la configuración especial")
            self.show_edit_layout_conditions()
        elif widget.tipo == "square":
            self.edit_id_label.setText("Editando Widget square")
            self.edit_message.setPlainText("Aquí va la configuración especial")
            self.edit_widget.show()
        else:
            self.edit_id_label.setText(f"Editando Widget {widget.widget_id}")
            self.edit_message.setPlainText("\n".join(widget.connections))
            self.edit_widget.show()

    def setup_edit_area_welcome(self):
        self.edit_widget_welcome = QWidget()
        edit_layout_welcome = QVBoxLayout()
        self.edit_widget_welcome.setLayout(edit_layout_welcome)
    
        # Áreas de configuración
        self.areas_edit_w = QVBoxLayout()
    
        self.edit_id_label_w = QLabel()
        edit_id_label_w = QLabel("Titulo del Widget:")
        self.areas_edit_w.addWidget(edit_id_label_w)
    
        self.edit_id_label_w = QLineEdit()
        self.areas_edit_w.addWidget(self.edit_id_label_w)
    
        # Mensaje de bienvenida
        self.label_edit_w = QLabel("Mensaje de Bienvenida:")
        self.areas_edit_w.addWidget(self.label_edit_w)
    
        # Checkbox para habilitar respuesta rápida
        self.quick_response_checkbox = QCheckBox("Usar respuesta rápida")
        self.quick_response_checkbox.stateChanged.connect(self.toggle_quick_response)
        self.areas_edit_w.addWidget(self.quick_response_checkbox)
    
        # QLineEdit para el nombre de la respuesta rápida
        self.quick_response_name = QLineEdit()
        self.quick_response_name.setPlaceholderText("Nombre de la respuesta rápida")
        self.quick_response_name.setVisible(False)
        self.areas_edit_w.addWidget(self.quick_response_name)
    
        # QTextEdit para el mensaje de bienvenida
        self.edit_message_w = QTextEdit()
        #alto minimo del textedit
        self.edit_message_w.setMinimumHeight(250)
        self.areas_edit_w.addWidget(self.edit_message_w)

        # Widgets
        self.upload_layout = QHBoxLayout()
        self.b_layout = QVBoxLayout()
        self.edit_file_button_w = QPushButton("Subir Archivo")
        self.cancelar_button_w = QPushButton("Cancelar")
    
        self.b_layout.addWidget(self.edit_file_button_w)
        self.b_layout.addWidget(self.cancelar_button_w)
    
        self.upload_layout.addStretch()
        self.upload_layout.addLayout(self.b_layout)
    
        # Convertir el b_layout en un widget
        self.widget_layout = QWidget()
        self.widget_layout.setLayout(self.upload_layout)
        
        # Archivos
        self.desplegador_w = DesplegableArea("Desplegar", [self.widget_layout])
        self.areas_edit_w.addWidget(self.desplegador_w)
    
        # Condiciones de script
        self.desplegador_script_w = DesplegableArea("Script", [QLabel("Aquí va el script")])
        self.areas_edit_w.addWidget(self.desplegador_script_w)
    
        # Área configuración lateral
        self.areas_edit_w_welcome = QHBoxLayout()
        self.list_config_welcome = QVBoxLayout()
        self.list_config_welcome.addWidget(QLabel("Configuraciones"))
        self.list_config_w = QListWidget()
        #ancho maximo de la lista de configuraciones
        self.list_config_w.setMaximumWidth(100)
        self.list_config_welcome.addWidget(self.list_config_w)
    
        # Crear un QWidget y establecer su layout
        self.areas_edit_w_widget = QWidget()
        self.areas_edit_w_widget.setLayout(self.areas_edit_w)
        
        # Configurar el QScrollArea con el nuevo QWidget
        self.scroll_areas_w = QScrollArea()
        self.scroll_areas_w.setWidgetResizable(True)
        self.scroll_areas_w.setWidget(self.areas_edit_w_widget)
        
        # Añadir el QScrollArea y el layout al layout principal
        self.areas_edit_w_welcome.addWidget(self.scroll_areas_w)
        self.areas_edit_w_welcome.addLayout(self.list_config_welcome)
    
        # Botones
        self.button_layout_w = QHBoxLayout()
        self.edit_save_button_w = QPushButton("Guardar Cambios")
        self.button_layout_w.addWidget(self.edit_save_button_w)
        self.cancelar_button_w = QPushButton("Cancelar")
        self.cancelar_button_w.clicked.connect(self.cancelar)
        self.button_layout_w.addWidget(self.cancelar_button_w)
    
        edit_layout_welcome.addLayout(self.areas_edit_w_welcome)
        edit_layout_welcome.addLayout(self.button_layout_w)
    
        self.edit_layout_welcome.addWidget(self.edit_widget_welcome)
    

    def setup_conditions_area_triangle(self):
        self.conditions_area_widget = QWidget()
        edit_layout_conditions = QVBoxLayout()
        self.conditions_area_widget.setLayout(edit_layout_conditions)
    
        # Áreas de configuración
        areas_edit_condition = QVBoxLayout()
        self.conditions_label = QLabel("Condiciones")
        areas_edit_condition.addWidget(self.conditions_label)
    
        # Botón para añadir condiciones a la lista
        self.add_condition_button = QPushButton("Añadir Condición")
        self.add_condition_button.clicked.connect(self.condicion_widget)
        areas_edit_condition.addWidget(self.add_condition_button)
    
        # Lista de condiciones
        self.conditions_list = QVBoxLayout()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        self.conditions_list.addStretch()  # Añadir el resorte al final
        scroll_content.setLayout(self.conditions_list)
    
        scroll_area.setWidget(scroll_content)
        areas_edit_condition.addWidget(scroll_area)
    
        # Agregar áreas de configuración al layout principal
        edit_layout_conditions.addLayout(areas_edit_condition)
    
        # Botones
        button_layout_conditions = QHBoxLayout()
        self.edit_save_button_conditions = QPushButton("Guardar Cambios")
        button_layout_conditions.addWidget(self.edit_save_button_conditions)
        self.cancelar_button_conditions = QPushButton("Cancelar")
        self.cancelar_button_conditions.clicked.connect(self.cancelar)
        button_layout_conditions.addWidget(self.cancelar_button_conditions)
    
        # Agregar layout de botones al layout principal
        edit_layout_conditions.addLayout(button_layout_conditions)
    
        # Agregar el widget de condiciones al layout principal de la interfaz
        self.edit_layout_conditions.addWidget(self.conditions_area_widget)

        # Añadir una condición por defecto
        self.condicion_widget(deletable=False)

    def condicion_widget(self, deletable=True):
        # Línea 336 en structure_message_ui.py
        ConditionWidget(self.conditions_list, action_names=[], condition_names=[], deletable=False)

    def toggle_quick_response(self, state):
        if state == Qt.Checked:
            self.quick_response_name.setVisible(True)
            self.edit_message_w.setVisible(False)
            self.areas_edit_w.addStretch()
            self.desplegador_w.setVisible(False)
            self.desplegador_script_w.setVisible(False)
        else:
            self.quick_response_name.setVisible(False)
            self.edit_message_w.setVisible(True)
            self.areas_edit_w.takeAt(self.areas_edit_w.count() - 1)
            self.desplegador_w.setVisible(True)
            self.desplegador_script_w.setVisible(True)

    def setup_edit_area(self):
        self.edit_widget = QWidget()
        edit_layout = QVBoxLayout()
        self.edit_widget.setLayout(edit_layout)

        self.edit_id_label = QLabel()
        edit_layout.addWidget(self.edit_id_label)

        self.edit_message = QTextEdit()
        edit_layout.addWidget(self.edit_message)

        self.edit_file_button = QPushButton("Subir Archivo")
        edit_layout.addWidget(self.edit_file_button)

        self.edit_save_button = QPushButton("Guardar Cambios")
        edit_layout.addWidget(self.edit_save_button)

        self.cancelar_button = QPushButton("Cancelar")
        self.cancelar_button.clicked.connect(self.cancelar)
        edit_layout.addWidget(self.cancelar_button)

        self.edit_layout.addWidget(self.edit_widget)

    def cancelar(self):
        self.show_structure_area()

    def setup_structure_area(self):
        # Crear el widget principal y los layouts
        self.structure_widget = QWidget()
        self.button_layout = QHBoxLayout()
        self.zoomable_layout = QVBoxLayout()

        # Crear los botones y conectar señales
        self.add_button = QPushButton("Agregar Widget")
        self.add_button.clicked.connect(self.add_random_widget)
        self.button_layout.addWidget(self.add_button)

        self.delete_button = QPushButton("Eliminar Último")
        self.button_layout.addWidget(self.delete_button)

        self.save_button = QPushButton("Guardar")
        self.save_button.clicked.connect(self.guardar)
        self.button_layout.addWidget(self.save_button)

        self.ocultar_button = QPushButton("Ocultar")
        self.ocultar_button.clicked.connect(self.ocultar_areas)
        self.button_layout.addWidget(self.ocultar_button)

        # Crear y configurar la vista gráfica
        self.scene = QGraphicsScene(0, 0, 10000, 10000)
        self.view = ZoomableGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setScene(self.scene)
        self.zoomable_layout.addWidget(self.view)
        self.view.setMouseTracking(True)

        # Crear un layout principal que contenga el layout de botones y el layout de vista gráfica
        self.main_layout = QVBoxLayout()
        self.main_layout.addLayout(self.button_layout)
        self.main_layout.addLayout(self.zoomable_layout)

        self.main_layout_h = QHBoxLayout()
        #lista de botones de configuracion
        self.list_config = QVBoxLayout()
        self.list_config.addWidget(QLabel("Configuraciones"))

        # Crear botón para agregar un triángulo a la lista de configuraciones
        self.button_add_triangle = QPushButton("Condiciones 🔼")
        self.button_add_triangle.clicked.connect(lambda: self.add_widget_movable(color="yellow", tipo="triangle"))
        
        self.button_add_scuare = QPushButton("Menu 📜")
        self.button_add_scuare.clicked.connect(lambda: self.add_widget_movable(color="blue", tipo="square"))

        # Crear botón para agregar una acción a la lista de configuraciones
        self.button_add_action = QPushButton("Acciones ➡️")
        # Esto añadirá al área zoomeable un widget rectángulo
        self.button_add_action.clicked.connect(lambda: self.add_widget_movable(color="gray", tipo="rectangle"))

        #añadir botones a la lista de configuraciones
        self.list_config.addWidget(self.button_add_triangle)
        self.list_config.addWidget(self.button_add_scuare)
        self.list_config.addWidget(self.button_add_action)
        self.list_config.addStretch()
        
        # Crear un QWidget y establecer su layout
        self.areas_edit = QWidget()
        self.areas_edit.setLayout(self.list_config)

        self.main_layout_h.addLayout(self.main_layout)
        self.main_layout_h.addWidget(self.areas_edit)

        # Establecer el layout principal en el widget principal
        self.structure_widget.setLayout(self.main_layout_h)

        # Añadir el widget principal al layout general
        self.structure_layout.addWidget(self.structure_widget)

    def add_widget_movable(self, color, widget_id=0, tipo="rectangle"):
        can_delete = True  # o el valor que corresponda
        opciones = []  # o el valor que corresponda
        connections = []  # o el valor que corresponda

        if widget_id is None:
            widget = MovableWidget(self, color, None, can_delete, opciones, connections, tipo="pentagon")
        else:
            widget_id = self.next_widget_id
            self.next_widget_id += 1
            widget = MovableWidget(self, color, widget_id, can_delete, opciones, connections, tipo)
    

    def add_random_widget(self):
        color = self.generate_random_color()
        self.add_widget_movable(color)

    def generate_random_color(self):
        return f"#{random.randint(0, 0xFFFFFF):06x}"
    
    def connect_widgets(self, widget1, widget2):
        if widget2 not in widget1.connected_widgets:
            side1, side2 = self.determine_connection_sides(widget1, widget2)
            point1 = widget1.add_connection_point(side1)
            point2 = widget2.add_connection_point(side2)
            
            if point1 and point2:
                self.create_l_shaped_connection(point1, point2)
                widget1.connected_widgets.add(widget2)
                widget2.connected_widgets.add(widget1)
                # Actualizar conexiones
                widget1.connections.append(f'Connected to widget {widget2.widget_id}')
                widget2.connections.append(f'Connected to widget {widget1.widget_id}')
                print(f"Connected widget {widget1.widget_id} to widget {widget2.widget_id}")

    def determine_connection_sides(self, widget1, widget2):
        dx = widget2.scenePos().x() - widget1.scenePos().x()
        dy = widget2.scenePos().y() - widget1.scenePos().y()

        if abs(dx) > abs(dy):
            return ('right', 'left') if dx > 0 else ('left', 'right')
        else:
            return ('bottom', 'top') if dy > 0 else ('top', 'bottom')

    def create_l_shaped_connection(self, point1, point2):
        path = QPainterPath()
        start = point1.scenePos()
        end = point2.scenePos()
        path.moveTo(start)

        if point1.side in ['left', 'right']:
            mid_x = (start.x() + end.x()) / 2
            path.lineTo(mid_x, start.y())
            path.lineTo(mid_x, end.y())
        else:
            mid_y = (start.y() + end.y()) / 2
            path.lineTo(start.x(), mid_y)
            path.lineTo(end.x(), mid_y)

        path.lineTo(end)

        line = QGraphicsPathItem(path)
        line.setPen(QPen(Qt.black, 2))
        self.scene.addItem(line)
        self.connections.append((point1, point2, line))

    def update_connections(self):
        connections_to_remove = []
        for point1, point2, line in self.connections:
            widget1 = point1.parentItem()
            widget2 = point2.parentItem()
            
            # If either widget has been deleted, mark the connection for removal
            if widget1 is None or widget2 is None:
                connections_to_remove.append((point1, point2, line))
                continue
            
            # Determine the new sides for the connection
            new_side1, new_side2 = self.determine_connection_sides(widget1, widget2)
            
            # Change sides if necessary
            if point1.side != new_side1 or point2.side != new_side2:
                widget1.connection_points[point1.side].remove(point1)
                widget2.connection_points[point2.side].remove(point2)
                point1.side = new_side1
                point2.side = new_side2
                widget1.connection_points[new_side1].append(point1)
                widget2.connection_points[new_side2].append(point2)
            
            # Update the positions of the connection points
            widget1.update_connection_point_position(new_side1)
            widget2.update_connection_point_position(new_side2)
            
            # Update the L-shaped connection path
            path = QPainterPath()
            start = point1.scenePos()
            end = point2.scenePos()
            path.moveTo(start)

            if new_side1 in ['left', 'right']:
                mid_x = (start.x() + end.x()) / 2
                path.lineTo(mid_x, start.y())
                path.lineTo(mid_x, end.y())
            else:
                mid_y = (start.y() + end.y()) / 2
                path.lineTo(start.x(), mid_y)
                path.lineTo(end.x(), mid_y)

            path.lineTo(end)
            line.setPath(path)

        # Remove any connections where one of the widgets has been deleted
        for connection in connections_to_remove:
            self.connections.remove(connection)

    def add_widget_movable(self, color, widget_id=0, tipo="rectangle"):
        can_delete = True  # o el valor que corresponda
        opciones = []  # o el valor que corresponda
        connections = []  # o el valor que corresponda

        if widget_id is None:
            widget = MovableWidget(self, color, None, can_delete, opciones, connections, tipo="pentagon")
        else:
            widget_id = self.next_widget_id
            self.next_widget_id += 1
            widget = MovableWidget(self, color, widget_id, can_delete, opciones, connections, tipo)
    
        # Calculamos el tamaño real del widget
        widget.setPos(0, 0)  # Posición temporal para calcular el tamaño
        widget_rect = widget.boundingRect()
        widget_width = widget_rect.width()
        widget_height = widget_rect.height()
        spacing = 50
    
        # Obtenemos el tamaño visible de la escena
        scene_rect = self.scene.sceneRect()
    
        # Inicializamos la posición de inicio
        start_x = scene_rect.left() + spacing
        start_y = scene_rect.top() + spacing
    
        # Buscamos una posición libre
        position_found = False
        while not position_found:
            new_pos = QPointF(start_x, start_y)
            collision = False
    
            # Verificamos si hay colisión con algún widget existente
            for existing_widget in self.widgets:
                if existing_widget.sceneBoundingRect().intersects(QRectF(new_pos, QSizeF(widget_width, widget_height))):
                    collision = True
                    break
    
            if not collision:
                position_found = True
            else:
                # Movemos la posición a la derecha
                start_x += widget_width + spacing
                
                # Si llegamos al borde derecho, pasamos a la siguiente fila
                if start_x > scene_rect.right() - widget_width - spacing:
                    start_x = scene_rect.left() + spacing
                    start_y += widget_height + spacing
    
            # Si llegamos al borde inferior, reajustamos la escena
            if start_y > scene_rect.bottom() - widget_height - spacing:
                new_height = scene_rect.height() + widget_height + spacing
                self.scene.setSceneRect(self.scene.sceneRect().united(
                    QRectF(scene_rect.left(), scene_rect.top(), scene_rect.width(), new_height)
                ))
                scene_rect = self.scene.sceneRect()
    
        # Desplazar la posición un 20% más lejos
        new_pos.setX(new_pos.x() + widget_width * 0.2)
        new_pos.setY(new_pos.y() + widget_height * 0.2)
    
        # Ajustar la posición si se sale de los límites de la escena
        if new_pos.x() + widget_width > scene_rect.right():
            new_pos.setX(scene_rect.right() - widget_width)
        if new_pos.y() + widget_height > scene_rect.bottom():
            new_pos.setY(scene_rect.bottom() - widget_height)
    
        widget.setPos(new_pos)
        self.scene.addItem(widget)
        self.widgets.append(widget)
    
        # Aseguramos que el widget sea visible en la escena
        self.view.ensureVisible(widget.sceneBoundingRect(), 50, 50)
    
        return widget

    def start_connecting(self, widget):
        self.connecting_widget = widget
        self.view.setCursor(Qt.CrossCursor)
    
    # eliminará la conexión entre 2 widgets, es decir, el widget objetivo y el widget que dispara la desconexión
    def remove_connection(self, widget1, widget2):
        connections_to_remove = []
        for connection in self.connections:
            point1, point2, line = connection
            if (point1.parentItem() == widget1 and point2.parentItem() == widget2) or \
            (point1.parentItem() == widget2 and point2.parentItem() == widget1):
                self.scene.removeItem(line)
                connections_to_remove.append(connection)
                # Eliminar los puntos de conexión
                widget1.remove_connection_points(point1)
                widget2.remove_connection_points(point2)

        for connection in connections_to_remove:
            self.connections.remove(connection)

        # Actualizar las listas de widgets conectados
        widget1.connected_widgets.remove(widget2)
        widget2.connected_widgets.remove(widget1)

        # Actualizar las conexiones en los widgets
        widget1.connections = [conn for conn in widget1.connections if f"widget {widget2.widget_id}" not in conn]
        widget2.connections = [conn for conn in widget2.connections if f"widget {widget1.widget_id}" not in conn]

        print(f"Removed connection between widget {widget1.widget_id} and widget {widget2.widget_id}")

    def delete_widget(self, widget):
        if widget in self.widgets:
            self.widgets.remove(widget)
    
        connections_to_remove = []
        for connection in self.connections:
            point1, point2, line = connection
            if point1.parentItem() == widget or point2.parentItem() == widget:
                self.scene.removeItem(line)
                connections_to_remove.append(connection)
                # Eliminar el punto de conexión del otro widget
                if point1.parentItem() == widget:
                    other_widget = point2.parentItem()
                    other_widget.remove_connection_points(point2)
                else:
                    other_widget = point1.parentItem()
                    other_widget.remove_connection_points(point1)
    
        for connection in connections_to_remove:
            self.connections.remove(connection)
    
        widget.remove_connection_points()
    
        self.scene.removeItem(widget)

    def guardar(self):
        file_path = os.path.join('DATA', 'resource', 'xml', 'widgets_data.xml')
        file_path_p = os.path.join('DATA', 'resource', 'xml', 'widgets_pos.xml')
        guardar_pos_flujo(file_path_p, self.widgets, self.connections)
        guardar_datos_xml(file_path, self.widgets)

    def cargar_widgets(self):
        file_path = os.path.join('DATA', 'resource', 'xml', 'widgets_data.xml')
        file_path_p = os.path.join('DATA', 'resource', 'xml', 'widgets_pos.xml')
        self.widgets = cargar_datos_xml(file_path)
        self.connections = cargar_pos_flujo(file_path_p)
        self.next_widget_id = max([widget.widget_id for widget in self.widgets]) + 1

        for widget in self.widgets:
            self.scene.addItem(widget)
            for point in widget.connection_points:
                for connection in point.connections:
                    self.create_l_shaped_connection(point, connection)

def container_estructure(MainUI):
    return StructureUI(MainUI)