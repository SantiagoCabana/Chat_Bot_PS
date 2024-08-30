from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, 
    QGraphicsScene, QGraphicsView, QFileDialog, QFrame, QScrollArea, QCheckBox
)
from PyQt5.QtCore import Qt
import xml.etree.ElementTree as ET
import os, sys

from functions.zoom_area import ZoomableGraphicsView
from functions.connection_point import MovableWidget, DesplegableArea
from functions.icon_button import IconButton

class FlowSheetManager(QWidget):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Gestor de Hojas de Flujo")
        self.flow_sheets = {}
        self.current_sheet = None
        self.next_sheet_id = 1

        self.delete_sheets = False
        
        self.svg_path = os.path.join(self.get_executable_dir(ruta='resource/svg'))
        print(self.svg_path)
        self.setup_ui()
        self.mostrar_area_A()
        
    def setup_ui(self):
        layout = QVBoxLayout()
    
        # Área A: Gestión de Hojas
        self.area_A = QWidget()
        self.area_A.setLayout(QVBoxLayout())
    
        add_sheet_layout = QVBoxLayout()
        label1 = QLabel("Nueva Hoja")
    
        Qframe_area = QFrame()
        Qframe_area.setFrameShape(QFrame.Panel)
    
        buttons_layout = QHBoxLayout()
        Qframe_area.setLayout(buttons_layout)
    
        new_sheet_button = IconButton("Nueva Hoja", self.svg_path + "/flow_sheet.svg")
        new_sheet_button.clicked.connect(self.new_sheet)
        new_sheet_button.setFixedSize(100, 100)
    
        copy_sheet_button = IconButton("Copiar Hoja", self.svg_path + "/flow_sheet.svg")
        copy_sheet_button.clicked.connect(self.new_sheet)
        copy_sheet_button.setFixedSize(100, 100)
    
        delete_sheet_button = IconButton("Eliminar Hojas", self.svg_path + "/flow_sheet.svg")
        delete_sheet_button.clicked.connect(self.show_checkboxes)
        delete_sheet_button.setFixedSize(100, 100)
    
        buttons_layout.addWidget(new_sheet_button)
        buttons_layout.addWidget(copy_sheet_button)
        buttons_layout.addWidget(delete_sheet_button)
        buttons_layout.addStretch()
    
        add_sheet_layout.addWidget(label1)
        add_sheet_layout.addWidget(Qframe_area)
    
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Buscar hojas...")
        self.search_bar.textChanged.connect(self.filter_sheets)
        add_sheet_layout.addWidget(self.search_bar)
    
        # Crear un QScrollArea
        self.scroll_list = QScrollArea()
        self.scroll_list.setWidgetResizable(True)
    
        # Crear un QWidget que contendrá los botones
        self.sheet_buttons_container = QWidget()
        self.sheet_buttons_layout = QVBoxLayout(self.sheet_buttons_container)
        self.sheet_buttons_layout.addStretch()
    
        self.scroll_list.setWidget(self.sheet_buttons_container)
        
        # Ajusta el estiramiento del diseño principal
        layout.addLayout(add_sheet_layout)
        layout.addWidget(self.scroll_list)  # Añade estiramiento vertical
    
        # Área B: Contenido de la Hoja Seleccionada
        self.area_B = QWidget()
        self.area_B.setLayout(QVBoxLayout())
        
        label1 = QLabel("Hoja de Flujo")
        label1.setAlignment(Qt.AlignCenter)
        self.area_B.layout().addWidget(label1)
    
        # Añadir ambas áreas al layout principal
        layout.addWidget(self.area_A)
        layout.addWidget(self.area_B)
        self.setLayout(layout)
    
    def new_sheet(self):
        # Crear un nuevo widget para la hoja
        widget = self.hoja_widget_item_list()
        
        # Insertar el widget en el layout de botones de hojas antes del resorte
        self.sheet_buttons_layout.insertWidget(self.sheet_buttons_layout.count() - 1, widget)
        
        # Si el modo de eliminación está activado, mostrar el checkbox de la nueva hoja
        if self.delete_sheets:
            checkbox = widget.findChild(QCheckBox)
            if checkbox:
                checkbox.setVisible(True)
    
    def hoja_widget_item_list(self):
        # Crear un nombre para la nueva hoja
        sheet_name = f"Hoja {self.next_sheet_id}"
        
        # Crear un widget contenedor
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # Crear un checkbox oculto
        checkbox = QCheckBox()
        checkbox.setVisible(False)
        layout.addWidget(checkbox)
        
        # Crear un botón contenedor
        button = QPushButton()
        button.setObjectName(f"button_{self.next_sheet_id}")
        button.setMinimumHeight(50)  # Establecer altura mínima
        
        # Crear un layout horizontal para el botón
        button_layout = QHBoxLayout(button)
        
        # Crear un QLabel para el nombre de la hoja
        label = QLabel(sheet_name)
        button_layout.addWidget(label)
        
        # Añadir un resorte para empujar los botones adicionales al final
        button_layout.addStretch()
        
        # Crear un botón de editar
        edit_button = QPushButton("Editar")
        button_layout.addWidget(edit_button)
        
        # Conectar el evento clicked del botón contenedor a la función principal_button_clicked
        button.clicked.connect(self.principal_button_clicked)
        
        # Conectar el evento clicked del botón de editar a la función edit_button_clicked
        edit_button.clicked.connect(self.edit_button_clicked)
        
        # Añadir el botón al layout principal
        layout.addWidget(button)
        
        # Incrementar el ID de la siguiente hoja
        self.next_sheet_id += 1
        
        # Actualizar la hoja actual
        self.current_sheet = sheet_name
        
        return widget
    
    def show_checkboxes(self):
        # Alternar el estado de delete_sheets
        self.delete_sheets = not self.delete_sheets
        
        # Mostrar u ocultar todos los checkboxes en los widgets de las hojas
        for i in range(self.sheet_buttons_layout.count() - 1):
            widget = self.sheet_buttons_layout.itemAt(i).widget()
            checkbox = widget.findChild(QCheckBox)
            if checkbox:
                checkbox.setVisible(self.delete_sheets)

    def principal_button_clicked(self):
        print("Hola Mundo")
    
    def edit_button_clicked(self):
        print("Mundo Hola")
    
    def select_sheet(self, sheet_name):
        self.current_sheet = sheet_name
        print(f"Hoja seleccionada: {sheet_name}")
    
    def select_sheet(self, sheet_name):
        self.current_sheet = sheet_name

    def filter_sheets(self):
        search_text = self.search_bar.text().lower()
        for i in range(self.sheet_buttons_layout.count()):
            button = self.sheet_buttons_layout.itemAt(i).widget()
            if isinstance(button, QPushButton):
                button.setVisible(search_text in button.text().lower())

    def mostrar_area_A(self):
        self.area_B.hide()
        self.area_A.show()

    def mostrar_area_B(self):
        self.area_A.hide()
        self.area_B.show()
    
    def ocultar_areas(self):
        self.area_A.hide()
        self.area_B.hide()

    def get_executable_dir(self, ruta):
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        
        base_dir = base_dir.replace('\\', '/')
        full_path = os.path.join(base_dir, ruta).replace('\\', '/')
        
        return full_path
    
    def lista_botones(self, ruta):
        # Crear un QScrollArea
        sscroll = QScrollArea()
        sscroll.setWidgetResizable(True)

        # Crear un QWidget que contendrá los botones
        container = QWidget()
        layout = QVBoxLayout(container)
        # agregar 20 botones a la lista
        for i in range(20):
            button = QPushButton(f"Botón {i}")
            sscroll.layout().addWidget(button)
        # prueba de la funcion de como se ve

def retornar_area_structure_message():
    return FlowSheetManager()
