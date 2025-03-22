from PyQt6.QtWidgets import (
        QApplication, QWidget, QPushButton, QLabel,
        QVBoxLayout, QFileDialog, QHBoxLayout, QScrollArea
    )
from PyQt6.QtCore import Qt
import sys
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


class FileLoaderApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("File Loader GUI")
        self.resize(400, 300)

        self.file_widgets = []

        main_layout = QVBoxLayout()

        self.load_button = QPushButton("Load File(s)")
        self.load_button.clicked.connect(self.load_files)
        main_layout.addWidget(self.load_button)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.file_list_widget = QWidget()
        self.file_list_layout = QVBoxLayout()
        self.file_list_layout.setSpacing(5)
        self.file_list_widget.setLayout(self.file_list_layout)

        self.scroll_area.setWidget(self.file_list_widget)
        main_layout.addWidget(self.scroll_area)

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileLoaderApp()
    window.show()
    sys.exit(app.exec())
