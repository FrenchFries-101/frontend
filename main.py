import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QPoint,QTimer
from PySide6.QtWidgets import QWidget
from pages.LoginWindows import LoginWindow
from pages.MainWindows import MainWindow
from pages.RegisterWindow import RegisterWindow
from pages.IELTSTestWindow import IELTSTestWindow
from utils.loading_overlay import LoadingOverlay
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QAction, QIcon
from floating_icon import FloatingIcon

from pages.TedTestWindow import TedTestWindow

class AppWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.test_page = IELTSTestWindow()
        self.ted_test_page = TedTestWindow()

        self.stack = QStackedWidget()

        self.login_page = LoginWindow()
        self.register_page = RegisterWindow()  # <-- 新增
        self.main_page = MainWindow()

        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.main_page)
        #这个占位是用来干什么的
        #self.stack.addWidget(QWidget())
        self.stack.addWidget(self.test_page)  # index 2
        self.stack.addWidget(self.register_page)
        self.stack.addWidget(self.ted_test_page)

        self.setCentralWidget(self.stack)

        self.login_page.login_success.connect(self.slide_to_main)
        self.login_page.ui.pushButton_2.clicked.connect(self.slide_to_register)  # Login 页的“Register”按钮

        self.register_page.register_success.connect(self.slide_to_main)  # 注册成功跳到主界面
        self.register_page.go_login.connect(self.slide_to_login)  # 点击已有账号返回登录

        self.main_page.exit_signal.connect(self.slide_to_login)
        self.main_page.start_test_signal.connect(self.slide_to_test)
        self.main_page.start_ted_signal.connect(self.slide_to_ted)
        self.test_page.exit_test_signal.connect(self.slide_back_to_main)
        self.ted_test_page.exit_signal.connect(self.slide_back_to_main)

        self.load_qss()

        self.loading = LoadingOverlay(self)
        self.loading.resize(self.size())

        self.init_tray()
        self.floating_icon = FloatingIcon(self)


    def slide_to_main(self):

        if not hasattr(self, "main_page"):
            #self.main_page = MainWindow()

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

        # 动画结束后再加载数据
        self.anim2.finished.connect(self.start_load_main)

        self.stack.setCurrentIndex(next_index)

        # overlay.hide()
        #
        # self.stack.setCurrentIndex(next_index)
        # self.loading.show()
        #
        # self.anim2.finished.connect(self.start_load_main)

    def slide_to_login(self):
        #先全部清空一遍
        self.logout_cleanup()

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

    def slide_to_test(self, cam, test, section,section_number):

        # ✅ 先传数据
        print("主界面传section",section)
        self.test_page.set_data(cam, test, section,section_number)

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

    def slide_to_ted(self, talk_id, title, audio_path):                                             
        self.ted_test_page.set_data(talk_id, title, audio_path)               
        current_index = self.stack.currentIndex()
        next_index = 4

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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.loading.resize(self.size())

    def load_main_data(self):
        self.main_page.load_data()
        self.loading.hide()

    # def start_loading_main(self):
    #     import session
    #     self.main_page.set_user(session.user)
    #
    #     self.loading.show()
    #
    #     QTimer.singleShot(100, self.load_main_data)

    def start_load_main(self):
        import session
        self.main_page.set_user(session.user)

        self.loading.show()

        QTimer.singleShot(100, self.load_main_data)

    def logout_cleanup(self):
        import session

        # 1. 清除 session
        session.user = None

        # 2. 清空 login 输入框
        #self.login_page.ui.username_lineEdit.clear()
        self.login_page.ui.lineEdit_2.clear()

        # 3. 清空 main 页面数据
        self.main_page.clear_data()

    def init_tray(self):
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(QIcon("resources/icons/unicorn.png"))

        menu = QMenu()

        open_action = QAction("Open")
        main_action = QAction("Main Menu")
        test_action = QAction("IELTS Test")
        logout_action = QAction("Logout")
        quit_action = QAction("Exit")

        open_action.triggered.connect(self.show_window)
        main_action.triggered.connect(lambda: self.stack.setCurrentIndex(1))
        test_action.triggered.connect(lambda: self.stack.setCurrentIndex(2))
        logout_action.triggered.connect(self.slide_to_login)
        quit_action.triggered.connect(self.quit_app)

        menu.addAction(open_action)
        menu.addAction(main_action)
        menu.addAction(test_action)
        menu.addAction(logout_action)
        menu.addSeparator()
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.tray_clicked)
        self.tray.show()

    def show_window(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def tray_clicked(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window()

    def quit_app(self):
        self.tray.hide()
        QApplication.quit()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray.showMessage(
            "IELTS Assistant",
            "App is minimized to tray",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )


app = QApplication(sys.argv)

window = AppWindow()
#window.resize(1000, 700)
window.showMaximized()
window.show()

sys.exit(app.exec())
