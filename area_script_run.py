from PyQt5.QtWidgets import (QWidget, QPushButton, QVBoxLayout, QHBoxLayout, 
                             QTextEdit, QGroupBox, QScrollArea, QGridLayout, 
                             QSizePolicy, QLineEdit, QLabel, QCheckBox, QInputDialog, QMessageBox,
                             QComboBox)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QTimer
from worker import WorkerManager
import os
import json
import sys
import time
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

        # Botones superiores (siempre visibles)
        button_layout = QHBoxLayout()
        self.running_button = QPushButton("Iniciar Todo", self)
        self.manage_script_button = QPushButton("Gestionar Script", self)
        for button in (self.running_button, self.manage_script_button):
            button.setFixedWidth(120)
            button_layout.addWidget(button)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        # Área de contenido
        self.content_layout = QVBoxLayout()
        main_layout.addLayout(self.content_layout)

        # Área de scripts
        self.script_area = QWidget()
        self.script_area_layout = QVBoxLayout(self.script_area)
        self.script_widget = QWidget()
        self.script_widget_layout = QGridLayout(self.script_widget)
        self.script_scroll_area = QScrollArea()
        self.script_scroll_area.setWidgetResizable(True)
        self.script_scroll_area.setWidget(self.script_widget)
        self.script_area_layout.addWidget(self.script_scroll_area)
        self.content_layout.addWidget(self.script_area)

        # Área de gestión de scripts
        self.management_area = QWidget()
        self.management_layout = QVBoxLayout(self.management_area)
        
        # Barra de búsqueda
        self.search_bar = QLineEdit(placeholderText='Buscar scripts...')
        self.search_bar.textChanged.connect(self.filter_scripts)
        self.management_layout.addWidget(self.search_bar)
        
        # Añadir widgets para crear nuevo script
        create_script_layout = QHBoxLayout()
        self.script_name_input = QLineEdit(placeholderText='Nombre del Script')
        self.create_script_button = QPushButton('Crear Script')
        create_script_layout.addWidget(self.script_name_input)
        create_script_layout.addWidget(self.create_script_button)
        self.management_layout.addLayout(create_script_layout)
        
        # Área para mostrar scripts en modo gestión
        self.management_script_widget = QWidget()
        self.management_script_layout = QVBoxLayout(self.management_script_widget)
        self.management_scroll_area = QScrollArea()
        self.management_scroll_area.setWidgetResizable(True)
        self.management_scroll_area.setWidget(self.management_script_widget)
        self.management_layout.addWidget(self.management_scroll_area)
        
        # Añadir stretch al final del layout de gestión
        self.management_script_layout.addStretch()
        
        self.content_layout.addWidget(self.management_area)

        # Ocultar el área de gestión por defecto
        self.management_area.hide()

        # Conexiones
        self.running_button.clicked.connect(self.run_all_scripts)
        self.manage_script_button.clicked.connect(self.toggle_script_management)
        self.create_script_button.clicked.connect(self.create_script)

    def load_scripts_from_json(self):
        user_data_file = os.path.join(self.get_executable_dir(), 'DATA', 'resource', 'json', 'Z_USERS_DATA.json')
        if os.path.exists(user_data_file):
            with open(user_data_file, 'r') as f:
                user_data = json.load(f)
                for script_name, script_data in user_data.items():
                    self.add_script(script_name)
                    if script_data.get('running', False):
                        self.start_script(script_name)

    def add_script(self, script_name):
        # Añadir al área de scripts
        row = self.script_widget_layout.rowCount()
        col = self.script_widget_layout.columnCount()
        new_script = ScriptContainer(len(self.script_widget_layout.children()), script_name, self.worker_manager)
        self.script_widget_layout.addWidget(new_script, row, col)

        # Añadir al área de gestión al inicio
        management_script = ManagementScriptWidget(script_name, self)
        self.management_script_layout.insertWidget(0, management_script)
        
        self.update_run_all_button()

    def create_script(self):
        script_name = self.script_name_input.text()
        if script_name:
            self.add_script(script_name)
            self.script_name_input.clear()
            self.update_json_file()

    def update_json_file(self):
        user_data_file = os.path.join(self.get_executable_dir(), 'DATA', 'resource', 'json', 'Z_USERS_DATA.json')
        user_data = {}
        for i in range(self.script_widget_layout.count()):
            script_container = self.script_widget_layout.itemAt(i).widget()
            user_data[script_container.nombre_script] = {"running": script_container.running, "selected_message": ""}
        
        with open(user_data_file, 'w') as f:
            json.dump(user_data, f, indent=4)

    def remove_script(self, script_name):
        # Eliminar del área de scripts
        for i in range(self.script_widget_layout.count()):
            widget = self.script_widget_layout.itemAt(i).widget()
            if widget.nombre_script == script_name:
                self.script_widget_layout.removeWidget(widget)
                widget.deleteLater()
                break
        
        # Eliminar del área de gestión
        for i in range(self.management_script_layout.count()):
            widget = self.management_script_layout.itemAt(i).widget()
            if widget.script_name == script_name:
                self.management_script_layout.removeWidget(widget)
                widget.deleteLater()
                break
        
        self.update_json_file()
        self.update_run_all_button()

    def get_executable_dir(self):
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        else:
            return os.path.dirname(os.path.abspath(__file__))

    def run_all_scripts(self):
        start_time = time.time()
        if self.running_button.text() == "Iniciar Todo":
            self.worker_manager.stop_all_workers()
            for i in range(self.script_widget_layout.count()):
                script_container = self.script_widget_layout.itemAt(i).widget()
                script_container.iniciar_script()
            self.running_button.setText("Detener Todo")
        else:
            self.worker_manager.stop_all_workers()
            for i in range(self.script_widget_layout.count()):
                script_container = self.script_widget_layout.itemAt(i).widget()
                script_container.detener_script()
            self.running_button.setText("Iniciar Todo")
        end_time = time.time()

    def toggle_script_management(self):
        if self.script_area.isVisible():
            self.show_management_area()
        else:
            self.show_script_area()

    def show_script_area(self):
        self.script_area.show()
        self.management_area.hide()

    def show_management_area(self):
        self.script_area.hide()
        self.management_area.show()

    def update_preview(self, script_id, q_img):
        script_container = self.script_widget_layout.itemAt(script_id).widget()
        script_container.update_preview(q_img)

    def update_log(self, script_id, message):
        script_container = self.script_widget_layout.itemAt(script_id).widget()
        script_container.update_log(message)

    def rename_script(self, old_name, new_name):
        # Renombrar en el área de scripts
        for i in range(self.script_widget_layout.count()):
            widget = self.script_widget_layout.itemAt(i).widget()
            if widget.nombre_script == old_name:
                widget.nombre_script = new_name
                widget.setTitle(new_name)
                break
        
        self.update_json_file()

    def filter_scripts(self, text):
        for i in range(self.management_script_layout.count()):
            item = self.management_script_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget.setVisible(text.lower() in widget.script_name.lower())

    def start_script(self, script_name):
        for i in range(self.script_widget_layout.count()):
            widget = self.script_widget_layout.itemAt(i).widget()
            if widget.nombre_script == script_name:
                widget.iniciar_script()
                break

    def update_run_all_button(self):
        all_running = all(self.script_widget_layout.itemAt(i).widget().running 
                          for i in range(self.script_widget_layout.count()))
        self.running_button.setText("Detener Todo" if all_running else "Iniciar Todo")


