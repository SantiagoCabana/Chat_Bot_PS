#area script run.py
from PyQt5.QtWidgets import (QWidget, QPushButton, QVBoxLayout, QHBoxLayout, 
                             QTextEdit, QGroupBox, QScrollArea, QGridLayout, 
                             QSizePolicy, QLineEdit)
from PyQt5.QtCore import Qt

class ScriptRunArea(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.asyncio_runner = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Botones superiores
        button_layout = QHBoxLayout()
        self.running_button = QPushButton("Iniciar Todo", self)
        self.manage_script_button = QPushButton("Gestionar Script", self)
        for button in (self.running_button, self.manage_script_button):
            button.setFixedWidth(120)
            button_layout.addWidget(button)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        # Área de scripts
        self.script_area = QScrollArea()
        self.script_area.setWidgetResizable(True)
        self.script_widget = QWidget()
        self.script_layout = QGridLayout(self.script_widget)
        self.script_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.script_area.setWidget(self.script_widget)
        main_layout.addWidget(self.script_area)

        # Área de gestión de scripts
        self.management_area = QWidget()
        management_layout = QHBoxLayout(self.management_area)
        self.script_name_input = QLineEdit(placeholderText='Nombre del Script')
        self.create_script_button = QPushButton('Crear Script')
        management_layout.addWidget(self.script_name_input)
        management_layout.addWidget(self.create_script_button)
        self.management_area.hide()
        main_layout.addWidget(self.management_area)

        # Conexiones
        self.running_button.clicked.connect(self.run_all_scripts)
        self.manage_script_button.clicked.connect(self.toggle_script_management)
        self.create_script_button.clicked.connect(self.create_script)

    def run_all_scripts(self):
        if self.asyncio_runner:
            self.asyncio_runner.run_task(self.alternar_estado_todos())

    def toggle_script_management(self):
        self.management_area.setVisible(not self.management_area.isVisible())
        self.script_area.setVisible(not self.management_area.isVisible())

    def create_script(self):
        script_name = self.script_name_input.text()
        if script_name:
            new_script = ScriptContainer(len(self.script_layout.children()), script_name)
            self.script_layout.addWidget(new_script, self.script_layout.rowCount(), 0)
            self.script_name_input.clear()

class ScriptContainer(QGroupBox):
    def __init__(self, id_script, nombre_script):
        super().__init__(nombre_script)
        self.id_script = id_script
        self.ventana_script = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        button_layout = QHBoxLayout()

        self.boton_estado = QPushButton("Iniciar", checkable=True)
        self.boton_configuracion = QPushButton("⚙️")
        self.boton_pantalla = QPushButton("📺")

        for button in (self.boton_estado, self.boton_pantalla, self.boton_configuracion):
            button_layout.addWidget(button)
            if button != self.boton_estado:
                button.setFixedWidth(50)

        self.pantalla = QWidget()
        self.pantalla.setDisabled(True)

        layout.addLayout(button_layout)
        layout.addWidget(self.pantalla)
        layout.addStretch()

        # Conexiones
        self.boton_estado.clicked.connect(self.toggle_estado)
        self.boton_pantalla.clicked.connect(self.mostrar_ventana_script)

    def toggle_estado(self):
        self.boton_estado.setText("Detener" if self.boton_estado.isChecked() else "Iniciar")

    def mostrar_ventana_script(self):
        if not self.ventana_script:
            self.ventana_script = VentanaPantallaYLog(self.id_script, self.windowTitle())
        self.ventana_script.show()

class VentanaPantallaYLog(QWidget):
    def __init__(self, id_script, nombre_script):
        super().__init__()
        self.setWindowTitle(f"Script: {nombre_script}")
        self.setMinimumSize(800, 600)
        
        layout = QHBoxLayout(self)
        self.pantalla = QWidget()
        self.pantalla.setDisabled(True)
        self.campo_log = QTextEdit(readOnly=True, placeholderText="Registros de ejecución")
        
        layout.addWidget(self.pantalla)
        layout.addWidget(self.campo_log)

def retornar_area_script_run():
    return ScriptRunArea()