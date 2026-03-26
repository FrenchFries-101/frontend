from PySide6.QtWidgets import QWidget, QLabel, QMenu
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QCursor,QAction,QMovie


class FloatingIcon(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        self.setFixedSize(1136, 810)
        # 无边框 + 置顶 + 不显示在任务栏
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 显示 GIF
        self.label = QLabel(self)
        self.label.setFixedSize(1136, 810)
        self.label.setAlignment(Qt.AlignCenter)
        self.movie = QMovie("resources/icons/tuoniao.gif")
        self.movie.setScaledSize(self.label.size())
        self.label.setMovie(self.movie)
        self.movie.start()

        self.show()

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