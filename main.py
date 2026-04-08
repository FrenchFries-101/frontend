import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QPoint, QTimer
from PySide6.QtWidgets import QWidget
from pages.LoginWindows import LoginWindow
from pages.MainWindows import MainWindow
from pages.RegisterWindow import RegisterWindow
from pages.IELTSTestWindow import IELTSTestWindow
from utils.loading_overlay import LoadingOverlay
from utils.path_utils import resource_path
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QAction, QIcon
from floating_icon import FloatingIcon
from desktop_plan_widget import DesktopPlanWidget

from pages.TedTestWindow import TedTestWindow

# ── 新增：导入 SplashScreen ──
from splash_screen import SplashScreen


class AppWindow(QMainWindow):
    # ↓↓↓ 这里完全不用改，和你原来一模一样 ↓↓↓
    def __init__(self):
        super().__init__()
        self.test_page = IELTSTestWindow()
        self.ted_test_page = TedTestWindow()
        self.desktop_plan_widget = DesktopPlanWidget()

        self.stack = QStackedWidget()

        self.login_page = LoginWindow()
        self.register_page = RegisterWindow()
        self.main_page = MainWindow()

        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.main_page)
        self.stack.addWidget(self.test_page)
        self.stack.addWidget(self.register_page)
        self.stack.addWidget(self.ted_test_page)

        self.setCentralWidget(self.stack)

        self.login_page.login_success.connect(self.slide_to_main)
        self.login_page.ui.pushButton_2.clicked.connect(self.slide_to_register)
        self.register_page.register_success.connect(self.slide_to_main)
        self.register_page.go_login.connect(self.slide_to_login)
        self.main_page.exit_signal.connect(self.slide_to_login)
        self.main_page.start_test_signal.connect(self.slide_to_test)
        self.main_page.start_ted_signal.connect(self.slide_to_ted)
        self.main_page.open_desktop_calendar_signal.connect(self.show_desktop_calendar)
        self.test_page.exit_test_signal.connect(self.slide_back_to_main)
        self.ted_test_page.exit_signal.connect(self.slide_back_to_main)

        self.load_qss()
        self.loading = LoadingOverlay(self)
        self.loading.resize(self.size())
        self.init_tray()
        self.floating_icon = FloatingIcon(self)

    # ↓↓↓ 以下所有方法和你原来完全一样，无需修改 ↓↓↓
    def slide_to_main(self):
        if not hasattr(self, "main_page"):
            self.stack.removeWidget(self.stack.widget(1))
            self.stack.insertWidget(1, self.main_page)
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
        self.anim2.finished.connect(self.start_load_main)
        self.stack.setCurrentIndex(next_index)

    def slide_to_login(self):
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
        self.anim1 = QPropertyAnimation(current_widget, b"pos")
        self.anim1.setDuration(500)
        self.anim1.setStartValue(QPoint(0, 0))
        self.anim1.setEndValue(QPoint(width, 0))
        self.anim1.setEasingCurve(QEasingCurve.OutCubic)
        self.anim2 = QPropertyAnimation(next_widget, b"pos")
        self.anim2.setDuration(500)
        self.anim2.setStartValue(QPoint(-width, 0))
        self.anim2.setEndValue(QPoint(0, 0))
        self.anim2.setEasingCurve(QEasingCurve.OutCubic)
        self.anim1.start()
        self.anim2.start()
        overlay.hide()
        self.stack.setCurrentIndex(next_index)

    def slide_to_test(self, cam, test, section, section_number):
        self.test_page.set_data(cam, test, section, section_number)
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
        next_index = 1
        current_widget = self.stack.widget(current_index)
        next_widget = self.stack.widget(next_index)
        width = self.stack.frameRect().width()
        next_widget.move(-width, 0)
        next_widget.show()
        self.anim1 = QPropertyAnimation(current_widget, b"pos")
        self.anim1.setDuration(500)
        self.anim1.setStartValue(QPoint(0, 0))
        self.anim1.setEndValue(QPoint(width, 0))
        self.anim1.setEasingCurve(QEasingCurve.OutCubic)
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
            with open(resource_path("styles/style.qss"), "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except:
            print("QSS not found")

    def slide_to_register(self):
        current_index = self.stack.currentIndex()
        next_index = 3
        current_widget = self.stack.widget(current_index)
        next_widget = self.stack.widget(next_index)
        width = self.stack.frameRect().width()
        next_widget.move(width, 0)
        next_widget.show()
        overlay = QWidget(self.stack)
        overlay.setStyleSheet("background-color: rgba(255,255,255,120);")
        overlay.resize(self.stack.size())
        overlay.show()
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
        overlay.hide()
        self.stack.setCurrentIndex(next_index)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.loading.resize(self.size())

    def show_desktop_calendar(self):
        self.desktop_plan_widget.show()
        self.desktop_plan_widget.raise_()
        self.desktop_plan_widget.activateWindow()

    def load_main_data(self):
        self.main_page.load_data()
        self.loading.hide()

    def start_load_main(self):
        import session
        self.main_page.set_user(session.user)
        self.loading.show()
        QTimer.singleShot(100, self.load_main_data)
        # 登录成功后显示浮动狐狸（使用用户当前皮肤）
        if session.user and hasattr(session.user, 'id'):
            self.floating_icon.show_with_skin(session.user.id)
        elif isinstance(session.user, dict) and session.user.get('id'):
            self.floating_icon.show_with_skin(session.user['id'])

    def logout_cleanup(self):
        import session
        session.user = None
        self.login_page.ui.lineEdit_2.clear()
        self.main_page.clear_data()
        self.floating_icon.hide_fox()

    def init_tray(self):
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(QIcon(resource_path("resources/icons/unicorn.png")))
        menu = QMenu()
        open_action   = QAction("Open")
        main_action   = QAction("Main Menu")
        test_action   = QAction("IELTS Test")
        logout_action = QAction("Logout")
        quit_action   = QAction("Exit")
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


# ── 文件顶部加这一行 import ──
from splash_screen import SplashScreen

# ════════════════════════════════
#  底部启动入口 —— 替换原来的5行
# ════════════════════════════════
app = QApplication(sys.argv)

# 1. 先显示 Splash
splash = SplashScreen()
splash.show()

# 2. 用一个容器持有 window，防止被垃圾回收
_holder = []

# 3. ★ 关键：在 Splash 播放期间（1秒后）就开始创建 AppWindow
#    此时狐狸还在破壳，用户完全感知不到卡顿
def _create_app():
    w = AppWindow()
    _holder.append(w)          # 存起来，等 Splash 结束再 show

QTimer.singleShot(800, _create_app)   # Splash 开始后 0.8 秒就开始初始化

# 4. Splash 动画结束后，AppWindow 早就建好了，直接 show
def on_splash_done():
    if _holder:
        w = _holder[0]
    else:
        # 极端情况：机器太慢，还没建好，就现在建
        w = AppWindow()
        _holder.append(w)
    w.showMaximized()
    w.show()

splash.finished.connect(on_splash_done)

sys.exit(app.exec())
