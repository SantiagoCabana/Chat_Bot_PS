from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout, QLabel, QHBoxLayout, QTextEdit, QGroupBox, QScrollArea, QApplication, QGridLayout, QSizePolicy, QFrame
from PyQt5.QtCore import Qt

class ScriptContainer(QWidget):
    def __init__(self, id_script, nombre_script):
        super().__init__()

        self.id_script = id_script
        self.nombre_script = nombre_script
        self.ventana_script = None  # Inicializar la ventana del script como None

        # Crear un QGroupBox con un título opcional
        self.group_box = QGroupBox(self.nombre_script)

        # Layout principal
        self.main_layout = QVBoxLayout(self.group_box)
        self.button_layout = QHBoxLayout()

        # Botón de estado
        self.boton_estado = QPushButton("Iniciar")
        self.boton_estado.setCheckable(True)
        self.boton_estado.clicked.connect(self.toggle_estado)

        # Botón de configuración
        self.boton_configuracion = QPushButton("⚙️")
        self.boton_configuracion.setFixedWidth(50)

        # Botón para ver la pantalla del script
        self.boton_pantalla = QPushButton("📺")
        self.boton_pantalla.setFixedWidth(50)
        self.boton_pantalla.clicked.connect(self.mostrar_ventana_script)

        self.button_layout.addWidget(self.boton_estado)
        self.button_layout.addWidget(self.boton_pantalla)
        self.button_layout.addWidget(self.boton_configuracion)

        # Mini Pantalla del script
        self.pantalla = QWidget()
        self.pantalla.setDisabled(True)  # Deshabilitar la interacción

        # Añadir widgets al layout
        self.main_layout.addLayout(self.button_layout)
        self.main_layout.addWidget(self.pantalla)
        self.main_layout.addStretch()

        # Establecer el layout en el contenedor
        layout = QVBoxLayout(self)
        layout.addWidget(self.group_box)
        layout.setContentsMargins(0, 0, 0, 0)  # Eliminar márgenes
        self.setLayout(layout)

    def toggle_estado(self):
        if self.boton_estado.isChecked():
            self.boton_estado.setText("Detener")
            self.boton_estado.setChecked(True)
        else:
            self.boton_estado.setText("Iniciar")
            self.boton_estado.setChecked(False)

    def mostrar_ventana_script(self):
        if self.ventana_script == None:
            self.ventana_script = venatana_pantalla_and_log(self.id_script, self.nombre_script)
        self.ventana_script.show()

class venatana_pantalla_and_log(QWidget):
    def __init__(self, id_script, nombre_script):
        super().__init__()
        # Atributos
        self.id_script = id_script
        self.nombre_script = nombre_script
        # Tamaño mínimo de la ventana
        self.setMinimumSize(800, 600)

        # Layout horizontal para la pantalla y el log
        self.layout_horizontal = QHBoxLayout()

        # Pantalla del script que cargará las capturas de pantalla del script
        self.pantalla = QWidget()
        self.pantalla.setDisabled(True)

        # Campo adicional para mostrar el log
        self.campo_adicional = QTextEdit()
        self.campo_adicional.setPlaceholderText("Registros de ejecución")
        self.campo_adicional.setReadOnly(True)

        self.layout_horizontal.addWidget(self.pantalla)
        self.layout_horizontal.addWidget(self.campo_adicional)

        self.setLayout(self.layout_horizontal)

# Función para crear y retornar una instancia de ScriptContainer
def create_script_container(id_script, nombre_script):
    return ScriptContainer(id_script, nombre_script)

