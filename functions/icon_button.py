from PyQt5.QtWidgets import QPushButton, QWidget, QVBoxLayout, QLabel
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtCore import Qt

class IconButton(QPushButton):
    def __init__(self, text, svg_path, parent=None):
        super().__init__(parent)
        
        # Crear un widget contenedor para la imagen y el texto
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(2, 2, 2, 2)  # Añadir márgenes de 2 px alrededor del contenedor
        layout.setSpacing(2)  # Añadir espacio de 2 px entre imagen y texto
        
        # Cargar la imagen SVG
        svg_renderer = QSvgRenderer(svg_path)
        
        # Calcular el tamaño adecuado del SVG
        svg_size = svg_renderer.defaultSize()
        button_width = 120  # Ancho fijo del botón
        button_height = 40  # Alto fijo del botón
        max_width = int(button_width * 1.5)  # 50% del ancho del botón
        max_height = int(button_height * 1.5)  # 50% del alto del botón
        aspect_ratio = svg_size.width() / svg_size.height()
        
        if aspect_ratio > 1:
            # SVG es más ancho que alto
            pixmap_width = min(max_width, button_width - 4)  # Restar márgenes y limitar al 50%
            pixmap_height = int(pixmap_width / aspect_ratio)
        else:
            # SVG es más alto que ancho
            pixmap_height = min(max_height, button_height - 4)  # Restar márgenes y limitar al 50%
            pixmap_width = int(pixmap_height * aspect_ratio)
        
        # Renderizar el SVG con el tamaño calculado
        pixmap = QPixmap(pixmap_width, pixmap_height)
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
        self.setFixedWidth(button_width)  # Ajusta el ancho fijo según sea necesario
        self.setFixedHeight(button_height)  # Ajusta el alto fijo según sea necesario
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(container)
        self.layout().setContentsMargins(0, 0, 0, 0)  # Eliminar márgenes alrededor del botón
        self.layout().setAlignment(Qt.AlignVCenter)  # Alinear el contenido verticalmente