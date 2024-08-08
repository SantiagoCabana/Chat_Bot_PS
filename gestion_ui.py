#gestion_ui.py
from PyQt5.QtWidgets import (QScrollArea, QPushButton, QLineEdit, QHBoxLayout, QVBoxLayout, 
                             QWidget, QSpacerItem, QSizePolicy,QLabel)


def gestionVentana(MainUI):
    MainUI.gest_layoud = QVBoxLayout()
    MainUI.nombre_input = QLineEdit(MainUI)
    MainUI.nombre_input.setPlaceholderText('Nombre del Script')
    MainUI.cantidad = QWidget()
    MainUI.cantidad_layout = QHBoxLayout(MainUI.cantidad)
    MainUI.crear_boton = QPushButton('Crear Script', MainUI)
    MainUI.crear_boton.clicked.connect(MainUI.crear_script_cube)
    # 
    MainUI.inputS = QHBoxLayout()
    MainUI.inputS.addWidget(MainUI.nombre_input)
    MainUI.inputS.addStretch()
    MainUI.inputS.addWidget(MainUI.cantidad)
    MainUI.inputS.addWidget(MainUI.crear_boton)
    MainUI.gest_layoud.addLayout(MainUI.inputS)

    # Define el contenedor para los scripts como un QScrollArea
    MainUI.scroll_area = QScrollArea()
    MainUI.scroll_area.setWidgetResizable(True)
    MainUI.scroll_content = QWidget()
    MainUI.scroll_layout = QVBoxLayout(MainUI.scroll_content)
    MainUI.scroll_content.setLayout(MainUI.scroll_layout)
    MainUI.scroll_area.setWidget(MainUI.scroll_content)
    MainUI.gest_layoud.addWidget(MainUI.scroll_area)

    # Añadir un resorte al final del layout del scroll_area
    MainUI.spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
    MainUI.scroll_layout.addItem(MainUI.spacer)

    MainUI.gest_layoud.addWidget(MainUI.scroll_area)

    #retorna el widget q tendra todos los elementos
    widget = QScrollArea()
    widget.setLayout(MainUI.gest_layoud)
    return widget

# Estructura de cada script que se cree en la interfaz
def cube_script(MainUI, id, nombre):
    cube = QWidget()
    # Nombre del contenedor (script) el cual se podrá editar
    name = QLineEdit(nombre)
    # Botones para editar y eliminar el script
    editar = QPushButton('Editar')
    eliminar = QPushButton('Eliminar')
    eliminar.clicked.connect(lambda: MainUI.eliminar_script_cube(id, cube))

    # Layout para los botones
    layout = QHBoxLayout()
    layout.addWidget(name)
    layout.addStretch()
    layout.addWidget(editar)
    layout.addWidget(eliminar)
    cube.setLayout(layout)
    return cube

