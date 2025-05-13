from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QComboBox, QTextEdit, QFileDialog, QHBoxLayout, QFormLayout, QLineEdit, QCheckBox
)
from PyQt6.QtCore import QThreadPool
from src.processing_utils import Worker, show_processing_dialog
from src.data_processing import DataProcessor


class FlightPlotPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.dataframes = {}
        self.threadpool = QThreadPool()
        self.processors = {}
        self.last_selected_file = None

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Flight data analysis"))

        self.file_selector = QComboBox()
        self.file_selector.currentTextChanged.connect(self._update_selection)
        layout.addWidget(self.file_selector)

        self.calc_button = QPushButton("Perform calculations")
        self.calc_button.clicked.connect(self.perform_calculations)
        layout.addWidget(self.calc_button)

        result_layout = QFormLayout()
        self.apogee_field = QLineEdit()
        self.apogee_field.setReadOnly(True)
        self.max_speed_field = QLineEdit()
        self.max_speed_field.setReadOnly(True)
        result_layout.addRow("Apogee (max altitude) [m]:", self.apogee_field)
        result_layout.addRow("Max speed [m/s]:", self.max_speed_field)
        layout.addLayout(result_layout)

        self.save_plot_checkbox = QCheckBox("Save plots to file")
        layout.addWidget(self.save_plot_checkbox)

        plot_buttons_layout = QHBoxLayout()
        self.plot_orientation_button = QPushButton("Plot orientation animation")
        self.plot_velocity_button = QPushButton("Plot velocity/acceleration")
        plot_buttons_layout.addWidget(self.plot_orientation_button)
        plot_buttons_layout.addWidget(self.plot_velocity_button)
        layout.addLayout(plot_buttons_layout)

        self.save_button = QPushButton("Save processed CSV")
        self.save_button.clicked.connect(self.save_to_file)
        layout.addWidget(self.save_button)

        self.status_log = QTextEdit()
        self.status_log.setReadOnly(True)
        layout.addWidget(QLabel("Logs:"))
        layout.addWidget(self.status_log)

        self.setLayout(layout)

    def add_dataframe(self, file_path, wrapper):
        self.dataframes[file_path] = wrapper
        self.processors[file_path] = DataProcessor(wrapper)
        self.file_selector.addItem(file_path)

    def _update_selection(self, file_path):
        self.last_selected_file = file_path

    def log(self, message):
        self.status_log.append(message)

    def perform_calculations(self):
        file_path = self.last_selected_file
        if not file_path:
            return

        processor = self.processors[file_path]

        def task():
            self.log("Starting flight profile computation...")
            processor.compute_flight_profile()
            df = processor.get_processed_data().compute()
            self.max_alt = df["z"].max()
            self.max_speed = df[["vx", "vy", "vz"]].pow(2).sum(axis=1).pow(0.5).max()
            self.log("Computation finished.")

        worker = Worker(task)
        worker.signals.finished.connect(self._update_results)
        show_processing_dialog(self, self.threadpool, worker)

    def _update_results(self):
        self.apogee_field.setText(f"{self.max_alt:.2f}")
        self.max_speed_field.setText(f"{self.max_speed:.2f}")
        self.log(f"Apogee: {self.max_alt:.2f} m")
        self.log(f"Max speed: {self.max_speed:.2f} m/s")

    def save_to_file(self):
        file_path = self.last_selected_file
        if not file_path:
            return

        processor = self.processors[file_path]
        save_path, _ = QFileDialog.getSaveFileName(self, "Save processed CSV", filter="CSV Files (*.csv)")
        if save_path:
            def task():
                processor.save_data(save_path)
                self.log(f"Data saved to: {save_path}")

            show_processing_dialog(self, self.threadpool, Worker(task))
