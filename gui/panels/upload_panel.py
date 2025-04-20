from PyQt6.QtWidgets import (
    QWidget, QPushButton, QLabel, QVBoxLayout,
    QFileDialog, QHBoxLayout, QListWidget, QTextEdit,
    QRadioButton, QButtonGroup, QProgressDialog
)
from PyQt6.QtCore import QThreadPool, Qt
import os
import json
from src.data_processing import DataFrameWrapper
from src.json_parser import JSONParser
from src.processing_utils import Worker, logger


class UploadPanel(QWidget):
    def __init__(self, add_callback=None, add_file_widget=None):
        super().__init__()
        self.add_callback = add_callback
        self.add_file_widget = add_file_widget
        self.loaded_files = []
        self.interpolated = True
        self.threadpool = QThreadPool()

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
        self.log(f"JSON conversion mode: {'Interpolated' if self.interpolated else 'None filled'}")

    def log(self, message):
        logger.info(message)
        self.status_log.append(message)

    def load_csv(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Choose CSV files", filter="CSV Files (*.csv)")
        if not files:
            return

        self.show_processing_dialog()
        worker = Worker(self._process_csv_files, files)
        worker.signals.finished.connect(self.processing_dialog.close)
        worker.signals.error.connect(lambda e: self.log(f"CSV error: {e}"))
        self.threadpool.start(worker)

    def _process_csv_files(self, file_paths):
        for file_path in file_paths:
            if file_path and file_path not in self.loaded_files:
                wrapper = DataFrameWrapper(file_path)
                self.loaded_files.append(file_path)
                if self.add_callback:
                    self.add_callback(file_path, wrapper)
                if self.add_file_widget:
                    self.add_file_widget(file_path)
                self.log(f"Loaded CSV file: {file_path}")

    def remove_dataframe(self, file_path):
        if file_path in self.loaded_files:
            self.loaded_files.remove(file_path)

            for i in range(self.file_list.count()):
                if self.file_list.item(i).text() == file_path:
                    self.file_list.takeItem(i)
                    break

            self.log(f"File removed: {file_path}")

    def load_json(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Choose JSON files", filter="JSON Files (*.json)")
        if not files:
            return

        self.show_processing_dialog()
        worker = Worker(self._process_json_files, files)
        worker.signals.finished.connect(self.processing_dialog.close)
        worker.signals.error.connect(lambda e: self.log(f"JSON error: {e}"))
        self.threadpool.start(worker)

    def _process_json_files(self, file_paths):
        for file_path in file_paths:
            base_path = os.path.splitext(file_path)[0]
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                parser = JSONParser(data, base_path, interpolated=self.interpolated)
                generated_paths = parser.json_to_csv()
                for path in generated_paths:
                    if self.add_file_widget:
                        self.add_file_widget(path)
                self.log(f"Converted JSON to CSVs: {base_path}")

    def show_processing_dialog(self):
        self.processing_dialog = QProgressDialog("Processing, please wait...", None, 0, 0, self)
        self.processing_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.processing_dialog.setCancelButton(None)
        self.processing_dialog.setMinimumDuration(0)
        self.processing_dialog.show()
