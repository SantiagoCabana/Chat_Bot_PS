import sys,asyncio,random
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QSizePolicy,QApplication, QMainWindow, QPushButton, QScrollArea, 
                            QVBoxLayout, QHBoxLayout, QWidget, QGridLayout, QStackedWidget,
                            QMessageBox, QFrame, QLabel)

# Importar de otros archivos
from selenium_controller import SeleniumController

from gestion_ui import gestionVentana, cube_script
#esto retorna lista de nombre e id de los scripts de la base de datos
from sql.database import consultar_scripts, Detener_script_bd, Iniciar_script_bd
from container_script import container_script
from sql.database import insertar_script, eliminar_script, buscar_script

from structure_message_ui import (container_estructure, add_widget, delete_last_widget, cargar_flujo,
                                update_connections, generate_unique_color, create_connection_path,
                                undo_changes)

from asyncio_runner import AsyncioRunner

class MainWindow(QMainWindow):
    def __init__(self, asyncio_runner):
        super().__init__()

        self.setWindowTitle("Control de Selenium")
        self.setMinimumHeight(500)
        self.setMinimumWidth(1100)

        self.respuestas_window = None
        self.asyncio_runner = asyncio_runner
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
        self.add_widget = add_widget
        self.delete_last_widget = delete_last_widget
        self.update_connections = update_connections
        self.generate_unique_color = generate_unique_color
        self.create_connection_path = create_connection_path

        self.cantidad = 0
        self.cube_script = cube_script
        self.cargar_flujo = cargar_flujo
        self.undo_changes = undo_changes

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
        scrollArea = container_estructure(self)
        return scrollArea

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
        contenedor_new = container_script(self, id_script, nombre_script)
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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    asyncio_runner = AsyncioRunner()
    asyncio_runner.start()

    main_ui = MainWindow(asyncio_runner)
    main_ui.show()

    sys.exit(app.exec_())
    asyncio_runner.stop()