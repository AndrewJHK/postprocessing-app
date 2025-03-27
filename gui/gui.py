from PyQt6.QtWidgets import (
    QWidget, QPushButton, QLabel,
    QVBoxLayout, QFileDialog, QHBoxLayout,
    QScrollArea, QStackedWidget, QListWidget, QListWidgetItem, QSizePolicy
)
import os
from src.data_processing import DataProcessor, DataFrameWrapper
from src.json_parser import JSONParser


class FileWidget(QWidget):
    def __init__(self, file_path, delete_callback):
        super().__init__()
        self.file_path = file_path
        self.delete_callback = delete_callback

        layout = QHBoxLayout()
        self.label = QLabel(os.path.basename(file_path))
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.handle_delete)

        layout.addWidget(self.label)
        layout.addWidget(self.delete_button)
        self.setLayout(layout)

    def handle_delete(self):
        self.delete_callback(self)


# Placeholder panels to be extended later
class UploadPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Upload Files Panel"))
        self.setLayout(layout)


class JsonConverterPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("JSON to CSV Converter Panel"))
        self.setLayout(layout)


class DataProcessingPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Data Processing Panel"))
        self.setLayout(layout)


class PlottingPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Plotting Panel"))
        self.setLayout(layout)


class PostProcessingApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Postprocessing GUI")
        self.resize(1000, 700)

        self.file_widgets = []

        main_layout = QHBoxLayout()

        # Left Sidebar Layout
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setSpacing(10)

        self.load_button = QPushButton("1. Wczytaj dane")
        self.converter_button = QPushButton("2. Konwerter JSON/CSV")
        self.processing_button = QPushButton("3. Obróbka danych")
        self.plotter_button = QPushButton("4. Wykresy")

        sidebar_layout.addWidget(self.load_button)
        sidebar_layout.addWidget(self.converter_button)
        sidebar_layout.addWidget(self.processing_button)
        sidebar_layout.addWidget(self.plotter_button)

        # File list area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.file_list_widget = QWidget()
        self.file_list_layout = QVBoxLayout()
        self.file_list_widget.setLayout(self.file_list_layout)
        self.scroll_area.setWidget(self.file_list_widget)
        sidebar_layout.addWidget(self.scroll_area, stretch=1)

        # Main content area with stacked views
        self.stack = QStackedWidget()
        self.upload_panel = UploadPanel()
        self.converter_panel = JsonConverterPanel()
        self.processing_panel = DataProcessingPanel()
        self.plotting_panel = PlottingPanel()

        self.stack.addWidget(self.upload_panel)      # index 0
        self.stack.addWidget(self.converter_panel)   # index 1
        self.stack.addWidget(self.processing_panel)  # index 2
        self.stack.addWidget(self.plotting_panel)    # index 3

        # Connect sidebar buttons to stack view
        self.load_button.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.converter_button.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        self.processing_button.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        self.plotter_button.clicked.connect(lambda: self.stack.setCurrentIndex(3))

        main_layout.addLayout(sidebar_layout, stretch=1)
        main_layout.addWidget(self.stack, stretch=4)

        self.setLayout(main_layout)

    def load_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files")
        for file_path in files:
            if file_path and not self._is_duplicate(file_path):
                self.add_file(file_path)

    def _is_duplicate(self, file_path):
        return any(w.file_path == file_path for w in self.file_widgets)

    def add_file(self, file_path):
        file_widget = FileWidget(file_path, self.remove_file)
        self.file_widgets.append(file_widget)
        self.file_list_layout.addWidget(file_widget)

    def remove_file(self, widget):
        self.file_widgets.remove(widget)
        widget.setParent(None)
        widget.deleteLater()
