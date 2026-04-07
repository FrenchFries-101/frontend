from PySide6.QtWidgets import QWidget, QLabel, QMenu
from PySide6.QtCore import Qt, QPoint, QTimer
from PySide6.QtGui import QCursor, QAction, QMovie
import random


class FloatingIcon(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        self.setFixedSize(80, 80)
        # 无边框 + 置顶 + 不显示在任务栏
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 显示 GIF
        self.label = QLabel(self)
        self.label.setFixedSize(80, 80)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("border: none; background: transparent;")
        
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
        self.movie.setScaledSize(self.label.size())
        self.label.setMovie(self.movie)
        self.movie.start()
        
        # 定时器，每隔一段时间随机切换 fox gif
        self.switch_timer = QTimer()
        self.switch_timer.timeout.connect(self.switch_fox_gif)
        # 随机设置切换时间（10-30秒）
        self.switch_interval = random.randint(10000, 30000)
        self.switch_timer.start(self.switch_interval)

        self.show()
    
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
        self.movie.setScaledSize(self.label.size())
        self.label.setMovie(self.movie)
        self.movie.start()
        
        # 随机设置下一次切换时间（10-30秒）
        self.switch_interval = random.randint(10000, 30000)
        self.switch_timer.setInterval(self.switch_interval)

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
        test_action = QAction("Hello")
        logout_action = QAction("Logout")
        quit_action = QAction("Exit")

        # 绑定动作
        test_action.triggered.connect(lambda: self.main_window.stack.setCurrentIndex(1))
        logout_action.triggered.connect(self.main_window.slide_to_login)
        quit_action.triggered.connect(lambda: exit())

        # 添加到菜单
        menu.addAction(test_action)
        menu.addAction(logout_action)
        menu.addSeparator()
        menu.addAction(quit_action)

        # 在鼠标位置显示菜单
        menu.exec_(self.mapToGlobal(event.pos()))
