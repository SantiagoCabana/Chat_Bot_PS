import os, sys
from PyQt5.QtWidgets import (QLabel, QMessageBox, QScrollArea, QPushButton, QVBoxLayout, QHBoxLayout,
                             QGraphicsView, QGraphicsScene, QGraphicsItem, QMenu, QAction, QGraphicsProxyWidget,
                             QApplication, QLineEdit, QTextEdit, QComboBox, QFileDialog, QLayout,
                             QListWidget, QWidget,QGraphicsLineItem,QGraphicsPathItem, QGraphicsRectItem
                             ,QGraphicsTextItem, QGraphicsEllipseItem, QGraphicsWidget, QGraphicsLayoutItem
                             ,QCheckBox,QFrame,QSizePolicy,QScrollArea,QListWidgetItem,QAbstractItemView
                             ,QSpacerItem,QGridLayout)


from PyQt5.QtCore import Qt, QPointF, QRectF, QLineF, QSizeF, QPropertyAnimation, QEasingCurve, QTimer
from PyQt5.QtGui import QPainter, QPen, QPainterPath, QBrush, QColor, QWheelEvent, QMouseEvent,QFont
import random
import time
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
        self.setup_ui()
        self.widget_count = 0  # Contador de widgets añadidos, empieza en 0
        self.nombre_flujo = 0

    def setup_ui(self):
        # Crear un layout vertical
        main_qframe = QVBoxLayout(self)
        
        # Activar bordes
        self.main_layout_h = QVBoxLayout()
        
        # Título
        layout_titulo = QHBoxLayout()
        titulo = QLabel("NUEVO FLUJO")
        font = QFont()
        # Tamaño de la fuente del título
        font.setPointSize(15)
        titulo.setFont(font)
        titulo.setAlignment(Qt.AlignCenter)
        layout_titulo.addWidget(titulo)
        layout_titulo.addStretch()
        self.main_layout_h.addLayout(layout_titulo)

        self.scroll_area = QScrollArea()
        scroll_area_widget = QWidget()
        self.scroll_area_layout = QGridLayout(scroll_area_widget)  # Cambiado a QGridLayout
        self.scroll_area_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        # Cuadro que será un botón con el símbolo de + en el centro del cuadro
        self.button_add = QPushButton()
        ruta_svg_plusa = os.path.join(self.get_executable_dir(), 'Z_interface', 'svg', 'add.svg')
        ruta_svg_plus = ruta_svg_plusa.replace("\\", "/")
        self.button_add.setStyleSheet(f"""
            QPushButton {{
                background-image: url({ruta_svg_plus});
                background-repeat: no-repeat;
                background-position: center;
                margin: 1px;
                border: 0.5px solid gray;
                border-radius: 5px;
                transition: background-color 0.3s ease;
            }}
            QPushButton:hover {{
                background-color: lightgray;
            }}
        """)
        self.button_add.setFixedSize(190, 140)
        self.button_add.clicked.connect(self.agregar_cuadro_flujo)
        
        # Añadir el botón directamente al layout del scroll area
        self.scroll_area_layout.addWidget(self.button_add, 0, 0)  # Añadir en la primera posición
        self.scroll_area.setWidget(scroll_area_widget)
        self.scroll_area.setWidgetResizable(True)
        
        # Añadir el scroll area al layout principal
        self.main_layout_h.addWidget(self.scroll_area)
        
        # Cuadro de flujo
        area2_widget = self.setup_area_flujo_widget()
        main_qframe.addWidget(area2_widget)
        main_qframe.addLayout(self.main_layout_h)
        
    def setup_area_flujo_widget(self):
        area_principal = QWidget()
        area = QVBoxLayout()
        h1_area = QHBoxLayout()
        label1 = QLabel("Nombre del flujo")
        name = QLineEdit()
        h1_area.addWidget(label1)
        h1_area.addWidget(name)
        h1_area.addStretch()
    
        h2_area = QHBoxLayout()
        # Crear y configurar la vista gráfica
        self.scene = QGraphicsScene(0, 0, 7000, 7000)
        self.view = ZoomableGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setScene(self.scene)
        self.view.setMouseTracking(True)

        h2_area.addWidget(self.view)

        area.addLayout(h1_area)
        area.addWidget(h2_area)
    
        area_principal.setLayout(area)
        return area_principal

    def agregar_cuadro_flujo(self):
        # Crear el nuevo cuadro de flujo
        numero = str(self.nombre_flujo)
        cuadro = self.cuadro_de_flujo(nombre="Nombre del Flujo: " + numero)
        self.nombre_flujo += 1
        self.widget_count += 1
    
        # Añadir el nuevo cuadro al layout
        self.scroll_area_layout.addWidget(cuadro)
    
        # Reorganizar los widgets
        self.reorganizar_widgets()

    def reorganizar_widgets(self):
        # Ancho de cada widget y margen
        ancho_widget = 190
        margen = 1
    
        # Obtener el ancho del área de desplazamiento
        ancho_scroll_area = self.scroll_area.width()
    
        # Calcular el número de columnas
        num_columnas = ancho_scroll_area // (ancho_widget + margen)
    
        # Reorganizar los widgets en el layout
        widgets = []
        for i in range(self.scroll_area_layout.count()):
            widget = self.scroll_area_layout.itemAt(i).widget()
            if widget != self.button_add:
                widgets.append(widget)
    
        # Limpiar el layout
        while self.scroll_area_layout.count():
            item = self.scroll_area_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
    
        # Añadir el botón de añadir en la primera posición
        self.scroll_area_layout.addWidget(self.button_add, 0, 0)
    
        # Añadir los widgets de nuevo en el layout reorganizados
        for i, widget in enumerate(widgets):
            row = (i + 1) // num_columnas
            col = (i + 1) % num_columnas
            self.scroll_area_layout.addWidget(widget, row, col)

    def cuadro_de_flujo(self, nombre="Nombre del Flujo", flujo=None):
        # Nombre
        nombre_label = QLabel(f"{nombre}")
        
        # Cuadro de flujo
        flujo_qframe = QFrame(self)
        flujo_qframe.setObjectName("customQFrame")
        flujo_qframe.setStyleSheet("""
            QFrame#customQFrame {
                border: 1px solid gray;
                border-radius: 5px;
                margin: 1px;
            }
        """)
        
        flujo_layout = QVBoxLayout()
        
        horizontal = QHBoxLayout()
        horizontal.addWidget(nombre_label)
        horizontal.addStretch()
        flujo_layout.addLayout(horizontal)

        #portada de el flujo
        label = QLabel()
        label.setMaximumSize(190, 170)
        label.setAlignment(Qt.AlignCenter)

        flujo_layout.addWidget(label)
        flujo_qframe.setLayout(flujo_layout)
        
        # Tamaño del cuadro de flujo
        flujo_qframe.setFixedSize(190, 140)
        
        return flujo_qframe
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        
        # Cancelar cualquier temporizador existente
        if hasattr(self, 'resize_timer'):
            self.resize_timer.stop()
        
        # Crear un nuevo temporizador
        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.reorganizar_widgets)
        
        # Iniciar el temporizador con un retraso de 200 ms
        self.resize_timer.start(100)

    def get_executable_dir(self):
        return os.path.dirname(os.path.abspath(__file__))


