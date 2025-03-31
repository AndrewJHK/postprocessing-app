from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QHBoxLayout,
    QPushButton, QTextEdit, QLineEdit, QFormLayout,
    QGroupBox, QFileDialog, QScrollArea, QListWidget, QFrame
)
from PyQt6.QtCore import Qt
from src.plotter import Plotter
from src.logs import logger
import os


class PlottingPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.dataframes = {}

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Plotting Panel"))

        self.plot_name = QLineEdit("Plot Title")
        layout.addWidget(self.plot_name)

        # Database selector dropdowns
        db_selector_layout = QHBoxLayout()
        self.db1_selector = QComboBox()
        self.db2_selector = QComboBox()
        self.db1_selector.currentIndexChanged.connect(lambda: self.refresh_channel_box("db1"))
        self.db2_selector.currentIndexChanged.connect(lambda: self.refresh_channel_box("db2"))
        db_selector_layout.addWidget(QLabel("Select DB1:"))
        db_selector_layout.addWidget(self.db1_selector)
        db_selector_layout.addWidget(QLabel("Select DB2:"))
        db_selector_layout.addWidget(self.db2_selector)
        layout.addLayout(db_selector_layout)

        self.db1_box = self.create_database_box("db1")
        self.db2_box = self.create_database_box("db2")

        db_layout = QHBoxLayout()
        db_layout.addWidget(self.db1_box)
        db_layout.addWidget(self.db2_box)
        layout.addLayout(db_layout)

        self.generate_button = QPushButton("Generate Plot")
        self.generate_button.clicked.connect(self.generate_plot)
        layout.addWidget(self.generate_button)

        self.status_log = QTextEdit()
        self.status_log.setReadOnly(True)
        layout.addWidget(QLabel("Logs:"))
        layout.addWidget(self.status_log)

        self.setLayout(layout)

    def create_database_box(self, db_key):
        box = QGroupBox(f"{db_key.upper()} Channels")
        layout = QVBoxLayout()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        channel_layout = QVBoxLayout()
        container.setLayout(channel_layout)
        scroll.setWidget(container)

        add_button = QPushButton("Add Plot Column")
        add_button.clicked.connect(lambda: self.add_plot_column(db_key))

        layout.addWidget(scroll)
        layout.addWidget(add_button)

        box.setLayout(layout)
        box.channel_layout = channel_layout
        return box

    def add_plot_column(self, db_key):
        container = QFrame()
        form = QFormLayout()

        # Dynamically load columns
        columns = []
        db_selector = self.db1_selector if db_key == "db1" else self.db2_selector
        db_path = db_selector.currentText()

        if db_path in self.dataframes:
            df = self.dataframes[db_path].get_dataframe()
            try:
                columns = df.columns
            except Exception as e:
                self.log(f"Failed to fetch columns from {db_path}: {e}")

        channel_input = QComboBox()
        channel_input.addItems(columns)

        label_input = QLineEdit()
        color_input = QLineEdit()
        alpha_input = QLineEdit()
        y_axis_input = QComboBox()
        y_axis_input.addItems(["y1", "y2"])
        x_column_input = QLineEdit("header.timestamp_epoch")

        form.addRow("Channel:", channel_input)
        form.addRow("Label:", label_input)
        form.addRow("Color:", color_input)
        form.addRow("Alpha:", alpha_input)
        form.addRow("Y Axis:", y_axis_input)
        form.addRow("X Column:", x_column_input)

        container.setLayout(form)

        if db_key == "db1":
            self.db1_box.channel_layout.addWidget(container)
        elif db_key == "db2":
            self.db2_box.channel_layout.addWidget(container)

    def log(self, message):
        logger.info(message)
        self.status_log.append(message)

    def add_dataframe(self, file_path, wrapper):
        self.dataframes[file_path] = wrapper
        self.db1_selector.addItem(file_path)
        self.db2_selector.addItem(file_path)

    def remove_dataframe(self, file_path):
        if file_path in self.dataframes:
            del self.dataframes[file_path]
        index1 = self.db1_selector.findText(file_path)
        if index1 >= 0:
            self.db1_selector.removeItem(index1)
        index2 = self.db2_selector.findText(file_path)
        if index2 >= 0:
            self.db2_selector.removeItem(index2)

    def refresh_channel_box(self, db_key):
        if db_key == "db1":
            for i in reversed(range(self.db1_box.channel_layout.count())):
                self.db1_box.channel_layout.itemAt(i).widget().deleteLater()
        elif db_key == "db2":
            for i in reversed(range(self.db2_box.channel_layout.count())):
                self.db2_box.channel_layout.itemAt(i).widget().deleteLater()

    def generate_plot(self):
        db1_path = self.db1_selector.currentText()
        db2_path = self.db2_selector.currentText()

        config = {
            "plot_settings": {
                "title": self.plot_name.text(),
                "type": "line",
                "precise_grid": False,
                "convert_epoch": "seconds",
                "offset": 0,
                "x_axis_label": "Time",
                "y_axis_labels": {
                    "y1": "Y1 Axis",
                    "y2": "Y2 Axis"
                },
                "horizontal_lines": {},
                "vertical_lines": {}
            },
            "databases": {}
        }

        for db_key, db_box, db_path in [("db1", self.db1_box, db1_path), ("db2", self.db2_box, db2_path)]:
            if not db_path:
                continue
            db_config = {"channels": {}}
            for i in range(db_box.channel_layout.count()):
                widget = db_box.channel_layout.itemAt(i).widget()
                if widget:
                    fields = widget.findChildren(QLineEdit)
                    combo_boxes = widget.findChildren(QComboBox)
                    if len(combo_boxes) >= 2:
                        channel_combo = combo_boxes[0]
                        y_axis_combo = combo_boxes[1]
                        channel = channel_combo.currentText()
                        db_config["channels"][channel] = {
                            "label": fields[0].text(),
                            "color": fields[1].text(),
                            "alpha": float(fields[2].text()) if fields[2].text() else 1.0,
                            "y_axis": y_axis_combo.currentText(),
                            "x_column": fields[3].text()
                        }
            if db_config["channels"]:
                config["databases"][db_key] = db_config

        if not config["databases"]:
            self.log("No channels configured.")
            return

        selected_dataframes = {}
        if db1_path in self.dataframes:
            selected_dataframes["db1"] = self.dataframes[db1_path]
        if db2_path in self.dataframes:
            selected_dataframes["db2"] = self.dataframes[db2_path]

        plotter = Plotter(config_dict=config, dataframe_map=selected_dataframes, plots_folder_path="plots")
        try:
            plotter.plot()
            self.log("Plot generated successfully.")
        except Exception as e:
            self.log(f"Error during plot generation: {e}")
