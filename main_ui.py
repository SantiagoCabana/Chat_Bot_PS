#main_ui.py
import sys,asyncio,random
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QSizePolicy,QApplication, QMainWindow, QPushButton, QScrollArea, 
                            QVBoxLayout, QHBoxLayout, QWidget, QGridLayout, QStackedWidget,
                            QMessageBox, QFrame, QLabel)

from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QPixmap, QPainter

import os
from google_auth_oauthlib.flow import InstalledAppFlow

# Importar de otros archivos
from selenium_controller import SeleniumController
from historial_chat import historial_chat_area


from gestion_ui import gestionVentana, cube_script
#esto retorna lista de nombre e id de los scripts de la base de datos
from sql.database import consultar_scripts, Detener_script_bd, Iniciar_script_bd
from container_script import create_script_container
from sql.database import insertar_script, eliminar_script, buscar_script

from structure_message_ui import container_estructure


class IconButton(QPushButton):
    def __init__(self, text, svg_path, parent=None):
        super().__init__(parent)
        
        # Crear un widget contenedor para la imagen y el texto
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)  # Eliminar márgenes alrededor del contenedor
        layout.setSpacing(0)  # Eliminar espacio entre imagen y texto
        
        # Cargar la imagen SVG
        svg_renderer = QSvgRenderer(svg_path)
        pixmap = QPixmap(50, 50)  # Ajusta el tamaño según sea necesario
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        svg_renderer.render(painter)
        painter.end()

        # Crear un QLabel para la imagen
        image_label = QLabel(self)
        image_label.setPixmap(pixmap)
        image_label.setAlignment(Qt.AlignCenter)  # Alinear la imagen al centro
        layout.addWidget(image_label, alignment=Qt.AlignCenter)

        # Crear un QLabel para el texto
        text_label = QLabel(text, self)
        text_label.setAlignment(Qt.AlignCenter)  # Alinear el texto al centro
        layout.addWidget(text_label, alignment=Qt.AlignCenter)
        
        # Configurar el contenedor
        container.setLayout(layout)
        
        # Configurar el botón
        self.setFixedWidth(120)  # Ajusta el ancho fijo según sea necesario
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(container)
        self.layout().setContentsMargins(0, 0, 0, 0)  # Eliminar márgenes alrededor del botón

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Control de Selenium")
        self.setMinimumHeight(500)
        self.setMinimumWidth(1100)

        self.respuestas_window = None
        self.selenium_controller = None
        self.gestion_ventana = None
        self.selenium_controllers = {}
        self.botones_estado = {}
        self.script_widgets = []
        self.scroll_layout = QVBoxLayout()
        self.grid_layout = QGridLayout()

        self.widgets = []
        self.connections = []
        self.next_widget_id = 1

        self.cantidad = 0
        self.cube_script = cube_script
        self.structure_ui = container_estructure(self)
        self.historial_chat_area = historial_chat_area()

        self.initUI()
        self.crear_token_api_contacts()

    def initUI(self):
        anchofijo = 115
        altura = 80
        # Crear botones personalizados con imagen y texto
        self.home = IconButton("Inicio", "resource/svg/home.svg", self)
        #tamaño de los botones
        self.home.setFixedWidth(anchofijo)
        self.home.setFixedHeight(altura)
        self.home.clicked.connect(self.show_home_area)

        self.Gestionar = IconButton("Gestionar Script", "resource/svg/blocks.svg", self)
        self.Gestionar.setFixedWidth(anchofijo)
        self.Gestionar.setFixedHeight(altura)
        self.Gestionar.clicked.connect(self.show_script_manager_area)

        self.btn_estructure = IconButton('Estructurar Mensajes', "resource/svg/flujo.svg", self)
        self.btn_estructure.setFixedWidth(anchofijo)
        self.btn_estructure.setFixedHeight(altura)
        self.btn_estructure.clicked.connect(self.show_structure_message_area)

        self.btn_hisstorial_chat = IconButton('Historial Chat', "resource/svg/historial_chat.svg", self)
        self.btn_hisstorial_chat.setFixedWidth(anchofijo)
        self.btn_hisstorial_chat.setFixedHeight(altura)
        self.btn_hisstorial_chat.clicked.connect(self.show_historial_chat_area)

        self.boton4 = QPushButton("⚙️", self)
        self.boton4.setFixedWidth(50)

        # Configurar el layout
        self.layout = QHBoxLayout()
        button_top = QVBoxLayout()
        button_layout = QVBoxLayout()

        # Agregar botones al layout
        button_layout.addWidget(self.home)
        button_layout.addWidget(self.Gestionar)
        button_layout.addWidget(self.btn_estructure)
        button_layout.addWidget(self.btn_hisstorial_chat)
        button_layout.addWidget(self.boton4)

        self.layout.addLayout(button_layout)
        central_widget = QWidget()
        central_widget.setLayout(self.layout)
        self.setCentralWidget(central_widget)

        button_top.addWidget(self.home)
        button_top.addWidget(self.Gestionar)
        button_top.addWidget(self.btn_estructure)
        button_top.addWidget(self.btn_hisstorial_chat)

        button_layout.addLayout(button_top)
        button_layout.addStretch()
        button_layout.addWidget(self.boton4)

        # Crear el layout principal
        self.main_layout = QVBoxLayout(self)

        # Crear las áreas sin direccion
        self.home_area = self.create_home_area()
        self.script_manager_area = self.create_script_manager_area()
        self.structure_message_area = self.create_structure_message_area()
        self.historial_chat_area = self.create_historial_chat_area()

        # Añadir las áreas al layout principal
        self.main_layout.addWidget(self.home_area)
        self.main_layout.addWidget(self.script_manager_area)
        self.main_layout.addWidget(self.structure_message_area)
        self.main_layout.addWidget(self.historial_chat_area)


        self.layout.addLayout(button_layout)
        self.layout.addLayout(self.main_layout)

        central_widget = QWidget()
        central_widget.setLayout(self.layout)
        self.setCentralWidget(central_widget)

        self.cargar_scripts()
        self.show_home_area()

    def create_home_area(self):
        layout = QVBoxLayout()
        self.Running = QPushButton("Iniciar Todo", self)
        self.Running.setFixedWidth(120)
        self.Running.clicked.connect(lambda: self.asyncio_runner.run_task(self.alternar_estado_todos()))

        self.campo = QScrollArea()
        self.campo.setWidgetResizable(True)
        self.campo.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.campo.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.scroll_widget = QWidget()
        self.grid_layout = QGridLayout(self.scroll_widget)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)  # Alinear al top y a la izquierda
        self.grid_layout.setSpacing(10)  # Añadir un poco de espacio entre los widgets
        self.scroll_widget.setLayout(self.grid_layout)
        self.campo.setWidget(self.scroll_widget)

        # Añadir un widget expansible al final del grid para empujar todo hacia arriba
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.grid_layout.addWidget(spacer, 100, 0, 1, 3)  # Añadir en una fila alta para que esté al final

        layout.addWidget(self.Running)
        layout.addWidget(self.campo)
        widget = QFrame()
        widget.setLayout(layout)
        return widget

    def create_script_manager_area(self):
        scrollArea = gestionVentana(self)
        return scrollArea

    def create_structure_message_area(self):
        return self.structure_ui
    
    def create_historial_chat_area(self):
        return self.historial_chat_area

    #funcion para ocultar las areas de los botones
    def ocultar_areas(self):
        self.home_area.hide()
        self.script_manager_area.hide()
        self.structure_message_area.hide()
        self.historial_chat_area.hide()

    #funcion para mostrar el area de inicio
    def show_home_area(self):
        self.ocultar_areas()
        self.home_area.show()
    
    #funcion para mostrar el area de gestion de scripts
    def show_script_manager_area(self):
        self.ocultar_areas()
        self.script_manager_area.show()

    #funcion para mostrar el area de estructura de mensajes
    def show_structure_message_area(self):
        self.ocultar_areas()
        self.structure_message_area.show()

    def show_historial_chat_area(self):
        self.ocultar_areas()
        self.historial_chat_area.show()

    def reordenar_scripts(self):
        for i, widget in enumerate(self.script_widgets):
            row = i // 3
            col = i % 3
            self.grid_layout.addWidget(widget, row, col)

    def consultar_cantidad_scripts(self):
        scripts = consultar_scripts()
        self.cantidad = len(scripts)
        #limpiar la cantidad en el layout
        for i in reversed(range(self.cantidad_layout.count())):
            widget = self.cantidad_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        #colocar la cantidad en el layout
        self.cantidad_layout.addWidget(QLabel(f"Scripts: {self.cantidad}"))

    def cargar_scripts(self):
        scripts = consultar_scripts()
        self.consultar_cantidad_scripts()

        for script in scripts:
            id_script = script['id']
            nombre_script = script['nombre']
            self.agregar_contenedor_script(id_script, nombre_script)
            self.scroll_layout.insertWidget(0, self.cube_script(self,id_script, nombre_script))

    def agregar_contenedor_script(self, id_script, nombre_script):
        contenedor_new = create_script_container(id_script, nombre_script)
        contenedor_new.id_script = id_script  # Añade esta línea
        self.script_widgets.append(contenedor_new)
        self.reordenar_scripts()

        boton_estado = self.botones_estado.get(id_script)
        if boton_estado:
            boton_estado.clicked.connect(lambda checked, s=nombre_script, id=id_script: self.asyncio_runner.run_task(self.alternar_estado_individual(s, id)))
            
    def crear_script_cube(self):
        nombre_script = self.nombre_input.text()
        if nombre_script:
            if buscar_script(nombre_script):
                QMessageBox.about(self, "ALERTA", "El script ya existe")
                return
            id = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=10))
            insertar_script(id, nombre_script)
            self.consultar_cantidad_scripts()
            self.agregar_contenedor_script(id, nombre_script)
            self.nombre_input.clear()
            # Añade el script a la interfaz el cual va a mostrar el nombre del script al scrollArea
            self.scroll_layout.insertWidget(0, cube_script(self, id, nombre_script))

    def eliminar_script_cube(self, id, cube):
        # Alerta de confirmación para confirmar si eliminar el script
        respuesta = QMessageBox.question(self, 'Eliminar script', '¿Estás seguro de eliminar el script?', QMessageBox.Yes | QMessageBox.No)
        if respuesta == QMessageBox.No:
            return
        
        # Eliminar el script de la base de datos
        eliminar_script(id)
        
        # Remueve el cube de la sección de gestión de scripts
        self.scroll_layout.removeWidget(cube)
        cube.deleteLater()
        
        # Remueve el script de la sección de inicio
        for i in range(self.grid_layout.count()):
            widget = self.grid_layout.itemAt(i).widget()
            if widget and hasattr(widget, 'id_script') and widget.id_script == id:
                self.grid_layout.removeWidget(widget)
                widget.deleteLater()
                break
        #reordenar los scripts
        self.reordenar_scripts()
        
        # Actualiza la lista script_widgets
        self.script_widgets = [widget for widget in self.script_widgets if not (hasattr(widget, 'id_script') and widget.id_script == id)]
        
        # Eliminar el botón de estado si existe
        if id in self.botones_estado:
            del self.botones_estado[id]
        
        # Eliminar el controlador de Selenium si existe
        script_name = next((script['nombre'] for script in consultar_scripts() if script['id'] == id), None)
        if script_name and script_name in self.selenium_controllers:
            del self.selenium_controllers[script_name]
        
        print(f'Script eliminado: {id}')
        self.consultar_cantidad_scripts()
        # Reordenar los scripts en la sección de inicio
        self.reordenar_scripts()

    def crear_token_api_contacts(self):
        # Ruta al archivo de credenciales
        creds_file = 'Z_interface/credentials/credencial_api_contacts.json'
        contact_token = 'DATA/tokens/contacts_token.json'

        #verificar si el token ya existe
        if os.path.exists(contact_token):
            print(f"Token encontrado en {contact_token}")
            return

        # Ruta donde se guardará el token
        token_path = os.path.join(contact_token)
        
        # Asegúrate de que el directorio existe
        os.makedirs(os.path.dirname(token_path), exist_ok=True)
        
        # Configura el flujo de OAuth 2.0
        flow = InstalledAppFlow.from_client_secrets_file(
            creds_file,
            scopes=['https://www.googleapis.com/auth/contacts']
        )
        
        # Ejecuta el flujo de autorización
        creds = flow.run_local_server(port=0)
        
        # Guarda las credenciales para la próxima ejecución
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
        
        print(f"Token guardado exitosamente en {token_path}")

    async def alternar_estado_todos(self):
        if self.Running.text() == "Iniciar Todo":
            self.Running.setEnabled(False)
            self.Running.setText("Detener Todo")
            await self.iniciar_todos_los_scripts()
            self.Running.setEnabled(True)
        else:
            self.Running.setEnabled(False)
            self.Running.setText("Iniciar Todo")
            await self.detener_todos_los_scripts()
            self.Running.setEnabled(True)

    async def iniciar_todos_los_scripts(self):
        scripts = consultar_scripts()
        tasks = [self.iniciar_script(script['nombre'], script['id']) for script in scripts]
        await asyncio.gather(*tasks)
        for boton in self.botones_estado.values():
            boton.setText("Detener")
            boton.setChecked(True)

    async def detener_todos_los_scripts(self):
        tasks = [self.detener_script(nombre_script, id_script) for nombre_script, id_script in self.selenium_controllers.items()]
        await asyncio.gather(*tasks)
        for boton in self.botones_estado.values():
            boton.setText("Iniciar")
            boton.setChecked(False)

    async def alternar_estado_individual(self, nombre_script, id_script):
        if nombre_script not in self.selenium_controllers or not await self.selenium_controllers[nombre_script].is_running():
            await self.iniciar_script(nombre_script, id_script)
        else:
            await self.detener_script(nombre_script, id_script)

    async def iniciar_script(self, nombre_script, id_script):
        if nombre_script not in self.selenium_controllers:
            self.selenium_controllers[nombre_script] = SeleniumController(nombre_script)
        await self.selenium_controllers[nombre_script].iniciar()
        Iniciar_script_bd(id_script)
        boton = self.botones_estado.get(nombre_script)
        if boton:
            boton.setText("Detener")
            boton.setChecked(True)

    async def detener_script(self, nombre_script, id_script):
        if nombre_script in self.selenium_controllers:
            await self.selenium_controllers[nombre_script].detener()
            del self.selenium_controllers[nombre_script]
            Detener_script_bd(id_script)
            boton = self.botones_estado.get(nombre_script)
            if boton:
                boton.setText("Iniciar")
                boton.setChecked(False)

    #seccion de el navegador donde se mostrara lo q hace el script selenium pero dentro de la interfaz 

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())