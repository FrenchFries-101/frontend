import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtWidgets import QWidget

from pages.LoginWindows import LoginWindow
from pages.MainWindows import MainWindow
from pages.RegisterWindow import RegisterWindow
from pages.IELTSTestWindow import IELTSTestWindow

class AppWindow(QMainWindow):

    def __init__(self):
        super().__init__()


        self.test_page = IELTSTestWindow()

        self.stack = QStackedWidget()

        self.login_page = LoginWindow()
        self.register_page = RegisterWindow()  # <-- 新增
        #self.main_page = MainWindow()

        self.stack.addWidget(self.login_page)
        #self.stack.addWidget(self.main_page)
        self.stack.addWidget(QWidget())
        self.stack.addWidget(self.test_page)  # index 2
        self.stack.addWidget(self.register_page)

        self.setCentralWidget(self.stack)

        self.login_page.login_success.connect(self.slide_to_main)
        self.login_page.ui.pushButton_2.clicked.connect(self.slide_to_register)  # Login 页的“Register”按钮

        self.register_page.register_success.connect(self.slide_to_main)  # 注册成功跳到主界面
        self.register_page.go_login.connect(self.slide_to_login)  # 点击已有账号返回登录
        self.test_page.exit_test_signal.connect(self.slide_back_to_main)

        self.load_qss()


    def slide_to_main(self):

        if not hasattr(self, "main_page"):
            self.main_page = MainWindow()

            # 替换 stack 里的占位 widget
            self.stack.removeWidget(self.stack.widget(1))
            self.stack.insertWidget(1, self.main_page)

            # 绑定信号（必须在这里做）
            self.main_page.exit_signal.connect(self.slide_to_login)
            self.main_page.start_test_signal.connect(self.slide_to_test)

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

    def slide_to_test(self, cam, test, section):

        # ✅ 先传数据
        print("主界面传section",section)
        self.test_page.set_data(cam, test, section)

        current_index = self.stack.currentIndex()
        next_index = 2

        current_widget = self.stack.widget(current_index)
        next_widget = self.stack.widget(next_index)

        width = self.stack.frameRect().width()

        next_widget.move(width, 0)
        next_widget.show()

        self.anim1 = QPropertyAnimation(current_widget, b"pos")
        self.anim1.setDuration(500)
        self.anim1.setStartValue(QPoint(0, 0))
        self.anim1.setEndValue(QPoint(-width, 0))
        self.anim1.setEasingCurve(QEasingCurve.OutCubic)

        self.anim2 = QPropertyAnimation(next_widget, b"pos")
        self.anim2.setDuration(500)
        self.anim2.setStartValue(QPoint(width, 0))
        self.anim2.setEndValue(QPoint(0, 0))
        self.anim2.setEasingCurve(QEasingCurve.OutCubic)

        self.anim1.start()
        self.anim2.start()

        self.stack.setCurrentIndex(next_index)

    def slide_back_to_main(self):
        current_index = self.stack.currentIndex()
        next_index = 1  # main page

        current_widget = self.stack.widget(current_index)
        next_widget = self.stack.widget(next_index)

        width = self.stack.frameRect().width()

        next_widget.move(-width, 0)
        next_widget.show()

        # 当前页面滑出
        self.anim1 = QPropertyAnimation(current_widget, b"pos")
        self.anim1.setDuration(500)
        self.anim1.setStartValue(QPoint(0, 0))
        self.anim1.setEndValue(QPoint(width, 0))
        self.anim1.setEasingCurve(QEasingCurve.OutCubic)

        # 主界面滑入
        self.anim2 = QPropertyAnimation(next_widget, b"pos")
        self.anim2.setDuration(500)
        self.anim2.setStartValue(QPoint(-width, 0))
        self.anim2.setEndValue(QPoint(0, 0))
        self.anim2.setEasingCurve(QEasingCurve.OutCubic)

        self.anim1.start()
        self.anim2.start()

        self.stack.setCurrentIndex(next_index)

    def load_qss(self):

        try:
            with open("styles/style.qss", "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except:
            print("QSS not found")

    def slide_to_register(self):
        current_index = self.stack.currentIndex()
        next_index = 3  # register page

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


app = QApplication(sys.argv)

window = AppWindow()
window.resize(1000, 700)
window.show()

sys.exit(app.exec())