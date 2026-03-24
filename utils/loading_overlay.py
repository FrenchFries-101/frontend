from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QMovie


class LoadingOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setStyleSheet("background-color: rgba(0, 0, 0, 120);")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        self.label = QLabel("Loading...")
        self.label.setStyleSheet("color: white; font-size: 16px;")

        self.spinner = QLabel()

        # GIF 转圈动画
        self.movie = QMovie("resources/icons/loading.gif")
        self.spinner.setMovie(self.movie)
        self.movie.start()

        layout.addWidget(self.spinner, alignment=Qt.AlignCenter)
        layout.addWidget(self.label, alignment=Qt.AlignCenter)

        self.hide()

    def resizeEvent(self, event):
        self.resize(self.parent().size())