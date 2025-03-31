from PyQt6.QtWidgets import (
    QWidget, QPushButton, QLabel, QVBoxLayout,
    QFileDialog, QHBoxLayout, QListWidget, QTextEdit,
    QRadioButton, QButtonGroup
)
import os
from src.data_processing import DataFrameWrapper
from src.json_parser import JSONParser
from src.logs import logger


class UploadPanel(QWidget):
    def __init__(self, add_callback=None, add_file_widget=None):
        super().__init__()
        self.add_callback = add_callback
        self.add_file_widget = add_file_widget
        self.loaded_files = []
        self.interpolated = True

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
                self.log(f"Loaded CSV file: {file_path}")

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
