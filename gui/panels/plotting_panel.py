from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QHBoxLayout,
    QPushButton, QLineEdit, QFormLayout,
    QGroupBox, QScrollArea, QListWidget, QFrame, QTextEdit
)
from src.plotter import Plotter
from src.logs import logger
from src.data_processing import DataProcessor


class PlottingPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.dataframes = {}
        self.secondary_db_offset = 0

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Plotting Panel"))

        self.plot_name = QLineEdit("Plot Title")
        layout.addWidget(self.plot_name)

        self.x_axis_label = QLineEdit("Time")
        self.y1_axis_label = QLineEdit("Y1 Axis")
        self.y2_axis_label = QLineEdit("Y2 Axis")

        layout.addWidget(QLabel("X Axis Label:"))
        layout.addWidget(self.x_axis_label)
        layout.addWidget(QLabel("Y1 Axis Label:"))
        layout.addWidget(self.y1_axis_label)
        layout.addWidget(QLabel("Y2 Axis Label:"))
        layout.addWidget(self.y2_axis_label)

        self.offset_input = QLineEdit("0")
        layout.addWidget(QLabel("Offset (ms):"))
        layout.addWidget(self.offset_input)

        self.convert_epoch = QComboBox()
        self.convert_epoch.addItems(["none", "seconds", "miliseconds"])
        layout.addWidget(QLabel("Convert epoch to:"))
        layout.addWidget(self.convert_epoch)

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

        sync_layout = QHBoxLayout()

        sync_col1_layout = QVBoxLayout()
        sync_col1_layout.addWidget(QLabel("Sync column DB1:"))
        self.sync_col1 = QComboBox()
        sync_col1_layout.addWidget(self.sync_col1)
        sync_layout.addLayout(sync_col1_layout)

        sync_col2_layout = QVBoxLayout()
        sync_col2_layout.addWidget(QLabel("Sync column DB2:"))
        self.sync_col2 = QComboBox()
        sync_col2_layout.addWidget(self.sync_col2)
        sync_layout.addLayout(sync_col2_layout)

        sync_return_layout = QVBoxLayout()
        self.sync_button = QPushButton("Sync DBs/Get start offset")
        self.sync_button.clicked.connect(self.sync_databases)
        sync_return_layout.addWidget(self.sync_button)
        self.start_offset = QLineEdit("Start offset:")
        self.start_offset.setReadOnly(True)
        sync_return_layout.addWidget(self.start_offset)
        sync_layout.addLayout(sync_return_layout)

        layout.addLayout(sync_layout)

        self.db1_box = self.create_database_box("db1")
        self.db2_box = self.create_database_box("db2")

        db_layout = QHBoxLayout()
        db_layout.addWidget(self.db1_box)
        db_layout.addWidget(self.db2_box)
        layout.addLayout(db_layout)

        self.h_lines_box = self.create_lines_box("horizontal")
        self.v_lines_box = self.create_lines_box("vertical")
        lines_layout = QHBoxLayout()
        lines_layout.addWidget(self.h_lines_box)
        lines_layout.addWidget(self.v_lines_box)
        layout.addLayout(lines_layout)

        self.generate_button = QPushButton("Generate Plot")
        self.generate_button.clicked.connect(self.generate_plot)
        layout.addWidget(self.generate_button)

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

    def create_lines_box(self, line_type):
        box = QGroupBox(f"{line_type.title()} Lines")
        layout = QVBoxLayout()
        box.setLayout(layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        lines_layout = QVBoxLayout()
        container.setLayout(lines_layout)
        scroll.setWidget(container)

        add_button = QPushButton(f"Add {line_type.title()} Line")
        add_button.clicked.connect(lambda: self.add_line_row(lines_layout))

        layout.addWidget(scroll)
        layout.addWidget(add_button)
        box.lines_layout = lines_layout
        return box

    def add_line_row(self, layout):
        container = QFrame()
        form = QFormLayout()

        label_input = QLineEdit()
        value_input = QLineEdit()

        color_input = QComboBox()
        color_input.addItems(['blue', 'red', 'green', 'cyan', 'purple', 'olive', 'pink', 'gray', 'brown'])

        remove_button = QPushButton("Remove")
        remove_button.clicked.connect(lambda: self.remove_input(container))

        form.addRow("Label:", label_input)
        form.addRow("Value:", value_input)
        form.addRow("Color:", color_input)
        form.addRow(remove_button)

        container.setLayout(form)
        layout.addWidget(container)

    def sync_databases(self):
        db1_path = self.db1_selector.currentText()
        db2_path = self.db2_selector.currentText()
        col1 = self.sync_col1.currentText()
        col2 = self.sync_col2.currentText()

        if db1_path not in self.dataframes or db2_path not in self.dataframes:
            self.log("Both DBs must be selected for syncing.")
            return

        try:
            dp1 = DataProcessor(self.dataframes[db1_path])
            dp2 = DataProcessor(self.dataframes[db2_path])
            df1 = dp1.get_processed_data()
            df2 = dp2.get_processed_data()

            idx1, val1 = dp1.find_index_where_max("header.timestamp_epoch", col1)
            _, val2 = dp2.find_index_where_max("header.timestamp_epoch", col2)
            self.secondary_db_offset = val1 - val2
            self.log(f"Syncing DB2 by offset {self.secondary_db_offset} based on max of {col1} and {col2}")

            df2["header.timestamp_epoch"] = df2["header.timestamp_epoch"].compute() + self.secondary_db_offset
            dp2.df_wrapper.update_dataframe(df2)

            first_value = df1['header.timestamp_epoch'].compute().iloc[0]
            start_offset = first_value - val1
            self.start_offset.setText(f"Start offset = {start_offset}")

        except Exception as e:
            self.log(f"Error during DB sync: {e}")

    def refresh_channel_box(self, db_key):
        if db_key == "db1":
            for i in reversed(range(self.db1_box.channel_layout.count())):
                self.db1_box.channel_layout.itemAt(i).widget().deleteLater()
            self.sync_col1.clear()
            path = self.db1_selector.currentText()
            if path in self.dataframes:
                df = self.dataframes[path].get_dataframe()
                self.sync_col1.addItems(df.columns)
        elif db_key == "db2":
            for i in reversed(range(self.db2_box.channel_layout.count())):
                self.db2_box.channel_layout.itemAt(i).widget().deleteLater()
            self.sync_col2.clear()
            path = self.db2_selector.currentText()
            if path in self.dataframes:
                df = self.dataframes[path].get_dataframe()
                self.sync_col2.addItems(df.columns)

    def add_plot_column(self, db_key):
        container = QFrame()
        form = QFormLayout()

        columns = []
        colors = ['blue', 'red', 'green', 'cyan', 'purple', 'olive', 'pink', 'gray', 'brown']
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

        color_input = QComboBox()
        color_input.addItems(colors)

        transparency_input = QLineEdit()
        y_axis_input = QComboBox()
        y_axis_input.addItems(["y1", "y2"])
        x_column_input = QLineEdit("header.timestamp_epoch")

        remove_button = QPushButton("Remove")
        remove_button.clicked.connect(lambda: self.remove_input(container))

        form.addRow("Channel:", channel_input)
        form.addRow("Label:", label_input)
        form.addRow("Color:", color_input)
        form.addRow("Transparency:", transparency_input)
        form.addRow("Y Axis:", y_axis_input)
        form.addRow("X Column:", x_column_input)
        form.addRow(remove_button)

        container.setLayout(form)

        if db_key == "db1":
            self.db1_box.channel_layout.addWidget(container)
        elif db_key == "db2":
            self.db2_box.channel_layout.addWidget(container)

    def generate_plot(self):
        db1_path = self.db1_selector.currentText()
        db2_path = self.db2_selector.currentText()
        try:
            offset_val = float(self.offset_input.text())
        except ValueError:
            offset_val = 0

        config = {
            "plot_settings": {
                "title": self.plot_name.text(),
                "type": "line",
                "precise_grid": False,
                "convert_epoch": self.convert_epoch.currentText(),
                "offset": offset_val,
                "secondary_db_offset": self.secondary_db_offset,
                "x_axis_label": self.x_axis_label.text(),
                "y_axis_labels": {
                    "y1": self.y1_axis_label.text(),
                    "y2": self.y2_axis_label.text()
                },
                "horizontal_lines": self.collect_lines(self.h_lines_box.lines_layout),
                "vertical_lines": self.collect_lines(self.v_lines_box.lines_layout)
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
                    if len(combo_boxes) >= 3:
                        channel_combo = combo_boxes[0]
                        color_combo = combo_boxes[1]
                        y_axis_combo = combo_boxes[2]
                        channel = channel_combo.currentText()
                        db_config["channels"][channel] = {
                            "label": fields[0].text(),
                            "color": color_combo.currentText(),
                            "alpha": float(fields[1].text()) if fields[1].text() else 1.0,
                            "y_axis": y_axis_combo.currentText(),
                            "x_column": fields[2].text()
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

    @staticmethod
    def remove_input(widget):
        widget.setParent(None)
        widget.deleteLater()

    @staticmethod
    def collect_lines(layout):
        lines = {}
        for i in range(layout.count()):
            widget = layout.itemAt(i).widget()
            if widget:
                fields = widget.findChildren(QLineEdit)
                if len(fields) >= 3:
                    label = fields[0].text()
                    try:
                        value = float(fields[1].text())
                        color = fields[2].text()
                        lines[label] = {"place": value, "label": label, "color": color}
                    except ValueError:
                        continue
        return lines

    @staticmethod
    def log(message):
        logger.info(message)
