from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import QThreadPool
from src.processing_utils import logger, Worker, show_processing_dialog

class FlightPlotPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Flight plot panel"))
        self.setLayout(layout)
