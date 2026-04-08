from PySide6.QtWidgets import QWidget, QMenu
from PySide6.QtCore import Qt, QPoint, QTimer, QDate
from PySide6.QtGui import QCursor, QAction, QMovie, QPainter, QPixmap
import random


class FloatingIcon(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        # 窗口大小设置为 GIF 大小
        self.setFixedSize(80, 80)
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
        self.movie.start()
        
        # 定时器，每隔一段时间随机切换 fox gif
        self.switch_timer = QTimer()
        self.switch_timer.timeout.connect(self.switch_fox_gif)
        # 随机设置切换时间（10-30秒）
        self.switch_interval = random.randint(10000, 30000)
        self.switch_timer.start(self.switch_interval)

        self.show()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.transparent)

        pixmap = self.movie.currentPixmap()
        if not pixmap.isNull():
            # 直接绘制，不做任何额外处理
            painter.drawPixmap(
                (self.width() - pixmap.width())//2,
                (self.height() - pixmap.height())//2,
                pixmap
            )
    
    def switch_fox_gif(self):
        # 随机选择一个新的 fox gif（避免选择同一个）
        new_index = random.randint(0, len(self.fox_gifs) - 1)
        while new_index == self.current_gif_index and len(self.fox_gifs) > 1:
            new_index = random.randint(0, len(self.fox_gifs) - 1)
        
        self.current_gif_index = new_index
        
        # 停止当前动画
        self.movie.stop()
        
        # 加载新的 gif
        self.movie = QMovie(self.fox_gifs[self.current_gif_index])
        self.movie.frameChanged.connect(self.update)
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
