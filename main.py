import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtWidgets import QWidget

from pages.LoginWindows import LoginWindow
from pages.MainWindows import MainWindow


class AppWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.stack = QStackedWidget()

        self.login_page = LoginWindow()
        self.main_page = MainWindow()

        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.main_page)

        self.setCentralWidget(self.stack)

        self.login_page.login_success.connect(self.slide_to_main)
        self.main_page.exit_signal.connect(self.slide_to_login)

    def slide_to_main(self):

        current_index = self.stack.currentIndex()
        next_index = 1

        current_widget = self.stack.widget(current_index)
        next_widget = self.stack.widget(next_index)

        width = self.stack.frameRect().width()

        next_widget.move(width, 0)
        next_widget.show()

        overlay = QWidget(self.stack)
        overlay.setStyleSheet("background-color: rgba(255,255,255,120);")
        overlay.resize(self.stack.size())
        overlay.show()

        # 当前页面滑出
        self.anim1 = QPropertyAnimation(current_widget, b"pos")
        self.anim1.setDuration(500)
        self.anim1.setStartValue(QPoint(0, 0))
        self.anim1.setEndValue(QPoint(-width, 0))
        self.anim1.setEasingCurve(QEasingCurve.OutCubic)

        # 新页面滑入
        self.anim2 = QPropertyAnimation(next_widget, b"pos")
        self.anim2.setDuration(500)
        self.anim2.setStartValue(QPoint(width, 0))
        self.anim2.setEndValue(QPoint(0, 0))
        self.anim2.setEasingCurve(QEasingCurve.OutCubic)

        self.anim1.start()
        self.anim2.start()

        overlay.hide()

        self.stack.setCurrentIndex(next_index)

    def slide_to_login(self):
        current_index = self.stack.currentIndex()
        next_index = 0

        current_widget = self.stack.widget(current_index)
        next_widget = self.stack.widget(next_index)

        width = self.stack.frameRect().width()

        next_widget.move(-width, 0)
        next_widget.show()

        overlay = QWidget(self.stack)
        overlay.setStyleSheet("background-color: rgba(255,255,255,120);")
        overlay.resize(self.stack.size())
        overlay.show()

        # 当前页面滑出
        self.anim1 = QPropertyAnimation(current_widget, b"pos")
        self.anim1.setDuration(500)
        self.anim1.setStartValue(QPoint(0, 0))
        self.anim1.setEndValue(QPoint(width, 0))
        self.anim1.setEasingCurve(QEasingCurve.OutCubic)

        # 登录页滑入
        self.anim2 = QPropertyAnimation(next_widget, b"pos")
        self.anim2.setDuration(500)
        self.anim2.setStartValue(QPoint(-width, 0))
        self.anim2.setEndValue(QPoint(0, 0))
        self.anim2.setEasingCurve(QEasingCurve.OutCubic)

        self.anim1.start()
        self.anim2.start()

        overlay.hide()

        self.stack.setCurrentIndex(next_index)


app = QApplication(sys.argv)

window = AppWindow()
window.resize(1000, 700)
window.show()

sys.exit(app.exec())