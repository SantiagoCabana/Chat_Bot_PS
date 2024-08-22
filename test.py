#test.py
import sys
import os
import asyncio
import hashlib
import socket
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout, QMainWindow, QTextEdit
from PyQt5.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot, Qt, QTimer
from PyQt5.QtGui import QPixmap
from qasync import QEventLoop
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_available_port(start_port):
    port = start_port
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port
            port += 1

class LogWindow(QMainWindow):
    def __init__(self, worker, parent=None):
        super(LogWindow, self).__init__(parent)
        self.worker = worker
        self.initUI()

    def initUI(self):
        self.setWindowTitle(f"Log y Frame de Instancia {self.worker.nombre_script}")

        # Main layout
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.layout = QHBoxLayout(self.central_widget)

        # Frame display
        self.frame_label = QLabel(self)
        self.frame_label.setAlignment(Qt.AlignCenter)
        self.frame_label.setFixedSize(400, 300)
        self.layout.addWidget(self.frame_label)

        # Log display
        self.log_display = QTextEdit(self)
        self.log_display.setReadOnly(True)
        self.layout.addWidget(self.log_display)

        # Connect worker signals to update UI components
        self.worker.signals.frame_ready.connect(self.update_frame)
        self.worker.signals.result.connect(self.append_log)
        self.worker.signals.error.connect(self.append_log)

        # Timer to continuously update the frame display
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame_from_worker)
        self.timer.start(1000 // 30)  # 30 FPS

    def update_frame(self, screenshot):
        self.latest_screenshot = screenshot

    def update_frame_from_worker(self):
        if hasattr(self, 'latest_screenshot'):
            pixmap = QPixmap()
            pixmap.loadFromData(self.latest_screenshot)
            scaled_pixmap = pixmap.scaled(self.frame_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.frame_label.setPixmap(scaled_pixmap)

    def append_log(self, message):
        self.log_display.append(message)

class SeleniumWorker(QRunnable):
    class Signals(QObject):
        finished = pyqtSignal()
        error = pyqtSignal(str)
        result = pyqtSignal(str)
        frame_ready = pyqtSignal(bytes)

    def __init__(self, nombre_script):
        super().__init__()
        self.nombre_script = str(nombre_script)  # Ensure it is a string
        self.signals = self.Signals()
        self.driver = None
        self.running = False

    @pyqtSlot()
    def run(self):
        try:
            self.running = True
            options = Options()
            self.user_data_directory = os.path.join(self.get_executable_dir(), 'DATA', 'SCRIPTS', self.nombre_script)
            if not os.path.exists(self.user_data_directory):
                os.makedirs(self.user_data_directory)

            options.add_argument(f"user-data-dir={self.user_data_directory}")

            hash_object = hashlib.md5(self.nombre_script.encode())  # Ensure nombre_script is a string here
            port = int(hash_object.hexdigest(), 16) % 1000 + 8000
            port = get_available_port(port)
            options.add_argument(f"--remote-debugging-port={port}")
            options.add_argument('--ignore-certificate-errors')
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--window-size=1024,768")

            self.signals.result.emit(f"Puerto asignado: {port}")

            self.driver = webdriver.Chrome(options=options)
            self.signals.result.emit(f"Navegador iniciado con carpeta de datos: {self.nombre_script} y puerto: {port}")

            self.driver.get("https://www.google.com")

            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )

            search_box.send_keys("Hola Mundo")
            self.signals.result.emit(f"Palabra escrita en el buscador ({self.nombre_script})")

            search_box.send_keys(Keys.RETURN)
            self.signals.result.emit(f"Búsqueda realizada ({self.nombre_script})")

            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "search"))
            )

            while self.running:
                screenshot = self.driver.get_screenshot_as_png()
                self.signals.frame_ready.emit(screenshot)
                asyncio.run(asyncio.sleep(1 / 30))  # 30 FPS

        except Exception as e:
            self.signals.error.emit(str(e))

    def stop(self):
        if self.driver:
            print(f"Deteniendo instancia {self.nombre_script}")
            self.driver.quit()
        self.running = False
        self.signals.finished.emit()

    def get_executable_dir(self):
        return os.path.dirname(os.path.abspath(__file__))

