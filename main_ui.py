import sys
import asyncio
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QScrollArea, QVBoxLayout, QHBoxLayout, QWidget, QGridLayout, QFrame, QLabel, QStackedWidget
import xml.etree.ElementTree as ET  # Importar el módulo XML

# Importar de otros archivos
from selenium_controller import SeleniumController
from gestion_ui import GestionVentana
from sql.database import consultar_scripts, Detener_script_bd, Iniciar_script_bd
from container_script import container_script
from structure_message_ui import (container_estructure, add_widget, delete_last_widget, update_connections, generate_unique_color, create_connection_path)
from asyncio_runner import AsyncioRunner

class MainWindow(QMainWindow):
    def __init__(self, asyncio_runner):
        super().__init__()

        self.setWindowTitle("Control de Selenium")
        self.setMinimumHeight(600)
        self.setMinimumWidth(1200)

        self.respuestas_window = None
        self.asyncio_runner = asyncio_runner
        self.selenium_controller = None
        self.gestion_ventana = None
        self.selenium_controllers = {}
        self.botones_estado = {}
        self.script_widgets = []

        self.widgets = []
        self.connections = []
        self.next_widget_id = 1
        self.add_widget = add_widget
        self.delete_last_widget = delete_last_widget
        self.update_connections = update_connections
        self.generate_unique_color = generate_unique_color
        self.create_connection_path = create_connection_path

        self.initUI()

    def initUI(self):
        ancho_fijo = 120

        self.home = QPushButton("Inicio", self)
        self.home.setFixedWidth(ancho_fijo)
        self.home.clicked.connect(self.show_home_area)

        self.Gestionar = QPushButton("Gestionar Script", self)
        self.Gestionar.setFixedWidth(ancho_fijo)
        self.Gestionar.clicked.connect(self.show_script_manager_area)

        self.btn_estructure = QPushButton('Estructurar Mensajes', self)
        self.btn_estructure.setFixedWidth(ancho_fijo)
        self.btn_estructure.clicked.connect(self.show_structure_message_area)

        self.boton4 = QPushButton("⚙️", self)
        self.boton4.setFixedWidth(50)

        self.layout = QHBoxLayout()
        button_top = QVBoxLayout()
        button_layout = QVBoxLayout()

        button_top.addWidget(self.home)
        button_top.addWidget(self.Gestionar)
        button_top.addWidget(self.btn_estructure)

        button_layout.addLayout(button_top)
        button_layout.addStretch()
        button_layout.addWidget(self.boton4)

        self.stacked_widget = QStackedWidget()

        # Crear las áreas sin direccion
        self.home_area = self.create_home_area()
        self.script_manager_area = self.create_script_manager_area()
        self.structure_message_area = self.create_structure_message_area()

        # Añadir las áreas al QStackedWidget
        self.stacked_widget.addWidget(self.home_area)
        self.stacked_widget.addWidget(self.script_manager_area)
        self.stacked_widget.addWidget(self.structure_message_area)

        self.layout.addLayout(button_layout)
        self.layout.addWidget(self.stacked_widget)

        central_widget = QWidget()
        central_widget.setLayout(self.layout)
        self.setCentralWidget(central_widget)

        self.cargar_scripts()

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
        self.scroll_widget.setLayout(self.grid_layout)
        self.campo.setWidget(self.scroll_widget)

        layout.addWidget(self.Running)
        layout.addWidget(self.campo)
        widget = QWidget()
        widget.setLayout(layout)
        return widget

    def create_script_manager_area(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Gestión de Scripts"))
        widget = QWidget()
        widget.setLayout(layout)
        return widget

    def create_structure_message_area(self):

        widget = container_estructure(self)
        return widget

    #funcion para ocultar las areas de los botones
    def ocultar_areas(self):
        self.home_area.hide()
        self.script_manager_area.hide()
        self.structure_message_area.hide()

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

    def cargar_scripts(self):
        scripts = consultar_scripts()

        for script in scripts:
            id_script = script['id']
            nombre_script = script['nombre']
            self.agregar_contenedor_script(id_script, nombre_script)

    def agregar_contenedor_script(self, id_script, nombre_script):
        contenedor_new = container_script(self, id_script, nombre_script)
        self.script_widgets.append(contenedor_new)
        self.reordenar_scripts()

        boton_estado = self.botones_estado.get(id_script)
        if boton_estado:
            boton_estado.clicked.connect(lambda checked, s=nombre_script: self.asyncio_runner.run_task(self.alternar_estado_individual(s)))

    def reordenar_scripts(self):
        for i, widget in enumerate(self.script_widgets):
            row = i // 3
            col = i % 3
            self.grid_layout.addWidget(widget, row, col)

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
        tasks = [self.iniciar_script(script['nombre']) for script in scripts]
        await asyncio.gather(*tasks)
        for boton in self.botones_estado.values():
            boton.setText("Detener")
            boton.setChecked(True)

    async def detener_todos_los_scripts(self):
        tasks = [self.detener_script(nombre_script) for nombre_script in list(self.selenium_controllers.keys())]
        await asyncio.gather(*tasks)
        for boton in self.botones_estado.values():
            boton.setText("Iniciar")
            boton.setChecked(False)

    async def alternar_estado_individual(self, nombre_script):
        if nombre_script not in self.selenium_controllers or not await self.selenium_controllers[nombre_script].is_running():
            await self.iniciar_script(nombre_script)
        else:
            await self.detener_script(nombre_script)

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

    def abrir_gestion(self):
        if self.gestion_ventana is None:
            self.gestion_ventana = GestionVentana()
        self.gestion_ventana.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    asyncio_runner = AsyncioRunner()
    asyncio_runner.start()

    main_ui = MainWindow(asyncio_runner)
    main_ui.show()

    sys.exit(app.exec_())
    asyncio_runner.stop()