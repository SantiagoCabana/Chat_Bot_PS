import sys
import time
import asyncio
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel,QPushButton
from PyQt5.QtGui import QPixmap, QMovie
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class SeleniumWorker(QThread):
    frame_ready = pyqtSignal(bytes)
    error_occurred = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.running = False
        self.driver = None

    async def selenium_actions(self):
        try:
            await asyncio.sleep(2)  # Esperar 2 segundos antes de iniciar
            self.driver.get("https://www.google.com")
            await asyncio.sleep(2)  # Esperar 2 segundos después de cargar la página

            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            await asyncio.sleep(1)  # Esperar 1 segundo antes de escribir

            search_box.send_keys("Hola Mundo")
            print("Palabra escrita en el buscador")
            await asyncio.sleep(1)  # Esperar 1 segundo antes de presionar Enter

            search_box.send_keys(Keys.RETURN)
            print("Búsqueda realizada")
            await asyncio.sleep(2)  # Esperar 2 segundos después de la búsqueda

            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "search"))
            )
        except Exception as e:
            print(f"Error en Selenium: {e}")
            self.error_occurred.emit()
    
    def stop(self):
        self.running = False
        self.quit()

    def run(self):
        self.running = True
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--window-size=1024,768")

        self.driver = webdriver.Chrome(options=chrome_options)

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.create_task(self.selenium_actions())

            while self.running:
                screenshot = self.driver.get_screenshot_as_png()
                self.frame_ready.emit(screenshot)
                time.sleep(1/25)  # 25 capturas por segundo
                loop.run_until_complete(asyncio.sleep(0.01))  # Dar tiempo para tareas asíncronas

        except Exception as e:
            print(f"Error general: {e}")
            self.error_occurred.emit()
        finally:
            self.driver.quit()
            loop.close()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visor de Selenium")
        self.setFixedSize(800, 600)  # Tamaño fijo de la ventana
        
        #botones de iniciar y detener
        self.iniciar_button = QPushButton()
        self.iniciar_button.setText("Iniciar")
        self.iniciar_button.clicked.connect(self.iniciar)

        #funcion para iniciar el script de selenium 
        def iniciar(self):
            inicado = True
            self.worker = SeleniumWorker()
            if inicado:
                self.worker.start()
            
            else:
                self.worker.running = False
                self.worker.wait()
                


        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)  # Eliminar márgenes

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFixedSize(800, 600)  # Tamaño fijo del label
        self.layout.addWidget(self.label)

        # Configurar el fondo de estática
        self.static_movie = QMovie("resource/gif/statica.gif")
        self.static_movie.setScaledSize(self.label.size())
        self.label.setMovie(self.static_movie)
        self.static_movie.start()

        # Preparar el fondo de error
        self.error_pixmap = QPixmap("resource/gif/error.gif")
        self.error_pixmap = self.error_pixmap.scaled(self.label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)

        self.worker = SeleniumWorker()
        self.worker.frame_ready.connect(self.update_frame)
        self.worker.error_occurred.connect(self.show_error)
        self.worker.start()

    def update_frame(self, screenshot):
        pixmap = QPixmap()
        pixmap.loadFromData(screenshot)
        scaled_pixmap = pixmap.scaled(self.label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.label.setPixmap(scaled_pixmap)

    def show_error(self):
        self.label.setPixmap(self.error_pixmap)

    def closeEvent(self, event):
        self.worker.running = False
        self.worker.wait()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())