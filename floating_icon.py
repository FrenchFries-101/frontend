from PySide6.QtWidgets import QWidget, QLabel, QMenu
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QCursor, QAction, QMovie, QPainter
from utils.path_utils import resource_path
from service.api_petshow import get_current_skin
from service.api import BASE_URL
import requests
import tempfile
import os
import sys

if sys.platform == "win32":
    import ctypes
    _HWND_BOTTOM = 0x0001
    _SWP_NOSIZE = 0x0001
    _SWP_NOMOVE = 0x0002
    _SWP_NOACTIVATE = 0x0010


def _resolve_gif(gif_url: str, skin_id: int) -> str | None:
    """解析 GIF 路径：优先后端 URL，失败则回退本地 fox_{skin_id}.gif"""
    if gif_url and gif_url.startswith("/"):
        gif_url = f"{BASE_URL}{gif_url}"

    if gif_url and (gif_url.startswith("http://") or gif_url.startswith("https://")):
        try:
            res = requests.get(gif_url, timeout=10)
            res.raise_for_status()
            _, ext = os.path.splitext(gif_url)
            tmp = tempfile.NamedTemporaryFile(suffix=ext or ".gif", delete=False)
            tmp.write(res.content)
            tmp.close()
            return tmp.name
        except Exception as e:
            print(f"[FloatingIcon] 下载皮肤 GIF 失败: {e}")

    # 回退本地
    local = resource_path(f"resources/icons/fox_{skin_id}.gif")
    if os.path.exists(local):
        return local
    return None


class FloatingIcon(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        # 无边框 + 不显示在任务栏（不使用 WindowStaysOnBottomHint，Windows 下会导致 paintEvent 崩溃）
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)

        self.movie = None
        self._first_frame_loaded = False

    def _move_to_top_right(self):
        """将狐狸移动到屏幕右上角（留边距）"""
        screen = self.screen().availableGeometry()
        if self.movie and not self.movie.currentPixmap().isNull():
            w = self.movie.currentPixmap().width()
            h = self.movie.currentPixmap().height()
        else:
            w, h = 120, 120
        x = screen.right() - w - 20
        y = screen.top() + 20
        self.move(x, y)

    # ──── 登录 / 登出 ────

    def show_with_skin(self, user_id: int):
        """登录后调用：加载用户当前皮肤并显示（固定展示，不随机切换）"""
        skin_data = get_current_skin(user_id)
        gif_url = skin_data.get("gif_url", "")
        skin_id = skin_data.get("skin_id", 1)

        gif_path = _resolve_gif(gif_url, skin_id)
        if not gif_path:
            print("[FloatingIcon] 无法加载皮肤 GIF")
            return

        self._load_gif(gif_path)

    def hide_fox(self):
        """登出时调用：隐藏狐狸"""
        if self.movie:
            self.movie.stop()
        self.hide()

    # ──── GIF 加载 ────

    def _load_gif(self, path: str):
        if self.movie:
            self.movie.stop()
        self.hide()
        self._first_frame_loaded = False

        self.movie = QMovie(path)
        self.movie.frameChanged.connect(self.update)
        self.movie.frameChanged.connect(self._on_first_frame_loaded)
        self.movie.start()

    def _on_first_frame_loaded(self):
        if not self._first_frame_loaded:
            self._first_frame_loaded = True
            pixmap = self.movie.currentPixmap()
            if not pixmap.isNull():
                self.setFixedSize(pixmap.width(), pixmap.height())
            self._move_to_top_right()
            self.show()
            self._set_window_bottom()
            try:
                self.movie.frameChanged.disconnect(self._on_first_frame_loaded)
            except Exception:
                pass

    def _set_window_bottom(self):
        """Windows: 将窗口置底"""
        if sys.platform == "win32":
            try:
                hwnd = int(self.winId())
                ctypes.windll.user32.SetWindowPos(
                    hwnd, _HWND_BOTTOM, 0, 0, 0, 0,
                    _SWP_NOSIZE | _SWP_NOMOVE | _SWP_NOACTIVATE
                )
            except Exception:
                pass

    # ──── 绘制 ────

    def paintEvent(self, event):
        if not self.movie:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.fillRect(self.rect(), Qt.transparent)
        pixmap = self.movie.currentPixmap()
        if not pixmap.isNull():
            painter.drawPixmap(0, 0, pixmap)

    # ──── 交互 ────

    def show_today_plan(self):
        if hasattr(self.main_window, 'desktop_plan_widget'):
            if self.main_window.desktop_plan_widget.isVisible():
                self.main_window.desktop_plan_widget.hide()
            else:
                self.main_window.desktop_plan_widget.show()
                self.main_window.desktop_plan_widget.raise_()

    def mousePressEvent(self, event):
        self.offset = event.pos()

    def mouseMoveEvent(self, event):
        self.move(self.pos() + event.pos() - self.offset)

    def mouseDoubleClickEvent(self, event):
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()

    def contextMenuEvent(self, event):
        menu = QMenu()
        plan_action = QAction("Today's Plan")
        logout_action = QAction("Logout")
        quit_action = QAction("Exit")

        plan_action.triggered.connect(self.show_today_plan)
        logout_action.triggered.connect(self.main_window.slide_to_login)
        quit_action.triggered.connect(lambda: exit())

        menu.addAction(plan_action)
        menu.addAction(logout_action)
        menu.addSeparator()
        menu.addAction(quit_action)
        menu.exec_(self.mapToGlobal(event.pos()))
