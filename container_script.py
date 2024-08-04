from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout, QLabel, QHBoxLayout, QTextEdit

# Función para la estructura de cada contenedor de script
def container_script(mainUI, id_script, nombre_script):

    # Crear el widget contenedor
    container = QWidget()
    
    # Crear el layout principal
    layout = QVBoxLayout()
    button_layout = QHBoxLayout()

    # Crear el botón que cambia de estado
    boton_estado = QPushButton("Iniciar")
    boton_estado.setCheckable(True)
    boton_estado.clicked.connect(lambda: estado_button(mainUI, id_script))

    boton_configuracion = QPushButton("⚙️")
    boton_configuracion.setFixedWidth(50)

    button_layout.addWidget(boton_estado)
    button_layout.addWidget(boton_configuracion)

    # Crear un campo adicional (QTextEdit) para mostrar el log
    campo_adicional = QTextEdit()
    campo_adicional.setPlaceholderText("Campo adicional")
    campo_adicional.setReadOnly(True)  # Hacer que el campo sea de solo lectura

    # Añadir widgets al layout
    layout.addWidget(QLabel(f"Script: {nombre_script}"))
    layout.addLayout(button_layout)
    layout.addWidget(campo_adicional)
    layout.addStretch()

    # Establecer el layout en el contenedor
    container.setLayout(layout)

    # Añadirle un tamaño mínimo
    container.setMinimumHeight(100)
    container.setMaximumHeight(300)
    container.setMinimumWidth(170)
    container.setMaximumWidth(300)

    # Almacenar los botones en un diccionario dentro de mainUI
    if not hasattr(mainUI, 'botones_estado'):
        mainUI.botones_estado = {}
    mainUI.botones_estado[id_script] = boton_estado

    return container

def estado_button(mainUI, id_script):
    boton_estado = mainUI.botones_estado[id_script]
    if boton_estado.isChecked():
        boton_estado.setText("Detener")
        boton_estado.setChecked(True)
    else:
        boton_estado.setText("Iniciar")
        boton_estado.setChecked(False)