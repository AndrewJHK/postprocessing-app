from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from src.logs import logger


class PlottingPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Plotting panel"))
        self.setLayout(layout)