class ManagementScriptWidget(QWidget):
    def __init__(self, script_name, parent):
        super().__init__()
        self.script_name = script_name
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.name_label = QLabel(self.script_name)
        self.rename_button = QPushButton("Renombrar")
        self.delete_button = QPushButton("Eliminar")
        
        layout.addWidget(self.name_label)
        layout.addWidget(self.rename_button)
        layout.addWidget(self.delete_button)
        
        self.setFixedHeight(120)
        
        self.rename_button.clicked.connect(self.rename_script)
        self.delete_button.clicked.connect(self.delete_script)

    def rename_script(self):
        new_name, ok = QInputDialog.getText(self, "Renombrar Script", "Nuevo nombre:", QLineEdit.Normal, self.script_name)
        if ok and new_name:
            old_name = self.script_name
            self.script_name = new_name
            self.name_label.setText(new_name)
            self.parent.rename_script(old_name, new_name)

    def delete_script(self):
        reply = QMessageBox.question(self, "Eliminar Script", 
                                     f"¿Estás seguro de que quieres eliminar el script '{self.script_name}'?", 
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.parent.remove_script(self.script_name)

class ScriptContainer(QGroupBox):
    def __init__(self, id_script, nombre_script, worker_manager):
        super().__init__(nombre_script)
        self.nombre_script = nombre_script
        self.id_script = id_script
        self.worker_manager = worker_manager
        self.ventana_script = None
        self.running = False
        self.last_frame_time = time.time()

        self.setFixedHeight(330)
        self.setFixedWidth(340)
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

        self.use_gui_checkbox = QCheckBox("Usar interfaz gráfica")
        
        self.preview_label = QLabel()
        self.preview_label.setFixedHeight(240)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("background-image: url(resource/gif/statica.gif);")

        layout.addLayout(button_layout)
        layout.addWidget(self.use_gui_checkbox)
        layout.addWidget(self.preview_label)
        layout.addStretch()

        # Crear y agregar la lista desplegable
        self.cuenta_combobox = QComboBox()
        self.cargar_cuentas()
        self.cuenta_combobox.currentIndexChanged.connect(self.actualizar_cuenta_seleccionada)
        layout.addWidget(self.cuenta_combobox)

        # Conexiones
        self.boton_estado.clicked.connect(self.toggle_estado)
        self.boton_pantalla.clicked.connect(self.mostrar_ventana_script)
        self.boton_configuracion.clicked.connect(self.abrir_configuracion)
        self.use_gui_checkbox.stateChanged.connect(self.actualizar_cuenta_seleccionada)

    def cargar_cuentas(self):
        ruta_cuentas = os.path.join(self.get_executable_dir(), 'DATA', 'resource', 'json', 'cuentas_google.json')
        try:
            with open(ruta_cuentas, 'r') as archivo:
                cuentas = json.load(archivo)
            for correo, datos in cuentas.items():
                if datos['estado']:
                    self.cuenta_combobox.addItem(datos['nombre'], correo)
        except Exception as e:
            print(f"Error al cargar las cuentas: {e}")

    def actualizar_cuenta_seleccionada(self):
        correo_seleccionado = self.cuenta_combobox.currentData()
        ruta_json = os.path.join(self.get_executable_dir(), 'DATA', 'resource', 'json', 'Z_USERS_DATA.json')
        try:
            with open(ruta_json, 'r') as archivo:
                datos = json.load(archivo)
            datos[self.nombre_script] = {
                'running': self.running,
                'selected_message': '',
                'cuenta_seleccionada': correo_seleccionado,
                'interface': self.use_gui_checkbox.isChecked()
            }
            with open(ruta_json, 'w') as archivo:
                json.dump(datos, archivo, indent=4)
        except Exception as e:
            print(f"Error al actualizar el archivo JSON: {e}")

    def toggle_estado(self):
        if self.boton_estado.isChecked():
            self.iniciar_script()
            self.boton_estado.setText("Detener")
            self.running = True
        else:
            self.detener_script()
            self.boton_estado.setText("Iniciar")
            self.running = False

    def iniciar_script(self):
        try:
            self.worker_manager.add_worker(self.id_script, self.nombre_script, self.use_gui_checkbox.isChecked())
            self.running = True
            self.actualizar_estado_json(True)
        except Exception as e:
            print(f"Error al iniciar el script: {e}")
            self.boton_estado.setChecked(False)
            self.boton_estado.setText("Iniciar")
            self.running = False
            self.show_error()

    def detener_script(self):
        try:
            self.worker_manager.remove_worker(self.id_script)
            self.running = False
            self.actualizar_estado_json(False)
        except Exception as e:
            print(f"Error al detener el script: {e}")
            self.show_error()

    def actualizar_estado_json(self, estado):
        ruta_json = os.path.join(self.get_executable_dir(), 'DATA', 'resource', 'json', 'Z_USERS_DATA.json')
        try:
            with open(ruta_json, 'r') as archivo:
                datos = json.load(archivo)
            if str(self.nombre_script) in datos:
                datos[str(self.nombre_script)]['running'] = estado
            else:
                datos[str(self.nombre_script)] = {
                    'running': estado,
                    'selected_message': '',
                    'cuenta_seleccionada': '',
                    'interface': False
                }
            with open(ruta_json, 'w') as archivo:
                json.dump(datos, archivo, indent=4)
        except Exception as e:
            print(f"Error al actualizar el archivo JSON: {e}")

    def update_preview(self, q_img):
        self.last_frame_time = time.time()
        pixmap = QPixmap.fromImage(q_img)
        self.preview_label.setPixmap(pixmap.scaled(320, 240, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.preview_label.setStyleSheet("")  # Eliminar el fondo cuando hay un frame

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

    def check_frame_timeout(self):
        if time.time() - self.last_frame_time > 2:
            self.preview_label.setPixmap(QPixmap())  # Limpiar la imagen
            self.preview_label.setStyleSheet("background-image: url(resource/gif/statica.gif);")

    def show_error(self):
        self.preview_label.setPixmap(QPixmap())  # Limpiar la imagen
        self.preview_label.setStyleSheet("background-image: url(resource/gif/error.gif);")

class VentanaPantallaYLog(QWidget):
    def __init__(self, id_script, nombre_script):
        super().__init__()
        self.setWindowTitle(f"Script: {nombre_script}")
        self.setMinimumSize(800, 600)
        
        layout = QHBoxLayout(self)
        self.pantalla = QLabel()
        self.pantalla.setAlignment(Qt.AlignCenter)
        self.pantalla.setStyleSheet("background-image: url(resource/gif/statica.gif);")
        self.campo_log = QTextEdit(readOnly=True, placeholderText="Registros de ejecución")
        
        layout.addWidget(self.pantalla, 2)
        layout.addWidget(self.campo_log, 1)

    def update_preview(self, q_img):
        pixmap = QPixmap.fromImage(q_img)
        self.pantalla.setPixmap(pixmap.scaled(self.pantalla.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.pantalla.setStyleSheet("")  # Eliminar el fondo cuando hay un frame

def retornar_area_script_run():
    return ScriptRunArea()