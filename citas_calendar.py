from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QScrollArea

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Crear un QScrollArea
        sscroll = QScrollArea()
        sscroll.setWidgetResizable(True)

        # Crear un QWidget que contendrá los botones
        container = QWidget()
        layout = QVBoxLayout(container)

        # Agregar 20 botones al layout
        for i in range(20):
            button = QPushButton(f"Botón {i}")
            layout.addWidget(button)

        # Establecer el QWidget como el widget de la QScrollArea
        sscroll.setWidget(container)

        # Establecer el QScrollArea como el widget central de la ventana principal
        self.setCentralWidget(sscroll)

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()