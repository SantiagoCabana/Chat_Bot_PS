import sys, random
from PyQt5.QtWidgets import QApplication, QMessageBox, QScrollArea, QMainWindow, QPushButton, QLineEdit, QHBoxLayout, QVBoxLayout, QWidget, QSpacerItem, QSizePolicy
from sql.database import insertar_script, consultar_scripts, eliminar_script, buscar_script

class GestionVentana(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestionar Script")
        self.initUI()
        self.cargar_scripts(consultar_scripts())

    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)
        self.setWindowTitle('Gestión de Scripts')
        self.nombre_input = QLineEdit(self)
        self.nombre_input.setPlaceholderText('Nombre del Script')
        self.crear_boton = QPushButton('Crear Script', self)
        self.crear_boton.clicked.connect(self.crear_script)
        self.inputS = QHBoxLayout()
        self.inputS.addWidget(self.nombre_input)
        self.inputS.addStretch()
        self.inputS.addWidget(self.crear_boton)
        self.layout.addLayout(self.inputS)

        # Define el contenedor para los scripts como un QScrollArea
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_content.setLayout(self.scroll_layout)
        self.scroll_area.setWidget(self.scroll_content)
        self.layout.addWidget(self.scroll_area)

        # Añadir un resorte al final del layout del scroll_area
        self.spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.scroll_layout.addItem(self.spacer)

    # Estructura de cada script que se cree en la interfaz
    def cube_script(self, id, nombre):
        cube = QWidget()
        # Nombre del contenedor (script) el cual se podrá editar
        name = QLineEdit(nombre)
        # Botones para editar y eliminar el script
        editar = QPushButton('Editar')
        eliminar = QPushButton('Eliminar')
        eliminar.clicked.connect(lambda: self.eliminar_widget_script(id, cube))

        # Layout para los botones
        layout = QHBoxLayout()
        layout.addWidget(name)
        layout.addStretch()
        layout.addWidget(editar)
        layout.addWidget(eliminar)
        cube.setLayout(layout)
        return cube

    def crear_script(self):
        nombre_script = self.nombre_input.text()
        if nombre_script:
            if buscar_script(nombre_script):
                QMessageBox.about(self, "ALERTA", "El script ya existe")
                return
            id = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=10))
            insertar_script(id, nombre_script)
            self.nombre_input.clear()
            # Añade el script a la interfaz el cual va a mostrar el nombre del script al scrollArea
            self.scroll_layout.insertWidget(0, self.cube_script(id, nombre_script))

    def cargar_scripts(self, scripts):
        for script in scripts:
            id = script['id']
            nombre = script['nombre']
            self.scroll_layout.insertWidget(0, self.cube_script(id, nombre))

    def eliminar_widget_script(self, id, cube):
        # Alerta de confirmación para confirmar si eliminar el script
        respuesta = QMessageBox.question(self, 'Eliminar script', '¿Estás seguro de eliminar el script?', QMessageBox.Yes | QMessageBox.No)
        if respuesta == QMessageBox.No:
            return
        eliminar_script(id)
        self.scroll_layout.removeWidget(cube)
        cube.deleteLater()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    gestion_ventana = GestionVentana()
    gestion_ventana.show()
    sys.exit(app.exec_())

