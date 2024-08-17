from PyQt5.QtCore import QRunnable, pyqtSlot

class StopWorker(QRunnable):
    def __init__(self, worker):
        super().__init__()
        self.worker = worker

    @pyqtSlot()
    def run(self):
        self.worker.stop()