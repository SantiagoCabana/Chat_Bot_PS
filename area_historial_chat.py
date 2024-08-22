from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QScrollArea, QWidget, QLabel, QListWidget, QPushButton, QListWidgetItem
from PyQt5.QtCore import Qt

# Clase de burbuja de chat que se mostrará en el historial de chat
class ChatBubble:
    def __init__(self, mensaje, emisor, orientacion):
        self.alto_maximo = 100
        self.alto_minimo = 50
        self.ancho_maximo = 300
        self.ancho_minimo = 100

        self.bubble_layout = QVBoxLayout()
        
        # Permitir HTML en el QLabel para soportar negrita, tachado e itálica
        mensaje_label = QLabel(mensaje)
        mensaje_label.setTextFormat(Qt.RichText)
        self.bubble_layout.addWidget(mensaje_label)
        
        emisor_label = QLabel(emisor)
        emisor_label.setTextFormat(Qt.RichText)
        self.bubble_layout.addWidget(emisor_label)
        
        self.bubble_layout.addStretch()

        self.bubble = QWidget()
        self.bubble.setLayout(self.bubble_layout)
        self.bubble.setStyleSheet(self.get_bubble_style(orientacion))

        # Tamaño máximo y mínimo de la burbuja
        self.bubble.setMaximumSize(self.ancho_maximo, self.alto_maximo)
        self.bubble.setMinimumSize(self.ancho_minimo, self.alto_minimo)

        self.main_layout = QHBoxLayout()
        if orientacion == "mio":
            self.main_layout.addStretch()
            self.main_layout.addWidget(self.bubble)
        else:
            self.main_layout.addWidget(self.bubble)
            self.main_layout.addStretch()

    def get_bubble(self):
        container = QWidget()
        container.setLayout(self.main_layout)
        return container

    def get_bubble_style(self, orientacion):
        if orientacion == "mio":
            return """
                QWidget {
                    background-color: #C8E6C9;
                    border-radius: 10px;
                    border-top-right-radius: 0px;
                    margin: 5px;
                    position: relative;
                }
                QWidget::after {
                    content: "";
                    position: absolute;
                    top: 10px;
                    right: -10px;
                    width: 0;
                    height: 0;
                    border: 10px solid transparent;
                    border-left-color: #C8E6C9;
                    border-right: 0;
                    border-bottom: 0;
                    margin-top: -5px;
                }
                """
        else:
            return """
                QWidget {
                    background-color: #E0E0E0;
                    border-radius: 10px;
                    border-top-left-radius: 0px;
                    margin: 5px;
                    position: relative;
                }
                QWidget::after {
                    content: "";
                    position: absolute;
                    top: 10px;
                    left: -10px;
                    width: 0;
                    height: 0;
                    border: 10px solid transparent;
                    border-right-color: #E0E0E0;
                    border-left: 0;
                    border-bottom: 0;
                    margin-top: -5px;
                }
                """

# Clase que retornará un widget al final de la función
class HistorialChat:
    def __init__(self):
        self.sin_imagen = self.generar_svg_no_image()
        self.historial_layout = QHBoxLayout()
        
        # Lista en la parte izquierda para los chats registrados
        self.list_contacts = QListWidget()
        self.historial_layout.addWidget(self.list_contacts)
        
        # Área de chat para mostrar los mensajes
        self.chat_area = QScrollArea()
        self.chat_area.setWidgetResizable(True)
        self.chat_area.setWidget(QWidget())
        self.chat_area.widget().setLayout(QVBoxLayout())
        self.historial_layout.addWidget(self.chat_area)
        
        # Ancho máximo y mínimo de la lista de contactos
        self.list_contacts.setMinimumWidth(100)

        self.container = QWidget()
        self.container.setLayout(self.historial_layout)

    def agregar_mensaje(self, mensaje, emisor, orientacion):
        bubble = ChatBubble(mensaje, emisor, orientacion)
        self.chat_area.widget().layout().addWidget(bubble.get_bubble())
    
    def contacto_chat(self, nombre, foto=None):
        # Widget de contacto que será un botón con la foto y nombre del contacto
        contacto = QWidget()
        contacto_layout = QHBoxLayout()
        contacto_nombre = QLabel(nombre)

        contacto_foto = QLabel()
        if foto:
            # Esta imagen se debe cambiar por la imagen del contacto
            contacto_foto.setStyleSheet(f"background-image: url({foto});")
        else:
            contacto_foto.setStyleSheet(f"background-image: url({self.sin_imagen});")
        
        contacto_foto.setMaximumSize(50, 50)
        # Bordes redondeados para que sea un círculo
        contacto_foto.setStyleSheet("border-radius: 25px; border: 1px solid black;")
        contacto_layout.addWidget(contacto_foto)
        contacto_layout.addWidget(contacto_nombre)
        contacto_layout.addStretch()
        contacto.setLayout(contacto_layout)

        # Colocarlo en botón
        contacto_button = QPushButton()
        contacto_button.setLayout(contacto_layout)

        # Añadir el botón a la lista de contactos
        item = QListWidgetItem()
        self.list_contacts.addItem(item)
        self.list_contacts.setItemWidget(item, contacto_button)

        # Conectar el botón para mostrar el chat correspondiente
        contacto_button.clicked.connect(lambda: self.mostrar_chat_contacto(nombre))

        return contacto_button

    def mostrar_chat_contacto(self, nombre):
        # Limpiar el área de chat actual
        for i in reversed(range(self.chat_area.widget().layout().count())):
            self.chat_area.widget().layout().itemAt(i).widget().setParent(None)
        
        # Aquí se puede cargar el historial de chat del contacto desde una base de datos o archivo
        # Por ahora, solo se muestra un mensaje de ejemplo
        self.agregar_mensaje(f"Chat con {nombre}", nombre, "el")

    def get_container(self):
        return self.container
    
    def generar_svg_no_image(self):
        svg_content = '''
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="black" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M5 21C5 17.134 8.13401 14 12 14C15.866 14 19 17.134 19 21M16 7C16 9.20914 14.2091 11 12 11C9.79086 11 8 9.20914 8 7C8 4.79086 9.79086 3 12 3C14.2091 3 16 4.79086 16 7Z"/>
        </svg>
        '''
        return svg_content

# Función que retorna el widget de la clase

""""cada chat sera un xml asi q crea chats el cual 
cada chat tendra el "nombre"_"ID".xml y dentro estara 
todos los mensajes"""
def retornar_area_historial_chat():
    return HistorialChat().get_container()

# Ejemplo de uso
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication, QVBoxLayout, QMainWindow

    app = QApplication([])

    window = QMainWindow()
    central_widget = QWidget()
    layout = QVBoxLayout(central_widget)

    historial = HistorialChat()
    layout.addWidget(historial.get_container())

    # Añadir un contacto y generar burbujas de chat
    contacto_button = historial.contacto_chat("Contacto 1")
    contacto_button.clicked.connect(lambda: historial.agregar_mensaje("<b>Hola</b>, <i>¿cómo estás?</i> <s>tachado</s>", "Contacto 1", "el"))
    contacto_button.clicked.connect(lambda: historial.agregar_mensaje("<b>Estoy bien</b>, <i>gracias</i>.", "Yo", "mio"))

    window.setCentralWidget(central_widget)
    window.show()

    app.exec_()