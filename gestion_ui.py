#gestion_ui.py
from PyQt5.QtWidgets import (QPushButton, QLineEdit, QHBoxLayout, QVBoxLayout, 
                             QWidget, QSpacerItem, QSizePolicy, QLabel, QScrollArea, QGroupBox)

def gestionVentana(MainUI):
    MainUI.gest_layoud = QVBoxLayout()
    MainUI.nombre_input = QLineEdit(MainUI)
    MainUI.nombre_input.setPlaceholderText('Nombre del Script')
    MainUI.cantidad = QWidget()
    MainUI.cantidad_layout = QHBoxLayout(MainUI.cantidad)
    MainUI.crear_boton = QPushButton('Crear Script', MainUI)
    MainUI.crear_boton.clicked.connect(MainUI.crear_script_cube)
    
    MainUI.inputS = QHBoxLayout()
    MainUI.inputS.addWidget(MainUI.nombre_input)
    MainUI.inputS.addStretch()
    MainUI.inputS.addWidget(MainUI.cantidad)
    MainUI.inputS.addWidget(MainUI.crear_boton)
    MainUI.gest_layoud.addLayout(MainUI.inputS)

    MainUI.scroll_area = QScrollArea()
    MainUI.scroll_area.setWidgetResizable(True)
    MainUI.scroll_content = QWidget()
    MainUI.scroll_layout = QVBoxLayout(MainUI.scroll_content)
    MainUI.scroll_content.setLayout(MainUI.scroll_layout)
    MainUI.scroll_area.setWidget(MainUI.scroll_content)
    MainUI.gest_layoud.addWidget(MainUI.scroll_area)

    MainUI.spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
    MainUI.scroll_layout.addItem(MainUI.spacer)

    container = QWidget()
    container.setLayout(MainUI.gest_layoud)
    return container


def cube_script(MainUI, id, nombre):
    cube = QWidget()

    # Crear un QGroupBox con un título opcional
    group_box = QGroupBox()

    nombre_label = QLabel("Nombre asignado: ")
    # Nombre del contenedor (script) el cual se podrá editar
    name = QLineEdit(nombre)
    # Botones para editar y eliminar el script
    editar = QPushButton('Editar')
    eliminar = QPushButton('Eliminar')
    eliminar.clicked.connect(lambda: MainUI.eliminar_script_cube(id, cube))

    # Layout para los botones
    layout = QHBoxLayout()
    layout.addWidget(nombre_label)
    layout.addWidget(name)
    layout.addStretch()
    layout.addWidget(editar)
    layout.addWidget(eliminar)

    # Añadir el layout al QGroupBox
    group_box.setLayout(layout)

    # Layout principal para el QWidget
    main_layout = QVBoxLayout()
    main_layout.addWidget(group_box)
    cube.setLayout(main_layout)

    #añadir el scroll en el cube
    cube.setLayout(layout)
    return cube