def container_estructure(MainUI):
    return StructureUI(MainUI)

import re

class ChatBot:
    def __init__(self):
        self.conditions_responses = []

    def format_condition(self, condition):
        # Reemplazar los formatos %palabra%, palabra%, %palabra
        condition = condition.replace('%', ' in mensaje.lower() ')
        condition = condition.replace(' ', '')
        # Convertir a evaluable en Python
        condition = condition.replace('or', ' or ')
        condition = condition.replace('and', ' and ')
        condition = condition.replace('not', ' not ')
        return condition

    def evaluate_condition(self, mensaje, condition, condition_type):
        try:
            result = eval(condition)
            if condition_type == 'obligatorio':
                return result
            elif condition_type == 'opcional':
                # Si la condición es opcional, no es necesario que sea verdadera, solo que no sea prohibida
                return result
            elif condition_type == 'prohibido':
                return not result
        except Exception as e:
            print(f"Error evaluando la condición: {e}")
            return False

    def responder(self, mensaje):
        for conditions, response, condition_type in self.conditions_responses:
            if all(self.evaluate_condition(mensaje, cond, cond_type) for cond, cond_type in conditions):
                return response
        return "No entiendo el mensaje."

    def add_conditions(self):
        while True:
            print("Introduce las condiciones para la nueva respuesta. Añade una condición por línea:")
            conditions = []
            while True:
                print("Introduce una condición (por ejemplo, '%hola%:obligatorio' o 'palabra%:opcional'), o escribe 'hecho' cuando termines:")
                input_condition = input()
                if input_condition.lower() == 'hecho':
                    break
                if ':' not in input_condition:
                    print("Formato inválido. Debes especificar el tipo de condición.")
                    continue
                
                condition, condition_type = input_condition.split(':', 1)
                formatted_condition = self.format_condition(condition.strip())
                conditions.append((formatted_condition, condition_type.strip()))

            print("Introduce la respuesta para estas condiciones:")
            response = input()
            self.conditions_responses.append((conditions, response.strip()))

            print("¿Quieres añadir más condiciones? (s/n): ")
            if input().lower() == 'n':
                break

# Menú principal
def main():
    chatbot = ChatBot()
    
    while True:
        print("¿Quieres añadir condiciones al chatbot? (s/n): ")
        if input().lower() == 's':
            chatbot.add_conditions()
        
        print("¿Quieres probar el chatbot? (s/n): ")
        if input().lower() == 's':
            while True:
                print("Introduce un mensaje para probar:")
                mensaje = input()
                print(chatbot.responder(mensaje))
                print("¿Quieres probar otro mensaje? (s/n): ")
                if input().lower() == 'n':
                    break
        
        print("¿Quieres continuar añadiendo más condiciones? (s/n): ")
        if input().lower() == 'n':
            print("Saliendo...")
            break

if __name__ == "__main__":
    main()
