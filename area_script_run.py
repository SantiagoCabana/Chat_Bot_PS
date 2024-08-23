#area script run.py
from PyQt5.QtWidgets import (QWidget, QPushButton, QVBoxLayout, QHBoxLayout, 
                             QTextEdit, QGroupBox, QScrollArea, QGridLayout, 
                             QSizePolicy, QLineEdit, QLabel, QCheckBox)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from worker import WorkerManager
import os
import json
import sys

class ScriptRunArea(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker_manager = WorkerManager()
        self.worker_manager.frame_ready.connect(self.update_preview)
        self.worker_manager.log_ready.connect(self.update_log)
        self.init_ui()
        self.load_scripts_from_json()

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

    def load_scripts_from_json(self):
        user_data_file = os.path.join(self.get_executable_dir(), 'DATA', 'resource', 'json', 'Z_USERS_DATA.json')
        if os.path.exists(user_data_file):
            with open(user_data_file, 'r') as f:
                user_data = json.load(f)
                for script_name in user_data.keys():
                    new_script = ScriptContainer(len(self.script_layout.children()), script_name, self.worker_manager)
                    self.script_layout.addWidget(new_script, self.script_layout.rowCount(), 0)

    def get_executable_dir(self):
        return os.path.dirname(os.path.abspath(__file__))

    def run_all_scripts(self):
        self.worker_manager.stop_all_workers()
        for i in range(self.script_layout.rowCount()):
            script_container = self.script_layout.itemAt(i).widget()
            script_container.iniciar_script()

    def toggle_script_management(self):
        self.management_area.setVisible(not self.management_area.isVisible())
        self.script_area.setVisible(not self.management_area.isVisible())

    def create_script(self):
        script_name = self.script_name_input.text()
        if script_name:
            new_script = ScriptContainer(len(self.script_layout.children()), script_name, self.worker_manager)
            self.script_layout.addWidget(new_script, self.script_layout.rowCount(), 0)
            self.script_name_input.clear()

    def update_preview(self, script_id, q_img):
        script_container = self.script_layout.itemAt(script_id).widget()
        script_container.update_preview(q_img)

    def update_log(self, script_id, message):
        script_container = self.script_layout.itemAt(script_id).widget()
        script_container.update_log(message)

class ScriptContainer(QGroupBox):
    def __init__(self, id_script, nombre_script, worker_manager):
        super().__init__(nombre_script)
        self.nombre_script = nombre_script
        self.id_script = id_script
        self.worker_manager = worker_manager
        self.ventana_script = None
        self.init_ui()
        self.running = False  # Estado inicial

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

        self.use_gui_checkbox = QCheckBox("Usar interfaz gráfica")
        
        self.preview_label = QLabel()
        self.preview_label.setFixedSize(320, 240)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("background-color: black;")

        layout.addLayout(button_layout)
        layout.addWidget(self.use_gui_checkbox)
        layout.addWidget(self.preview_label)
        layout.addStretch()

        # Conexiones
        self.boton_estado.clicked.connect(self.toggle_estado)
        self.boton_pantalla.clicked.connect(self.mostrar_ventana_script)
        self.boton_configuracion.clicked.connect(self.abrir_configuracion)

    def toggle_estado(self):
        if self.boton_estado.isChecked():
            self.iniciar_script()
            self.boton_estado.setText("Detener")
            self.running = True  # Actualizar estado a True
        else:
            self.detener_script()
            self.boton_estado.setText("Iniciar")
            self.running = False  # Actualizar estado a False

    def iniciar_script(self):
        try:
            self.worker_manager.add_worker(self.id_script, self.nombre_script, self.use_gui_checkbox.isChecked())
            self.running = True  # Actualizar estado a True
            self.actualizar_estado_json(True)
        except Exception as e:
            print(f"Error al iniciar el script: {e}")
            self.boton_estado.setChecked(False)
            self.boton_estado.setText("Iniciar")
            self.running = False  # Asegurarse de que el estado se actualice correctamente

    def detener_script(self):
        try:
            self.worker_manager.remove_worker(self.id_script)
            self.running = False  # Actualizar estado a False
            self.actualizar_estado_json(False)
        except Exception as e:
            print(f"Error al detener el script: {e}")

    def actualizar_estado_json(self, estado):
        ruta_json = os.path.join(self.get_executable_dir(), 'DATA', 'resource', 'json', 'Z_USERS_DATA.json')
        print(ruta_json)
        try:
            with open(ruta_json, 'r') as archivo:
                datos = json.load(archivo)
            if str(self.nombre_script) in datos:
                datos[str(self.nombre_script)]['running'] = estado
            else:
                datos[str(self.nombre_script)] = {'running': estado, 'selected_message': ''}
            with open(ruta_json, 'w') as archivo:
                json.dump(datos, archivo, indent=4)
        except Exception as e:
            print(f"Error al actualizar el archivo JSON: {e}")

    def update_preview(self, q_img):
        pixmap = QPixmap.fromImage(q_img)
        self.preview_label.setPixmap(pixmap.scaled(320, 240, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def update_log(self, message):
        if self.ventana_script:
            self.ventana_script.campo_log.append(message)

    def mostrar_ventana_script(self):
        if not self.ventana_script:
            self.ventana_script = VentanaPantallaYLog(self.nombre_script, self.windowTitle())
        self.ventana_script.show()

    def abrir_configuracion(self):
        # Aquí puedes implementar la lógica para abrir la configuración del script
        pass

    def get_executable_dir(self):
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        else:
            return os.path.dirname(os.path.abspath(__file__))

class VentanaPantallaYLog(QWidget):
    def __init__(self, id_script, nombre_script):
        super().__init__()
        self.setWindowTitle(f"Script: {nombre_script}")
        self.setMinimumSize(800, 600)
        
        layout = QHBoxLayout(self)
        self.pantalla = QLabel()
        self.pantalla.setAlignment(Qt.AlignCenter)
        self.pantalla.setStyleSheet("background-color: black;")
        self.campo_log = QTextEdit(readOnly=True, placeholderText="Registros de ejecución")
        
        layout.addWidget(self.pantalla, 2)
        layout.addWidget(self.campo_log, 1)

    def update_preview(self, q_img):
        pixmap = QPixmap.fromImage(q_img)
        self.pantalla.setPixmap(pixmap.scaled(self.pantalla.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))


def retornar_area_script_run():
    return ScriptRunArea()