class StopWorker(QRunnable):
    def __init__(self, worker):
        super().__init__()
        self.worker = worker

    @pyqtSlot()
    def run(self):
        self.worker.stop()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.selenium_workers = []
        self.thread_pool = QThreadPool()
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()

        self.add_button = QPushButton("Agregar Instancia de Selenium", self)
        self.add_button.clicked.connect(self.add_selenium_instance)
        self.layout.addWidget(self.add_button)

        self.global_buttons_layout = QHBoxLayout()

        self.start_all_button = QPushButton("Iniciar Todos", self)
        self.start_all_button.clicked.connect(self.start_all)
        self.global_buttons_layout.addWidget(self.start_all_button)

        self.stop_all_button = QPushButton("Detener Todos", self)
        self.stop_all_button.clicked.connect(self.stop_all)
        self.global_buttons_layout.addWidget(self.stop_all_button)

        self.layout.addLayout(self.global_buttons_layout)

        self.status_label = QLabel("Estado: Listo")
        self.layout.addWidget(self.status_label)

        self.setLayout(self.layout)
        self.setWindowTitle('Gestión de Instancias de Selenium')
        self.show()

        self.update_global_buttons_state()

    def add_selenium_instance(self):
        nombre_script = len(self.selenium_workers) + 1
        worker = SeleniumWorker(nombre_script=nombre_script)
        self.selenium_workers.append(worker)

        instance_layout = QHBoxLayout()

        instance_label = QLabel(f"Selenium Instance {len(self.selenium_workers)}")
        instance_layout.addWidget(instance_label)

        start_button = QPushButton("Iniciar", self)
        start_button.clicked.connect(lambda: self.start_task(worker, start_button, stop_button))
        instance_layout.addWidget(start_button)

        stop_button = QPushButton("Detener", self)
        stop_button.clicked.connect(lambda: self.stop_task(worker, start_button, stop_button))
        stop_button.setEnabled(False)
        instance_layout.addWidget(stop_button)

        delete_button = QPushButton("Eliminar", self)
        delete_button.clicked.connect(lambda: self.delete_selenium_instance(worker, instance_layout))
        instance_layout.addWidget(delete_button)

        view_button = QPushButton("Ver Log y Frame", self)
        view_button.clicked.connect(lambda: self.view_log_frame(worker))
        instance_layout.addWidget(view_button)

        self.layout.addLayout(instance_layout)
        self.update_global_buttons_state()
        self.update_instance_buttons_state()

    def start_task(self, worker, start_button, stop_button):
        if not worker.running:
            worker.signals.result.connect(self.print_output)
            worker.signals.finished.connect(self.task_complete)
            worker.signals.error.connect(self.print_error)
            self.thread_pool.start(worker)
            self.status_label.setText("Estado: Ejecutando")
            if start_button is not None:
                start_button.setEnabled(False)
            if stop_button is not None:
                stop_button.setEnabled(True)
            self.update_global_buttons_state()
            self.update_instance_buttons_state()

    def stop_task(self, worker, start_button, stop_button):
        if worker.running:
            stop_worker = StopWorker(worker)
            self.thread_pool.start(stop_worker)
            self.status_label.setText("Estado: Deteniendo")
            worker.signals.finished.connect(lambda: self.remove_worker(worker, start_button, stop_button))
            self.update_global_buttons_state()
            self.update_instance_buttons_state()

    def remove_worker(self, worker, start_button, stop_button):
        if worker in self.selenium_workers:
            self.selenium_workers.remove(worker)
            start_button.setEnabled(True)
            stop_button.setEnabled(False)
            self.update_global_buttons_state()
            self.update_instance_buttons_state()

    def delete_selenium_instance(self, worker, instance_layout):
        if worker in self.selenium_workers:
            self.stop_task(worker, None, None)
            self.selenium_workers.remove(worker)
            for i in reversed(range(instance_layout.count())): 
                widget = instance_layout.itemAt(i).widget()
                if widget is not None: 
                    widget.setParent(None)
            self.layout.removeItem(instance_layout)
            self.status_label.setText(f"Estado: Instancia {worker.nombre_script} eliminada")
            self.update_global_buttons_state()
            self.update_instance_buttons_state()

    def view_log_frame(self, worker):
        log_window = LogWindow(worker)
        log_window.show()

    def start_all(self):
        for i in range(len(self.selenium_workers)):
            worker = self.selenium_workers[i]
            if not worker.running:
                new_worker = SeleniumWorker(nombre_script=worker.nombre_script)
                self.selenium_workers[i] = new_worker
                self.start_task(new_worker, None, None)
        self.status_label.setText("Estado: Ejecutando todos los no iniciados")
        self.update_global_buttons_state()
        self.update_instance_buttons_state()

    def stop_all(self):
        for worker in self.selenium_workers:
            if worker.running:
                stop_worker = StopWorker(worker)
                self.thread_pool.start(stop_worker)

        self.status_label.setText("Estado: Deteniendo todos los ejecutando")
        self.update_global_buttons_state()
        self.update_instance_buttons_state()

    def update_global_buttons_state(self):
        any_running = any(worker.running for worker in self.selenium_workers)
        any_not_running = any(not worker.running for worker in self.selenium_workers)

        self.start_all_button.setEnabled(any_not_running)
        self.stop_all_button.setEnabled(any_running)

    def update_instance_buttons_state(self):
        for i in range(self.layout.count()):
            item = self.layout.itemAt(i)
            if isinstance(item, QHBoxLayout):
                instance_layout = item
                start_button = instance_layout.itemAt(1).widget() if instance_layout.itemAt(1) is not None else None
                stop_button = instance_layout.itemAt(2).widget() if instance_layout.itemAt(2) is not None else None
                if start_button is not None and stop_button is not None:
                    worker_index = i - 2  # Ajustar índice porque los primeros dos layouts son global_buttons_layout y add_button
                    if 0 <= worker_index < len(self.selenium_workers):
                        worker = self.selenium_workers[worker_index]
                        start_button.setEnabled(not worker.running)
                        stop_button.setEnabled(worker.running)

    @pyqtSlot(str)
    def print_output(self, s):
        print(s)
        self.status_label.setText(f"Estado: {s}")

    @pyqtSlot()
    def task_complete(self):
        print("Task completed")
        self.status_label.setText("Estado: Tarea completada")
        self.update_global_buttons_state()
        self.update_instance_buttons_state()

    @pyqtSlot(str)
    def print_error(self, s):
        print(f"Error: {s}")
        self.status_label.setText(f"Estado: Error - {s}")
        self.update_global_buttons_state()
        self.update_instance_buttons_state()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = MainWindow()

    with loop:
        loop.run_forever()
