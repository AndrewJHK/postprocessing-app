from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QHBoxLayout,
    QPushButton, QTextEdit, QCheckBox, QLineEdit, QFormLayout,
    QGroupBox, QFileDialog, QScrollArea, QListWidget
)
from PyQt6.QtCore import Qt
from src.data_processing import DataProcessor
from src.logs import logger


class DataProcessingPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.dataframes = {}
        self.processors = {}

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Data processing"))

        self.file_selector = QComboBox()
        self.file_selector.currentIndexChanged.connect(self.update_columns)
        layout.addWidget(QLabel("Choose file:"))
        layout.addWidget(self.file_selector)

        side_layout = QHBoxLayout()

        # Columns
        self.column_box = QGroupBox("Columns")
        self.column_scroll = QScrollArea()
        self.column_widget = QWidget()
        self.column_layout = QVBoxLayout()
        self.column_widget.setLayout(self.column_layout)
        self.column_scroll.setWidgetResizable(True)
        self.column_scroll.setWidget(self.column_widget)
        column_box_layout = QVBoxLayout()
        column_box_layout.addWidget(self.column_scroll)
        self.column_box.setLayout(column_box_layout)
        side_layout.addWidget(self.column_box)

        # Operations
        self.operation_box = QGroupBox("Operations")
        self.operation_selector = QComboBox()
        self.operation_selector.addItems(["normalize", "scale", "flip_sign", "sort", "drop"])
        self.operation_param = QLineEdit()
        self.apply_op_button = QPushButton("Apply operation")
        self.apply_op_button.clicked.connect(self.apply_operation)

        op_layout = QFormLayout()
        op_layout.addRow("Operation:", self.operation_selector)
        op_layout.addRow("Parameter:", self.operation_param)
        op_layout.addRow(self.apply_op_button)
        self.operation_box.setLayout(op_layout)
        side_layout.addWidget(self.operation_box)

        # Filters
        self.filter_box = QGroupBox("Filters")
        self.filter_selector = QComboBox()
        self.filter_selector.addItems(
            ["remove_negatives", "remove_positives", "rolling_mean", "rolling_median", "threshold",
             "wavelet_transform"])
        self.filter_param = QLineEdit()
        self.add_filter_button = QPushButton("Add filter")
        self.add_filter_button.clicked.connect(self.add_filter)

        filter_layout = QFormLayout()
        filter_layout.addRow("Filter:", self.filter_selector)
        filter_layout.addRow(QLabel("Parameters (ex. key1=val1,key2=val2):"))
        filter_layout.addRow(self.filter_param)
        filter_layout.addRow(self.add_filter_button)
        self.filter_box.setLayout(filter_layout)
        side_layout.addWidget(self.filter_box)

        layout.addLayout(side_layout)

        # Filter queue
        self.queue_list = QListWidget()
        queue_box = QGroupBox("Filter queue")
        queue_layout = QVBoxLayout()
        queue_layout.addWidget(self.queue_list)
        queue_box.setLayout(queue_layout)
        layout.addWidget(queue_box)

        self.apply_filters_button = QPushButton("Apply filter")
        self.apply_filters_button.clicked.connect(self.apply_filters)
        layout.addWidget(self.apply_filters_button)

        self.save_button = QPushButton("Save to file")
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

    def remove_dataframe(self, file_path):
        if file_path in self.dataframes:
            del self.dataframes[file_path]
        if file_path in self.processors:
            del self.processors[file_path]
        index = self.file_selector.findText(file_path)
        if index >= 0:
            self.file_selector.removeItem(index)

    def update_columns(self):
        self.clear_column_checkboxes()
        current_path = self.file_selector.currentText()
        if current_path and current_path in self.dataframes:
            df = self.dataframes[current_path].get_dataframe()
            for col in df.columns:
                checkbox = QCheckBox(col)
                self.column_layout.addWidget(checkbox)

    def clear_column_checkboxes(self):
        while self.column_layout.count():
            child = self.column_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def get_selected_columns(self):
        return [self.column_layout.itemAt(i).widget().text()
                for i in range(self.column_layout.count())
                if self.column_layout.itemAt(i).widget().isChecked()]

    def log(self, message):
        logger.info(message)
        self.status_log.append(message)

    def apply_operation(self):
        file_path = self.file_selector.currentText()
        columns = self.get_selected_columns()
        operation = self.operation_selector.currentText()
        param = self.operation_param.text()

        if not file_path or not columns or not operation:
            self.log("Choose file, culumn and operation.")
            return

        processor = self.processors.get(file_path)
        try:
            match operation:
                case "normalize":
                    processor.normalize_columns(columns)
                case "scale":
                    processor.scale_columns(columns, float(param))
                case "flip_sign":
                    processor.flip_column_sign(columns)
                case "sort":
                    processor.sort_data(columns[0], ascending=True)
                case "drop":
                    processor.drop_data(columns=columns)
            self.log(f"Applied operation: {operation} on columns: {columns}")
        except Exception as e:
            self.log(f"Error during operation: {e}")

    def add_filter(self):
        file_path = self.file_selector.currentText()
        columns = self.get_selected_columns()
        filter_type = self.filter_selector.currentText()
        raw_params = self.filter_param.text()
        processor = self.processors.get(file_path)

        try:
            params = dict(p.split('=') for p in raw_params.split(',') if '=' in p)
            for k in params:
                try:
                    params[k] = int(params[k]) if params[k].isdigit() else float(params[k])
                except Exception as e:
                    self.log(f"Error during operation: {e}")
            processor.add_filter(columns, filter_type, **params)
            self.queue_list.addItem(f"{filter_type} on {columns} with {params}")
            self.log(f"Added filter {filter_type} for {columns}")
        except Exception as e:
            self.log(f"Error adding filter: {e}")

    def apply_filters(self):
        file_path = self.file_selector.currentText()
        processor = self.processors.get(file_path)
        try:
            processor.queue_filters()
            self.log("Applied all queued filters")
        except Exception as e:
            self.log(f"Error during filter application: {e}")

    def save_to_file(self):
        file_path = self.file_selector.currentText()
        processor = self.processors.get(file_path)
        if processor:
            save_path, _ = QFileDialog.getSaveFileName(self, "Save as", filter="CSV Files (*.csv)")
            if save_path:
                processor.save_data(save_path)
                self.log(f"Data saved to: {save_path}")
