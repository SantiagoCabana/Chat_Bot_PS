import json
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, QFrame, QScrollArea, QGridLayout, 
                             QHBoxLayout, QSizePolicy, QSpacerItem)
from PyQt5.QtCore import Qt, QSize, QTimer, pyqtSignal, QEvent, QThread, QByteArray, QUrl, QIODevice
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen, QBrush, QPalette, QPaintEvent
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

import weakref, threading, concurrent.futures
import os, uuid
import requests,hashlib,socket
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

class AlertWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setFixedSize(300, 50)
        self.hide()
        
        # Set window flags to keep it on top

        #bordes redondeados y de color griss
        self.setStyleSheet("background-color: rgba(255, 255, 255, 0.8); border-radius: 5px; padding: 10px; border: 1px solid gray;")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(Qt.NoBrush)  # No brush to make the background transparent
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 5, 5)

    def show_alert(self, message, duration=5000):
        if self.layout.count() > 0:
            # If there's already an alert, remove it
            self.remove_alert(self.layout.itemAt(0).widget())
        
        label = QLabel(message)
        label.setStyleSheet("color: red;")
        label.setWordWrap(True)
        self.layout.addWidget(label)
        
        # Position the alert in the top-right corner of the parent widget
        if self.parent():
            parent_rect = self.parent().rect()
            self.move(parent_rect.right() - self.width() - 10, parent_rect.top() + 10)
        
        self.show()
        self.raise_()  # Bring the widget to the front
        
        # Use weakref to avoid premature deletion
        label_ref = weakref.ref(label)
        QTimer.singleShot(duration, lambda: self.remove_alert(label_ref()))

    def remove_alert(self, label):
        if label:
            self.layout.removeWidget(label)
            label.deleteLater()
        self.destroy()

class LoginThread(QThread):
    login_completed = pyqtSignal(str, str, str, str, str)
    login_failed = pyqtSignal(str)

    def __init__(self, id, credenciales, scopes, puerto):
        super().__init__()
        self.id = id
        self.credenciales = credenciales
        self.scopes = scopes
        self.puerto = puerto
        self.is_cancelled = False

    def run(self):
        try:
            flow = InstalledAppFlow.from_client_secrets_file(self.credenciales, self.scopes)
            creds = flow.run_local_server(port=self.puerto)

            if self.is_cancelled:
                return

            user_info_service = build('oauth2', 'v2', credentials=creds)
            user_info = user_info_service.userinfo().get().execute()

            nombre = user_info.get('name')
            correo = user_info.get('email')
            foto_perfil = user_info.get('picture')
            token_acceso = creds.token

            self.login_completed.emit(self.id, nombre, correo, foto_perfil, token_acceso)
        except Exception as e:
            self.login_failed.emit(str(e))

    def cancel(self):
        self.is_cancelled = True

