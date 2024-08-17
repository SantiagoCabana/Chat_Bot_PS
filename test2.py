#prototipo de interfaz gráfica para controlar instancias de selenium
import os
import asyncio
import sys
import hashlib
import socket
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout
from PyQt5.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot
from qasync import QEventLoop, QApplication

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

class SeleniumWorker(QRunnable):
    class Signals(QObject):
        finished = pyqtSignal()
        error = pyqtSignal(str)
        result = pyqtSignal(str)

    def __init__(self, nombre_script):
        super().__init__()
        self.nombre_script = nombre_script
        self.signals = self.Signals()
        self.driver = None
        self.running = False

    @pyqtSlot()
    def run(self):
        try:
            self.running = True
            options = Options()
            self.user_data_directory = os.path.join(self.get_executable_dir(), 'DATA', 'SCRIPTS', f'{self.nombre_script}')
            if not os.path.exists(self.user_data_directory):
                os.makedirs(self.user_data_directory)

            options = webdriver.ChromeOptions()
            options.add_argument(f"user-data-dir={self.user_data_directory}")
            
            # Generar un hash del data_folder y asignar un puerto
            if not isinstance(self.nombre_script, str):
                self.nombre_script = str(self.nombre_script)
            
            hash_object = hashlib.md5(self.nombre_script.encode())
            port = int(hash_object.hexdigest(), 16) % 1000 + 8000
            port = get_available_port(port)
            options.add_argument(f"--remote-debugging-port={port}")
            #ignorar el ssl
            options.add_argument('--ignore-certificate-errors')
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