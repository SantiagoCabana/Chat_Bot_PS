import asyncio
import threading
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QProgressBar, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer, pyqtSignal, QObject
import time
import random

class MainApplication(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Main Interface")
        self.setGeometry(100, 100, 300, 200)
        
        self.start_button = QPushButton("Start", self)
        self.start_button.clicked.connect(self.start_task)
        self.start_button.move(50, 50)

        self.stop_button = QPushButton("Stop", self)
        self.stop_button.clicked.connect(self.stop_task)
        self.stop_button.move(150, 50)
        self.stop_button.setEnabled(False)

        self.continue_button = QPushButton("Continue", self)
        self.continue_button.clicked.connect(self.continue_task)
        self.continue_button.move(50, 100)
        self.continue_button.setEnabled(False)

        self.reset_button = QPushButton("Reset", self)
        self.reset_button.clicked.connect(self.reset_task)
        self.reset_button.move(150, 100)
        self.reset_button.setEnabled(True)

        self.restart_all_button = QPushButton("Reiniciar Todo", self)
        self.restart_all_button.clicked.connect(self.restart_all)
        self.restart_all_button.move(100, 150)
        self.restart_all_button.setEnabled(True)

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.queue = asyncio.Queue()

        self.task = None
        self.secondary_window = None
        self.task_state = {'index': 0, 'start_time': None}
        self.is_running = False

        self.run_async_loop()

    def run_async_loop(self):
        self.loop_thread = threading.Thread(target=self.loop.run_forever)
        self.loop_thread.start()

    def start_task(self):
        if self.secondary_window is None:
            self.secondary_window = SecondaryWindow(self.queue)
            self.secondary_window.show()

        self.task = asyncio.run_coroutine_threadsafe(self.long_running_task(), self.loop)
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.continue_button.setEnabled(False)
        self.reset_button.setEnabled(True)
        self.is_running = True

    def stop_task(self):
        self.is_running = False
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.continue_button.setEnabled(True)
        self.reset_button.setEnabled(True)

    def continue_task(self):
        self.is_running = True
        self.task = asyncio.run_coroutine_threadsafe(self.long_running_task(), self.loop)
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.continue_button.setEnabled(False)
        self.reset_button.setEnabled(True)

    def reset_task(self):
        self.is_running = False
        if self.task:
            self.task.cancel()
        self.queue = asyncio.Queue()
        self.task_state = {'index': 0, 'start_time': None}
        self.secondary_window.reset_progress()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.continue_button.setEnabled(False)
        self.reset_button.setEnabled(True)

    def restart_all(self):
        self.reset_task()
        if self.secondary_window:
            self.secondary_window.close()
            self.secondary_window = None

    async def long_running_task(self):
        if self.task_state['start_time'] is None:
            self.task_state['start_time'] = time.time()

        while self.task_state['index'] < 100 and self.is_running:
            elapsed_time = time.time() - self.task_state['start_time']
            remaining_time = max(0, 100 - elapsed_time)
            operation_result = f"{self.task_state['index'] + 1} + {self.task_state['index'] + 1} = {2 * (self.task_state['index'] + 1)}"
            await self.queue.put((self.task_state['index'] + 1, elapsed_time, remaining_time, operation_result))
            await asyncio.sleep(0.1)  # Reduced sleep time for responsiveness
            
            # Simulate CPU intensive task
            for _ in range(1000000):
                _ = random.random() * random.random()
            
            if self.task_state['index'] % 4 == 0:
                await self.simulate_pdf_generation()
            
            self.task_state['index'] += 1

        if self.task_state['index'] >= 100:
            self.is_running = False
            self.reset_task()

    async def simulate_pdf_generation(self):
        # Simulate PDF generation
        print("Generating PDF...")
        time.sleep(1)  # Simulate some delay for PDF generation
        await asyncio.sleep(0.5)  # Simulate some delay for PDF generation

    def closeEvent(self, event):
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.loop_thread.join()
        event.accept()

class SecondaryWindow(QWidget):
    update_progress_signal = pyqtSignal(int, float, float, str)

    def __init__(self, queue):
        super().__init__()
        self.setWindowTitle("Secondary Interface")
        self.setGeometry(400, 100, 300, 300)

        layout = QVBoxLayout()

        self.progress = QProgressBar(self)
        layout.addWidget(self.progress)

        self.elapsed_label = QLabel("Elapsed Time: 0s", self)
        layout.addWidget(self.elapsed_label)

        self.remaining_label = QLabel("Remaining Time: 100s", self)
        layout.addWidget(self.remaining_label)

        self.operation_label = QLabel("", self)
        layout.addWidget(self.operation_label)

        self.queue = queue
        self.setLayout(layout)

        self.update_progress_signal.connect(self.update_progress)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_queue)
        self.timer.start(100)  # Check queue more frequently

    def check_queue(self):
        while not self.queue.empty():
            progress, elapsed_time, remaining_time, operation_result = self.queue.get_nowait()
            self.update_progress_signal.emit(progress, elapsed_time, remaining_time, operation_result)

    def update_progress(self, progress, elapsed_time, remaining_time, operation_result):
        self.progress.setValue(progress)
        self.elapsed_label.setText(f"Elapsed Time: {int(elapsed_time)}s")
        self.remaining_label.setText(f"Remaining Time: {int(remaining_time)}s")
        self.operation_label.setText(f"Last Operation: {operation_result}")

    def reset_progress(self):
        self.progress.setValue(0)
        self.elapsed_label.setText("Elapsed Time: 0s")
        self.remaining_label.setText("Remaining Time: 100s")
        self.operation_label.setText("")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_app = MainApplication()
    main_app.show()
    sys.exit(app.exec_())