class GoogleAccountsArea(QWidget):
    login_completed = pyqtSignal(str, str, str, str)

    def __init__(self):
        super().__init__()
        self.area = "Cuentas de Google"
        self.num_accounts = 0
        self.accounts_data = self.load_accounts_data()
        self.login_threads = {}
        self.login_timers = {}
        self.login_timer = None
        
        # Define the scopes
        self.SCOPES = [
            'https://www.googleapis.com/auth/userinfo.profile',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/contacts',
            'openid'
        ]

        self.init_ui()
        self.agregar_contacto_prueba("samitodevjs@gmail.com")

    def init_ui(self):
        main_layout = QVBoxLayout()
        label = QLabel("Área de Cuentas de Google")
        main_layout.addWidget(label)

        btn_agregar_cuenta = QPushButton("Agregar Cuenta de Google")
        btn_agregar_cuenta.clicked.connect(self.agregar_cuenta)
        main_layout.addWidget(btn_agregar_cuenta)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QGridLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area)

        self.alert_widget = AlertWidget(self)
        
        self.alert_widget.setGeometry(self.width() - 310, 10, 300, 50)  # Position in top-right corner

        self.setLayout(main_layout)
        self.initialize_columns()
        self.load_saved_accounts()
        self.login_completed.connect(self.update_account_info)

    def initialize_columns(self):
        widget_size = int(self.scroll_area.width() * 0.23)
        for col in range(4):
            placeholder = QLabel("")
            placeholder.setFixedSize(widget_size, widget_size)
            self.scroll_layout.addWidget(placeholder, 0, col)
            spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
            self.scroll_layout.addItem(spacer, 1, col)

    def add_empty_row(self):
        row = self.num_accounts // 4
        for col in range(4):
            placeholder = QLabel("")
            widget_size = int(self.scroll_area.width() * 0.23)
            placeholder.setFixedSize(widget_size, widget_size)
            self.scroll_layout.addWidget(placeholder, row, col)

    def load_saved_accounts(self):
        for email, account_data in self.accounts_data.items():
            self.agregar_cuenta(
                foto_perfil=account_data.get("foto_perfil"),
                nombre=account_data.get("nombre"),
                correo=email,
                id=account_data.get("ID"),
                estado=account_data.get("estado")
            )

    def agregar_cuenta(self, foto_perfil=None, nombre=None, correo=None, id=None, estado=None):
        if id is None:
            id = str(uuid.uuid4())  # Generar un nuevo UUID para cada cuenta

        cuenta_frame = QFrame()
        cuenta_frame.setFrameStyle(QFrame.Box | QFrame.Plain)
        cuenta_frame.setProperty("id", id)

        layout_vertical = QVBoxLayout(cuenta_frame)
        foto_perfil_label = QLabel()
        foto_perfil_label.setFixedSize(50, 50)
        self.actualizar_foto_perfil(foto_perfil_label, foto_perfil or "resource/svg/user.svg")

        nombre_area = QLabel(nombre if nombre else f"Cuenta {self.num_accounts + 1}")
        nombre_area.setAlignment(Qt.AlignCenter)
        correo_area = QLabel(correo if correo else "")
        correo_area.setAlignment(Qt.AlignCenter)
        estado_cuenta = QLabel("🟢Activa" if estado else "🟠Sin Cuenta")

        btn_iniciar_sesion = QPushButton("Iniciar Sesión")
        btn_iniciar_sesion.clicked.connect(lambda: self.iniciar_sesion(id))
        btn_cerrar_sesion = QPushButton("Cerrar Sesión")
        btn_cerrar_sesion.clicked.connect(lambda: self.cerrar_sesion(id))

        estado_area = QVBoxLayout()
        estado_area.addWidget(estado_cuenta)
        if estado == "🟢Activo":
            estado_area.addWidget(btn_cerrar_sesion)
        else:
            estado_area.addWidget(btn_iniciar_sesion)

        layout_vertical.addWidget(foto_perfil_label, alignment=Qt.AlignCenter)
        layout_vertical.addWidget(nombre_area)
        layout_vertical.addWidget(correo_area)
        layout_vertical.addLayout(estado_area)

        widget_size = int(self.scroll_area.width() * 0.23)
        cuenta_frame.setFixedSize(widget_size, widget_size)

        row, col = divmod(self.num_accounts, 4)
        item = self.scroll_layout.itemAtPosition(row, col)
        if item is not None:
            widget = item.widget()
            if widget is not None:
                self.scroll_layout.removeWidget(widget)
                widget.deleteLater()

        self.scroll_layout.addWidget(cuenta_frame, row, col)
        self.num_accounts += 1

        if correo and correo not in self.accounts_data:
            self.accounts_data[correo] = {
                "foto_perfil": foto_perfil,
                "nombre": nombre if nombre else f"Cuenta {self.num_accounts}",
                "correo_censurado": self.censor_email(correo),
                "estado": estado if estado else "🟠Sin Cuenta",
                "ID": id
            }
            self.save_accounts_data()

        if self.num_accounts % 4 == 0:
            self.add_empty_row()

    def censor_email(self, correo):
        return correo[:3] + "****" + correo[correo.index("@"):]
    
    def load_accounts_data(self):
        try:
            with open("DATA/resource/json/cuentas_google.json", "r") as file:
                content = file.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        except FileNotFoundError:
            return {}

    def save_accounts_data(self):
        with open("DATA/resource/json/cuentas_google.json", "w") as file:
            json.dump(self.accounts_data, file)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Update alert widget position when the window is resized
        self.alert_widget.setGeometry(self.width() - 310, 10, 300, 50)
        widget_size = int(self.scroll_area.width() * 0.23)
        for i in range(self.scroll_layout.count()):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget is not None:
                widget.setFixedSize(widget_size, widget_size)

    def get_area(self):
        return self.area

    def update_account_info(self, id, nombre, correo, foto_perfil):
        censored_email = self.censor_email(correo)
        self.accounts_data[correo] = {
            "nombre": nombre,
            "correo_censurado": censored_email,
            "foto_perfil": foto_perfil,
            "estado": True,
            "ID": id
        }
        self.save_accounts_data()
        self.refresh_account_widget(id)
    
    def refresh_account_widget(self, id):
        for row in range(self.scroll_layout.rowCount()):
            for col in range(self.scroll_layout.columnCount()):
                item = self.scroll_layout.itemAtPosition(row, col)
                if item and isinstance(item.widget(), QFrame) and item.widget().property("id") == id:
                    widget = item.widget()
                    layout = widget.layout()

                    account_data = next((data for data in self.accounts_data.values() if data['ID'] == id), None)
                    if account_data:
                        foto_label = layout.itemAt(0).widget()
                        self.actualizar_foto_perfil(foto_label, account_data.get("foto_perfil"))

                        layout.itemAt(1).widget().setText(account_data.get("nombre", ""))
                        layout.itemAt(2).widget().setText(account_data.get("correo_censurado", ""))

                        estado_text = "🟢Activo" if account_data.get("estado", False) else "🟠Reactivación Necesaria"
                        layout.itemAt(3).itemAt(0).widget().setText(estado_text)

                        while layout.itemAt(3).count() > 1:
                            item = layout.itemAt(3).takeAt(1)
                            if item.widget():
                                item.widget().deleteLater()

                        if account_data.get("estado", False):
                            btn_cerrar_sesion = QPushButton("Cerrar Sesión")
                            btn_cerrar_sesion.clicked.connect(lambda: self.cerrar_sesion(id))
                            layout.itemAt(3).addWidget(btn_cerrar_sesion)
                        else:
                            btn_iniciar_sesion = QPushButton("Iniciar/Reactivar Sesión")
                            btn_iniciar_sesion.clicked.connect(lambda: self.iniciar_sesion(id))
                            layout.itemAt(3).addWidget(btn_iniciar_sesion)
                    return

    def actualizar_foto_perfil(self, label, url_or_path):
        if url_or_path.startswith(('http://', 'https://')):
            # Es una URL, necesitamos descargar la imagen
            self.network_manager = QNetworkAccessManager()
            self.network_manager.finished.connect(lambda reply: self.handle_network_response(reply, label))
            self.network_manager.get(QNetworkRequest(QUrl(url_or_path)))
        elif url_or_path.endswith('.svg'):
            # Es un archivo SVG
            renderer = QSvgRenderer(url_or_path)
            if not renderer.isValid():
                print(f"Error: El archivo SVG {url_or_path} no es válido.")
                url_or_path = "resource/svg/user.svg"
                renderer = QSvgRenderer(url_or_path)
            pixmap = QPixmap(50, 50)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            label.setPixmap(pixmap)
        else:
            # Es un archivo local o una ruta por defecto
            pixmap = QPixmap(url_or_path)
            if pixmap.isNull():
                print(f"Error: No se pudo cargar la imagen desde {url_or_path}. Usando imagen por defecto.")
                pixmap = QPixmap("resource/svg/user.svg")
            label.setPixmap(pixmap.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def handle_network_response(self, reply, label):
        if reply.error() == QNetworkReply.NoError:
            data = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            label.setPixmap(pixmap.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            print(f"Error downloading image: {reply.errorString()}")
            # Use a default image in case of error
            pixmap = QPixmap("resource/svg/user.svg")
            label.setPixmap(pixmap.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation))

#---------------------------------Funciones de Inicio de Sesión y Cierre de Sesión---------------------------------#

    def hash_puerto(self, palabra):
        # Hashear la palabra utilizando SHA-256
        hash = hashlib.sha256(palabra.encode()).hexdigest()
        
        # Convertir el hash a un número entero
        puerto = int(hash, 16) % 65535  # Limitar el rango de puertos válidos (0-65535)
        
        # Verificar si el puerto está disponible
        while not self.puerto_disponible(puerto):
            puerto += 1
            if puerto > 65535:  # Reiniciar si se pasa del rango de puertos válidos
                puerto = 1024  # Evitar puertos reservados (0-1023)
        
        return puerto
    
    def puerto_disponible(self, puerto):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("", puerto))
            except OSError:
                return False
        return True
    
    def obtener_credenciales(self):
        credenciales_path = os.path.join("resource", "credentials.json")
        if not os.path.exists(credenciales_path):
            raise FileNotFoundError(f"No se encontró el archivo de credenciales en {credenciales_path}")
        
        with open(credenciales_path, 'r') as cred_file:
            credenciales = json.load(cred_file)
        
        return credenciales

    def iniciar_sesion(self, id):
        if id in self.login_threads and self.login_threads[id].isRunning():
            self.alert_widget.show_alert(f"Ya hay un proceso de inicio de sesión en curso para la cuenta {id}.")
            return

        credenciales_path = os.path.join("resource", "credentials.json")  # Usar la ruta correcta
        puerto = self.hash_puerto(id)

        self.login_threads[id] = LoginThread(id, credenciales_path, self.SCOPES, puerto)
        self.login_threads[id].login_completed.connect(self.on_login_completed)
        self.login_threads[id].login_failed.connect(lambda error_message: self.on_login_failed(id, error_message))
        
        self.login_threads[id].start()

        # Iniciar el temporizador
        self.login_timers[id] = threading.Timer(30.0, lambda: self.cancelar_sesion(id))
        self.login_timers[id].start()

    
    def save_token(self, correo, token_acceso):
        token_dir = os.path.join("DATA", "resource", "token", correo)
        os.makedirs(token_dir, exist_ok=True)
        token_path = os.path.join(token_dir, "token.json")
        
        with open(token_path, 'w') as token_file:
            json.dump({
                'token': token_acceso,
                'client_id': self.obtener_credenciales()['installed']['client_id'],
                'client_secret': self.obtener_credenciales()['installed']['client_secret'],
                'scopes': self.SCOPES
            }, token_file)
    
    def on_login_completed(self, id, nombre, correo, foto_perfil, token_acceso):
        if id in self.login_timers:
            self.login_timers[id].cancel()
            del self.login_timers[id]
    
        self.alert_widget.show_alert(f"Inicio de sesión exitoso para {correo}")
        self.update_account_info(id, nombre, correo, foto_perfil)
        
        # Guardar el token de acceso
        self.save_token(correo, token_acceso)
        
        # Agregar contacto de prueba automáticamente
        self.agregar_contacto_prueba(correo)
    
    def on_login_failed(self, id, error_message):
        if id in self.login_timers:
            self.login_timers[id].cancel()
            del self.login_timers[id]
    
        self.alert_widget.show_alert(f"Error en el inicio de sesión para la cuenta {id}: {error_message}")

    def cancelar_sesion(self, id):
        if id in self.login_threads and self.login_threads[id].isRunning():
            self.login_threads[id].cancel()
            self.login_threads[id].quit()
            self.login_threads[id].wait()
            self.alert_widget.show_alert(f"El inicio de sesión para la cuenta {id} ha sido cancelado por tiempo de espera.")

        if id in self.login_timers:
            del self.login_timers[id]

    def cerrar_sesion(self, id):
        account_data = next((data for data in self.accounts_data.values() if data['ID'] == id), None)
        if account_data:
            correo = next(key for key, value in self.accounts_data.items() if value['ID'] == id)
            account_data["estado"] = False
            
            if "token_acceso" in account_data:
                del account_data["token_acceso"]
            
            self.save_accounts_data()

            self.alert_widget.show_alert(f"Sesión cerrada correctamente para la cuenta {correo}.")
            self.refresh_account_widget(id)

    def agregar_contacto_prueba(self, correo):
        token_path = os.path.join("DATA", "resource", "token", correo, "token.json")
        if not os.path.exists(token_path):
            print(f"No se encontró un token de acceso válido para {correo}")
            return

        try:
            with open(token_path, 'r') as token_file:
                token_data = json.load(token_file)

            creds = Credentials(
                token=token_data['token'],
                refresh_token=token_data.get('refresh_token'),
                token_uri="https://oauth2.googleapis.com/token",
                client_id=token_data['client_id'],
                client_secret=token_data['client_secret'],
                scopes=token_data['scopes']
            )

            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                self.save_token(correo, creds.token)

            service = build('people', 'v1', credentials=creds)

            contact_body = {
                'names': [{'givenName': 'Contacto', 'familyName': 'Prueba'}],
                'phoneNumbers': [{'value': '1234567890'}],
                'emailAddresses': [{'value': 'prueba@example.com'}]
            }

            service.people().createContact(body=contact_body).execute()
            print(f"Contacto de prueba agregado exitosamente para {correo}")
        except Exception as e:
            print(f"Error al agregar contacto de prueba para {correo}: {str(e)}")

def retornar_area_google_accounts():
    return GoogleAccountsArea()