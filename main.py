#main.py
import os, sys, json, requests
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QMessageBox
)
from PyQt5.QtGui import QIcon, QPixmap, QImage
from PyQt5.QtCore import Qt, QSize
from functions.icon_button import IconButton
from google.auth.exceptions import RefreshError
from google_authenticate import google_authenticate, get_user_info
from area_script_run import retornar_area_script_run
from area_structure_message import retornar_area_structure_message
from area_historial_chat import retornar_area_historial_chat

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.crear_carpetas()
        self.descargar_xpath()
        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout()

        self.create_content_areas()
        self.create_menu_widget()

        self.main_layout.addWidget(self.menu_widget)

        self.setLayout(self.main_layout)
        self.setWindowTitle("Ventana Principal")
        self.setMinimumHeight(500)
        self.setMinimumWidth(1100)

        self.mostrar_home_area()

    def create_content_areas(self):
        self.home_area = QWidget()
        self.script_manager_area = retornar_area_script_run()
        self.structure_message_area = retornar_area_structure_message()
        self.historial_chat_area = retornar_area_historial_chat()

    def create_menu_widget(self):
        self.menu_widget = QWidget()
        menu_layout = QHBoxLayout()

        anchofijo = 120
        altura = 70

        self.home = IconButton("Inicio", "resource/svg/home.svg", self)
        self.home.clicked.connect(self.mostrar_home_area)
        self.home.setFixedSize(anchofijo, altura)

        self.Gestionar = IconButton("Gestionar Script", "resource/svg/blocks.svg", self)
        self.Gestionar.clicked.connect(self.mostrar_script_manager_area)
        self.Gestionar.setFixedSize(anchofijo, altura)

        self.btn_estructure = IconButton('Estructurar Mensajes', "resource/svg/flujo.svg", self)
        self.btn_estructure.clicked.connect(self.mostrar_structure_message_area)
        self.btn_estructure.setFixedSize(anchofijo, altura)

        self.btn_hisstorial_chat = IconButton('Historial Chat', "resource/svg/historial_chat.svg", self)
        self.btn_hisstorial_chat.clicked.connect(self.mostrar_historial_chat_area)
        self.btn_hisstorial_chat.setFixedSize(anchofijo, altura)

        self.btn_close_user = IconButton('Cerrar Sesión', "resource/svg/user.svg", self)
        self.btn_close_user.setFixedSize(anchofijo, altura)

        self.boton4 = QPushButton("⚙️", self)
        self.boton4.setFixedSize(120, 70)

        button_frame = QFrame(self)
        button_frame.setFrameShape(QFrame.Box)
        button_frame.setFrameShadow(QFrame.Raised)
        button_frame.setFixedWidth(141)

        button_layout = QVBoxLayout(button_frame)
        button_layout.addWidget(self.home)
        button_layout.addWidget(self.Gestionar)
        button_layout.addWidget(self.btn_estructure)
        button_layout.addWidget(self.btn_hisstorial_chat)
        button_layout.addStretch()
        button_layout.addWidget(self.btn_close_user)
        button_layout.addWidget(self.boton4)

        content_frame = QFrame()
        content_frame.setFrameShape(QFrame.Box)
        content_frame.setFrameShadow(QFrame.Raised)
        content_frame.setLineWidth(2)
        
        content_layout = QVBoxLayout(content_frame)
        content_layout.addWidget(self.home_area)
        content_layout.addWidget(self.script_manager_area)
        content_layout.addWidget(self.structure_message_area)
        content_layout.addWidget(self.historial_chat_area)
        
        menu_layout.addWidget(button_frame)
        menu_layout.addWidget(content_frame)
        
        self.menu_widget.setLayout(menu_layout)

    def ocultar_areas(self):
        self.home_area.hide()
        self.script_manager_area.hide()
        self.structure_message_area.hide()
        self.historial_chat_area.hide()
    
    def mostrar_home_area(self):
        self.ocultar_areas()
        self.home_area.show()
    
    def mostrar_script_manager_area(self):
        self.ocultar_areas()
        self.script_manager_area.show()
    
    def mostrar_structure_message_area(self):
        self.ocultar_areas()
        self.structure_message_area.show()
    
    def mostrar_historial_chat_area(self):
        self.ocultar_areas()
        self.historial_chat_area.show()

    def descargar_xpath(self):
        existing_path = 'DATA/xpath/xpath.json'
        file_id = '1L-lH-EIeU5xen8U0NUdYF2-0BKuuguDd'
        url = f"https://drive.google.com/uc?export=download&id={file_id}"
        
        if os.path.exists(existing_path):
            temp_path = 'DATA/xpath/temp_xpath.json'
            response = requests.get(url)
            with open(temp_path, 'wb') as temp_file:
                temp_file.write(response.content)
            
            with open(temp_path, 'r') as temp_file:
                temp_data = json.load(temp_file)
                temp_version = temp_data.get("version", [0, 0, 0, 0])
            
            with open(existing_path, 'r') as existing_file:
                existing_data = json.load(existing_file)
                existing_version = existing_data.get("version", [0, 0, 0, 0])
            
            if temp_version > existing_version:
                with open(existing_path, 'w') as existing_file:
                    json.dump(temp_data, existing_file, indent=4)
                QMessageBox.information(self, "Descarga de Xpath", f"Archivo Necesario actualizado con la versión {temp_version}")
            
            if os.path.exists(temp_path):
                os.remove(temp_path)
        else:
            temp_path = 'DATA/xpath/temp_xpath.json'
            response = requests.get(url)
            with open(temp_path, 'wb') as temp_file:
                temp_file.write(response.content)
            
            os.rename(temp_path, existing_path)
            QMessageBox.information(self, "Descarga de Xpath", "Archivo Necesario descargado con éxito")

    def crear_carpetas(self):
        lista_carpetas = ['DATA', 'DATA/tokens', 'DATA/xpath']
        base_path = self.get_executable_path()
        for carpeta in lista_carpetas:
            carpeta_path = os.path.join(base_path, carpeta)
            if not os.path.exists(carpeta_path):
                os.makedirs(carpeta_path)
                print(f"Se ha creado la carpeta {carpeta_path}")

    def get_executable_path(self):
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        else:
            return os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    app = QApplication([])
    window = LoginWindow()
    window.show()
    app.exec_()