from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from src.processing_utils import logger


class FlightPlotPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Flight plot panel"))
        self.setLayout(layout)
