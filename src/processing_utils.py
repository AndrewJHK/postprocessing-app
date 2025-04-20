from PyQt6.QtCore import QRunnable, pyqtSignal, QObject
import logging

logger = logging.getLogger("postprocessing-app")
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler("app.log", mode='a', encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

if not logger.hasHandlers():
    logger.addHandler(file_handler)

logger.propagate = False


class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    file_ready = pyqtSignal(str)

    def __init__(self):
        super().__init__()


class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self):
        try:
            self.fn(*self.args, **self.kwargs)
        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            self.signals.finished.emit()
