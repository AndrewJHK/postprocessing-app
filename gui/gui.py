from PyQt6.QtWidgets import (
    QWidget, QPushButton, QLabel,
    QVBoxLayout, QFileDialog, QHBoxLayout,
    QScrollArea, QStackedWidget, QListWidget, QListWidgetItem, QSizePolicy, QTextEdit, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt
import os
import logging
from src.data_processing import DataProcessor, DataFrameWrapper
from src.json_parser import JSONParser

logger = logging.getLogger(__name__)
file_handler = logging.FileHandler("app.log", mode='a', encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)
logger.propagate = False


class FileWidget(QWidget):
    def __init__(self, file_path, delete_callback):
        super().__init__()
        self.file_path = file_path
        self.delete_callback = delete_callback

        layout = QHBoxLayout()
        self.label = QLabel(os.path.basename(file_path))
        self.delete_button = QPushButton("Delete")
        self.delete_button.setFixedWidth(70)  # Set fixed size
        self.delete_button.clicked.connect(self.handle_delete)

        layout.addWidget(self.label)
        layout.addWidget(self.delete_button)
        self.setLayout(layout)

    def handle_delete(self):
        self.delete_callback(self)


# Extended UploadPanel with CSV/JSON loader
class UploadPanel(QWidget):
    def __init__(self, add_callback=None, add_file_widget=None):
        super().__init__()
        self.add_callback = add_callback  # optional callback to send loaded data to main app
        self.add_file_widget = add_file_widget  # callback to add FileWidget to main app
        self.loaded_files = []
        self.interpolated = True  # Default setting

        layout = QVBoxLayout()

        self.csv_button = QPushButton("Load CSV")
        self.csv_button.clicked.connect(self.load_csv)

        self.json_button = QPushButton("Convert JSON")
        self.json_button.clicked.connect(self.load_json)

        self.radio_group = QButtonGroup(self)
        self.interpolated_radio = QRadioButton("Interpolated")
        self.none_filled_radio = QRadioButton("None filled")
        self.interpolated_radio.setChecked(True)
        self.radio_group.addButton(self.interpolated_radio)
        self.radio_group.addButton(self.none_filled_radio)

        self.interpolated_radio.toggled.connect(self.update_interpolation_mode)

        radio_layout = QHBoxLayout()
        radio_layout.addWidget(self.interpolated_radio)
        radio_layout.addWidget(self.none_filled_radio)

        self.status_log = QTextEdit()
        self.status_log.setReadOnly(True)
        self.status_log.setPlaceholderText("Logs will appear here...")

        self.file_list = QListWidget()

        layout.addWidget(QLabel("Loading data"))
        layout.addWidget(self.csv_button)
        layout.addWidget(self.json_button)
        layout.addLayout(radio_layout)
        layout.addWidget(QLabel("Loaded files:"))
        layout.addWidget(self.file_list)
        layout.addWidget(QLabel("Logs:"))
        layout.addWidget(self.status_log)

        self.setLayout(layout)

    def update_interpolation_mode(self):
        self.interpolated = self.interpolated_radio.isChecked()
        logger.info(f"JSON conversion mode: {'Interpolated' if self.interpolated else 'None filled'}")

    def log(self, message):
        logger.info(message)
        self.status_log.append(message)

    def load_csv(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Choose CSV files", filter="CSV Files (*.csv)")
        for file_path in files:
            if file_path and file_path not in self.loaded_files:
                wrapper = DataFrameWrapper(file_path)
                self.loaded_files.append(file_path)
                self.file_list.addItem(file_path)
                if self.add_callback:
                    self.add_callback(file_path, wrapper)
                if self.add_file_widget:
                    self.add_file_widget(file_path)
                self.log(f"Wczytano plik CSV: {file_path}")

    def load_json(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Choose JSON files", filter="JSON Files (*.json)")
        for file_path in files:
            if file_path:
                base_path = os.path.splitext(file_path)[0]
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        import json
                        data = json.load(f)
                        parser = JSONParser(data, base_path, interpolated=self.interpolated, dynamic_fields=True)
                        generated_paths = parser.json_to_csv()
                        for path in generated_paths:
                            if self.add_file_widget:
                                self.add_file_widget(path)
                        self.log(f"Converted JSON to CSV: {base_path}_interpolated_adv.csv / lpb.csv")
                except Exception as e:
                    self.log(f"JSON conversion error: {e}")


class FlightPlotPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Flight Data Plot Panel"))
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
        self.dataframes = {}  # dictionary with file_path -> DataFrameWrapper
        self.active_button = None

        main_layout = QHBoxLayout()

        # Left Sidebar Layout
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setSpacing(10)

        self.load_button = QPushButton("1. Load data")
        self.flight_plot_button = QPushButton("2. Flight Plot")
        self.processing_button = QPushButton("3. Postprocess data")
        self.plotter_button = QPushButton("4. Plot")

        self.buttons = [
            self.load_button,
            self.flight_plot_button,
            self.processing_button,
            self.plotter_button
        ]

        for btn in self.buttons:
            btn.setCheckable(True)
            btn.setStyleSheet("QPushButton { padding: 6px; } QPushButton:checked { background-color: lightblue; }")

        self.load_button.clicked.connect(lambda: self.change_panel(0, self.load_button))
        self.flight_plot_button.clicked.connect(lambda: self.change_panel(1, self.flight_plot_button))
        self.processing_button.clicked.connect(lambda: self.change_panel(2, self.processing_button))
        self.plotter_button.clicked.connect(lambda: self.change_panel(3, self.plotter_button))

        sidebar_layout.addWidget(self.load_button)
        sidebar_layout.addWidget(self.flight_plot_button)
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
        self.upload_panel = UploadPanel(add_callback=self.add_dataframe, add_file_widget=self.add_file)
        self.flight_panel = FlightPlotPanel()
        self.processing_panel = DataProcessingPanel()
        self.plotting_panel = PlottingPanel()

        self.stack.addWidget(self.upload_panel)      # index 0
        self.stack.addWidget(self.flight_panel)      # index 1
        self.stack.addWidget(self.processing_panel)  # index 2
        self.stack.addWidget(self.plotting_panel)    # index 3

        main_layout.addLayout(sidebar_layout, stretch=1)
        main_layout.addWidget(self.stack, stretch=4)

        self.setLayout(main_layout)
        self.change_panel(0, self.load_button)  # Set initial panel

    def change_panel(self, index, button):
        self.stack.setCurrentIndex(index)
        if self.active_button:
            self.active_button.setChecked(False)
        button.setChecked(True)
        self.active_button = button

    def add_dataframe(self, file_path, wrapper):
        self.dataframes[file_path] = wrapper

    def _is_duplicate(self, file_path):
        return any(w.file_path == file_path for w in self.file_widgets)

    def add_file(self, file_path):
        if self._is_duplicate(file_path):
            return
        file_widget = FileWidget(file_path, self.remove_file)
        self.file_widgets.append(file_widget)
        self.file_list_layout.addWidget(file_widget)

    def remove_file(self, widget):
        self.file_widgets.remove(widget)
        widget.setParent(None)
        widget.deleteLater()
