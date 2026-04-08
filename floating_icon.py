from PySide6.QtWidgets import QWidget, QLabel, QMenu
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QCursor,QAction,QMovie
from utils.path_utils import resource_path
from PySide6.QtWidgets import QWidget, QMenu
from PySide6.QtCore import Qt, QPoint, QTimer, QDate
from PySide6.QtGui import QCursor, QAction, QMovie, QPainter, QPixmap
import random


class FloatingIcon(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        # 窗口大小将根据 GIF 自动调整
        # 无边框 + 置顶 + 不显示在任务栏
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        # 透明背景 - 这是关键
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)

        # Fox GIF 列表
        self.fox_gifs = [
            "resources/icons/fox_1.gif",
            "resources/icons/fox_2.gif",
            "resources/icons/fox_3.gif",
            "resources/icons/fox_4.gif",
            "resources/icons/fox_5.gif",
            "resources/icons/fox_6.gif"
        ]

        # 随机选择一个 fox gif
        self.current_gif_index = random.randint(0, len(self.fox_gifs) - 1)
        self.movie = QMovie(self.fox_gifs[self.current_gif_index])
        # 连接帧变化信号
        self.movie.frameChanged.connect(self.update)
        # 连接第一帧加载完成信号
        self.movie.frameChanged.connect(self.on_first_frame_loaded)
        self.movie.start()

        # 初始时隐藏窗口，直到 GIF 加载完成
        self.hide()

        # 标记是否已加载完成
        self.first_frame_loaded = False

        # 定时器，每隔一段时间随机切换 fox gif
        self.switch_timer = QTimer()
        self.switch_timer.timeout.connect(self.switch_fox_gif)
        # 随机设置切换时间（10-30秒）
        self.switch_interval = random.randint(10000, 30000)
        self.switch_timer.start(self.switch_interval)

    def paintEvent(self, event):
        painter = QPainter(self)
        # 设置抗锯齿，使绘制更平滑
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # 完全清除背景为透明
        painter.fillRect(self.rect(), Qt.transparent)

        pixmap = self.movie.currentPixmap()
        if not pixmap.isNull():
            # 直接绘制，覆盖整个窗口
            painter.drawPixmap(0, 0, pixmap)

    def on_first_frame_loaded(self):
        # 当第一帧加载完成后，调整窗口大小并显示
        if not self.first_frame_loaded:
            self.first_frame_loaded = True
            self.adjust_window_size()
            self.show()
            # 断开这个信号，避免重复调用
            try:
                self.movie.frameChanged.disconnect(self.on_first_frame_loaded)
            except:
                pass

    def adjust_window_size(self):
        # 调整窗口大小以适应 GIF
        pixmap = self.movie.currentPixmap()
        if not pixmap.isNull():
            self.setFixedSize(pixmap.width(), pixmap.height())

    def switch_fox_gif(self):
        # 随机选择一个新的 fox gif（避免选择同一个）
        new_index = random.randint(0, len(self.fox_gifs) - 1)
        while new_index == self.current_gif_index and len(self.fox_gifs) > 1:
            new_index = random.randint(0, len(self.fox_gifs) - 1)

        self.current_gif_index = new_index

        # 停止当前动画
        self.movie.stop()

        # 隐藏窗口，直到新 GIF 加载完成
        self.hide()

        # 加载新的 gif
        self.movie = QMovie(self.fox_gifs[self.current_gif_index])
        self.movie.frameChanged.connect(self.update)
        # 连接第一帧加载完成信号
        self.first_frame_loaded = False
        self.movie.frameChanged.connect(self.on_first_frame_loaded)
        self.movie.start()

        # 随机设置下一次切换时间（10-30秒）
        self.switch_interval = random.randint(10000, 30000)
        self.switch_timer.setInterval(self.switch_interval)

    def show_today_plan(self):
        # 显示或隐藏便签
        if hasattr(self.main_window, 'desktop_plan_widget'):
            if self.main_window.desktop_plan_widget.isVisible():
                self.main_window.desktop_plan_widget.hide()
            else:
                self.main_window.desktop_plan_widget.show()

    # 拖动
    def mousePressEvent(self, event):
        self.offset = event.pos()

    def mouseMoveEvent(self, event):
        self.move(self.pos() + event.pos() - self.offset)

    # 双击打开主窗口
    def mouseDoubleClickEvent(self, event):
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()

    # 右键菜单
    def contextMenuEvent(self, event):
        menu = QMenu()

        # 创建动作
        plan_action = QAction("Today's Plan")
        logout_action = QAction("Logout")
        quit_action = QAction("Exit")

        # 绑定动作
        plan_action.triggered.connect(self.show_today_plan)
        logout_action.triggered.connect(self.main_window.slide_to_login)
        quit_action.triggered.connect(lambda: exit())

        # 添加到菜单
        menu.addAction(plan_action)
        menu.addAction(logout_action)
        menu.addSeparator()
        menu.addAction(quit_action)

        # 在鼠标位置显示菜单
        menu.exec_(self.mapToGlobal(event.pos()))
