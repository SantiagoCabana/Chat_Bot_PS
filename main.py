#main.py
import os, sys, json, requests
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QMessageBox
)
from PyQt5.QtGui import QIcon, QPixmap, QImage
from PyQt5.QtCore import Qt, QSize
from functions.icon_button import IconButton
from google_authenticate import google_authenticate, get_user_info
from area_script_run import retornar_area_script_run
from area_historial_chat import retornar_area_historial_chat

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.crear_carpetas()
        self.descargar_xpath()
        self.init_ui()
        self.check_existing_credentials()

    def init_ui(self):
        self.main_layout = QVBoxLayout()

        self.create_content_areas()
        self.create_login_widget()
        self.create_menu_widget()

        self.main_layout.addWidget(self.login_widget)
        self.main_layout.addWidget(self.menu_widget)

        self.setLayout(self.main_layout)
        self.setWindowTitle("Inicio de Sesión")
        self.setMinimumHeight(500)
        self.setMinimumWidth(1100)

        self.menu_widget.hide()
        self.mostrar_home_area()

    def create_content_areas(self):
        self.home_area = QWidget()
        self.script_manager_area = retornar_area_script_run()
        self.structure_message_area = QWidget()
        self.historial_chat_area = retornar_area_historial_chat()

    def create_login_widget(self):
        self.login_widget = QWidget()
        login_layout = QHBoxLayout()

        self.frame = QFrame()
        self.frame.setFrameShape(QFrame.Box)
        self.frame.setFrameShadow(QFrame.Raised)
        self.frame.setLineWidth(2)
        self.frame_layout = QVBoxLayout(self.frame)

        background_url = "https://svgtrace-upload-results-bucket.s3.amazonaws.com/2024-08-19/windows_c988e48c-d50d-4716-97e6-c20130cc414b_1724057753252.svg"
        background_data = requests.get(background_url).content
        background_image = QPixmap()
        background_image.loadFromData(background_data)

        frame_size = self.frame.size()
        new_width = int(frame_size.width() * 1)
        new_height = int(frame_size.height() * 1)
        background_image = background_image.scaled(new_width, new_height, Qt.KeepAspectRatio)

        background_label = QLabel()
        background_label.setPixmap(background_image)

        hbox_layout = QHBoxLayout()
        hbox_layout.addStretch()
        hbox_layout.addWidget(background_label)
        hbox_layout.addStretch()

        self.frame_layout.addLayout(hbox_layout)

        vbox_layout = QVBoxLayout()

        title = QLabel("Inicio de Sesión de Google")
        title.setAlignment(Qt.AlignCenter)

        google_login_button = QPushButton("Iniciar Sesión con Google")
        google_icon_url = "https://upload.wikimedia.org/wikipedia/commons/c/c1/Google_%22G%22_logo.svg"
        google_icon_data = requests.get(google_icon_url).content
        google_icon = QIcon(QPixmap.fromImage(QImage.fromData(google_icon_data)))
        google_login_button.setIcon(google_icon)
        google_login_button.setIconSize(QSize(24, 24))
        google_login_button.clicked.connect(self.login_with_google)

        vbox_layout.addWidget(title)
        vbox_layout.addStretch()
        vbox_layout.addWidget(google_login_button)
        vbox_layout.addStretch()

        login_layout.addWidget(self.frame)
        login_layout.addLayout(vbox_layout)

        self.login_widget.setLayout(login_layout)

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

    def show_menu_window(self):
        self.login_widget.hide()
        self.menu_widget.show()

    def hide_menu_window(self):
        self.menu_widget.hide()
        self.login_widget.show()

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

    def login_with_google(self):
        credentials = google_authenticate()
        if credentials:
            user_info = get_user_info(credentials)
            token = credentials.token
            email = user_info.get('email')
            name = user_info.get('name')
            self.save_token(email, token, name)
            self.check_existing_credentials()

    def save_token(self, email, token, name):
        os.makedirs('DATA/tokens', exist_ok=True)
        token_filename = f'token_{email.split("@")[0]}.json'
        token_path = os.path.join('DATA', 'tokens', token_filename)
        with open(token_path, 'w') as token_file:
            json.dump({'token': token, 'name': name}, token_file)

    def check_existing_credentials(self):
        credentials = google_authenticate()
        if credentials and credentials.valid:
            user_info = get_user_info(credentials)
            email = user_info.get('email')
            token_filename = f'token_{email.split("@")[0]}.json'
            if os.path.exists(f'DATA/tokens/{token_filename}'):
                print("Hola Mundo")
                self.show_menu_window()

if __name__ == "__main__":
    app = QApplication([])
    window = LoginWindow()
    window.show()
    app.exec_()