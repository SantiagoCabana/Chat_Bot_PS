from PyQt5.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QImage
from script_whatsApp import SeleniumWorker

class WorkerManager(QObject):
    frame_ready = pyqtSignal(int, QImage)  # Señal para enviar frames
    log_ready = pyqtSignal(int, str)       # Señal para enviar logs

    def __init__(self):
        super().__init__()
        self.thread_pool = QThreadPool()
        self.workers = {}

    def add_worker(self, script_id, script_name, use_gui):
        if script_id not in self.workers:
            worker = SeleniumWorker(script_name)
            worker.set_use_gui(use_gui)
            worker.signals.frame_ready.connect(lambda img: self.frame_ready.emit(script_id, img))
            worker.signals.result.connect(lambda msg: self.log_ready.emit(script_id, msg))
            worker.signals.error.connect(lambda err: self.log_ready.emit(script_id, f"ERROR: {err}"))
            worker.signals.finished.connect(lambda: self.remove_worker(script_id))
            self.workers[script_id] = worker
            self.thread_pool.start(worker)

    def remove_worker(self, script_id):
        if script_id in self.workers:
            self.workers[script_id].stop_running()
            del self.workers[script_id]

    def stop_all_workers(self):
        for worker in self.workers.values():
            worker.stop_running()
        self.workers.clear()