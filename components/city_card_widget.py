# components/city_card_widget.py
# 城市卡片组件：天气卡片（左）+ 景点卡片（右），用 QSplitter 支持拉缩

import os
import html
import tempfile
import requests as http_req

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QSizePolicy, QGraphicsDropShadowEffect,
    QPushButton, QSplitter
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QFont, QPixmap, QMovie, QDesktopServices

from service.api import BASE_URL
from service.api_city import get_weather, get_sights


def _full_url(path: str) -> str:
    if not path:
        return ""
    path = path.lstrip("/")
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return f"{BASE_URL}/{path}"


def _download_to_tmp(url: str, suffix: str = ".gif") -> str | None:
    try:
        r = http_req.get(url, timeout=8)
        r.raise_for_status()
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.write(r.content)
        tmp.close()
        return tmp.name
    except Exception as e:
        print(f"[CityCard] 下载失败 {url}: {e}")
        return None


# ─────────────────────────────────────────────
#  配色（统一暖色系，与整体风格一致）
# ─────────────────────────────────────────────
C_PRIMARY    = "#B3886B"
C_ACCENT     = "#E76F51"
C_BG         = "#FFF6EA"
C_CARD       = "white"
C_TEXT       = "#444444"
C_SUB        = "#999999"
C_WEATHER_BG = "#FFF8F2"
C_SIGHT_BG   = "#FFFAF6"
C_TAG        = "#F5E6D3"


def _month_name(month_val) -> str:
    """将月份数字（int/str）转为完整英文名"""
    months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    try:
        idx = int(month_val) - 1
        if 0 <= idx < 12:
            return months[idx]
    except (ValueError, TypeError):
        pass
    return str(month_val)


class WeatherCard(QFrame):
    """左侧天气卡片：标题 + 天气图标 + 月份 + 描述"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("weatherCard")
        self.setStyleSheet(
            f"QFrame#weatherCard {{ background:{C_WEATHER_BG}; border:none; "
            f"border-radius:14px; }}"
        )
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        # ── 标题 ──
        hdr = QHBoxLayout()
        hdr.setContentsMargins(0, 0, 0, 0)
        ttl = QLabel("Weather")
        ttl.setFont(QFont("", 13, QFont.Weight.Bold))
        ttl.setStyleSheet(f"color:{C_PRIMARY}; background:transparent;")
        hdr.addWidget(ttl)
        hdr.addStretch()
        layout.addLayout(hdr)

        # ── 内容区 ──
        content = QVBoxLayout()
        content.setSpacing(8)
        content.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._weather_icon = QLabel()
        self._weather_icon.setFixedSize(100, 100)
        self._weather_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._weather_icon.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._weather_icon.setStyleSheet("background:transparent; border:none;")
        content.addWidget(self._weather_icon, alignment=Qt.AlignmentFlag.AlignCenter)

        self._month_label = QLabel()
        self._month_label.setFont(QFont("", 10, QFont.Weight.Bold))
        self._month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._month_label.setStyleSheet(f"color:{C_PRIMARY}; background:transparent;")
        content.addWidget(self._month_label)

        self._desc_label = QLabel()
        self._desc_label.setFont(QFont("", 9))
        self._desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._desc_label.setWordWrap(True)
        self._desc_label.setStyleSheet(f"color:{C_TEXT}; background:transparent;")
        content.addWidget(self._desc_label)

        layout.addLayout(content)
        layout.addStretch()

        self._movies = []

    def load_data(self, data: dict):
        month = str(data.get("month", ""))
        desc = data.get("description", "")
        icon_url = data.get("icon_url", "") or data.get("icon", "")

        self._month_label.setText(_month_name(month))
        self._desc_label.setText(desc)

        for item in self._movies:
            if isinstance(item, tuple):
                item[0].stop()
                try:
                    os.unlink(item[1])
                except OSError:
                    pass
        self._movies.clear()

        if icon_url:
            full = _full_url(icon_url)
            suffix = ".gif" if ".gif" in icon_url.lower() else ".png"
            tmp_path = _download_to_tmp(full, suffix=suffix)
            if tmp_path:
                if suffix == ".gif":
                    movie = QMovie(tmp_path)
                    movie.setScaledSize(self._weather_icon.size())
                    self._weather_icon.setMovie(movie)
                    movie.start()
                    self._movies.append((movie, tmp_path))
                else:
                    pixmap = QPixmap(tmp_path)
                    if not pixmap.isNull():
                        pixmap = pixmap.scaled(
                            self._weather_icon.size(),
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        )
                        self._weather_icon.setPixmap(pixmap)
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass
            else:
                self._weather_icon.clear()
                self._weather_icon.setText("\u2601")
        else:
            self._weather_icon.clear()
            self._weather_icon.setText("\u2601")


class SightCard(QFrame):
    """右侧景点卡片：标题 + 左图右文"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sightCard")
        self.setStyleSheet(
            f"QFrame#sightCard {{ background:{C_SIGHT_BG}; border:none; "
            f"border-radius:14px; }}"
        )
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 12, 14, 12)
        outer.setSpacing(8)

        # ── 标题栏（固定最小高度，防止 QSplitter 压缩） ──
        hdr_widget = QWidget()
        hdr_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        hdr_widget.setMinimumHeight(32)
        hdr_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        hdr = QHBoxLayout(hdr_widget)
        hdr.setContentsMargins(0, 0, 0, 0)
        hdr.setSpacing(8)
        ttl = QLabel("Sightseeing")
        ttl.setFont(QFont("", 13, QFont.Weight.Bold))
        ttl.setStyleSheet(f"color:{C_PRIMARY}; background:transparent;")
        hdr.addWidget(ttl)
        hdr.addStretch()

        self._sight_idx_label = QLabel("1/1")
        self._sight_idx_label.setFont(QFont("", 9))
        self._sight_idx_label.setStyleSheet(f"color:{C_SUB}; background:transparent;")
        hdr.addWidget(self._sight_idx_label)

        self._btn_next = QPushButton("\u25b6")
        self._btn_next.setFixedSize(28, 28)
        self._btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_next.setFont(QFont("", 10))
        self._btn_next.setStyleSheet(
            f"QPushButton {{ background:{C_TAG}; color:{C_PRIMARY}; border:none; border-radius:14px; }}"
            f"QPushButton:hover {{ background:#EDD9C4; }}"
        )
        hdr.addWidget(self._btn_next)

        outer.addWidget(hdr_widget)

        # ── 左图右文 ──
        body_splitter = QSplitter(Qt.Orientation.Horizontal)
        body_splitter.setHandleWidth(2)
        body_splitter.setStyleSheet(
            f"QSplitter::handle {{ background:transparent; width:2px; }}"
        )

        img_wrapper = QWidget()
        img_layout = QVBoxLayout(img_wrapper)
        img_layout.setContentsMargins(0, 0, 4, 0)
        img_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sight_image = QLabel()
        self._sight_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sight_image.setStyleSheet("background:transparent; border:none;")
        self._sight_image.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        img_layout.addWidget(self._sight_image)

        right_widget = QWidget()
        right = QVBoxLayout(right_widget)
        right.setContentsMargins(8, 4, 4, 4)
        right.setSpacing(10)

        self._sight_name = QLabel()
        self._sight_name.setFont(QFont("", 11, QFont.Weight.Bold))
        self._sight_name.setWordWrap(True)
        self._sight_name.setStyleSheet(f"color:{C_TEXT}; background:transparent;")
        right.addWidget(self._sight_name)

        self._sight_desc = QLabel()
        self._sight_desc.setFont(QFont("", 9))
        self._sight_desc.setWordWrap(True)
        self._sight_desc.setStyleSheet(f"color:{C_SUB}; background:transparent;")
        right.addWidget(self._sight_desc)

        right.addStretch()

        self._sight_copyright = QLabel()
        self._sight_copyright.setWordWrap(True)
        self._sight_copyright.setStyleSheet(
            f"color:#ccc; background:transparent; font-size:7px;"
        )
        self._sight_copyright.linkActivated.connect(self._open_link)
        right.addWidget(self._sight_copyright)

        right_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        right_widget.setStyleSheet("background:transparent;")

        body_splitter.addWidget(img_wrapper)
        body_splitter.addWidget(right_widget)
        body_splitter.setStretchFactor(0, 1)
        body_splitter.setStretchFactor(1, 1)
        body_splitter.setSizes([200, 200])

        outer.addWidget(body_splitter, stretch=1)

        self._sight_image_tmp = None

    def set_index_label(self, idx: int, total: int):
        self._sight_idx_label.setText(f"{idx + 1}/{total}")

    def load_sight(self, sight: dict):
        title = sight.get("title", "")
        desc = sight.get("description", "")
        image = sight.get("image_url", "") or sight.get("image", "")
        copyright_text = sight.get("copyright", "")

        self._sight_name.setText(title)
        self._sight_desc.setText(desc)

        if self._sight_image_tmp:
            try:
                os.unlink(self._sight_image_tmp)
            except OSError:
                pass
            self._sight_image_tmp = None

        self._sight_image.clear()
        self._sight_image.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        if image:
            full_img = _full_url(image)
            tmp_path = _download_to_tmp(full_img, suffix=".png")
            if tmp_path:
                pixmap = QPixmap(tmp_path)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(
                        280, 200,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self._sight_image.setPixmap(pixmap)
                    self._sight_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    self._sight_image_tmp = tmp_path
                else:
                    self._sight_image.setText("Failed to load")
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass
            else:
                self._sight_image.setText("Image not found")
        else:
            self._sight_image.setText("No image")

        if copyright_text:
            if "http" in copyright_text:
                display = html.escape(copyright_text)
                self._sight_copyright.setText(
                    f'<a href="{copyright_text}" style="color:#ccc; font-size:5px;">{display}</a>'
                )
            else:
                self._sight_copyright.setText(copyright_text)
        else:
            self._sight_copyright.clear()

    def _open_link(self, url: str):
        QDesktopServices.openUrl(QUrl(url))


class CityCardWidget(QWidget):
    """城市卡片组件：天气（左）+ 景点（右），QSplitter 可拖拽调整宽度比例"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._sights_data = []
        self._current_sight_idx = 0

        self._build_ui()
        self._load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(4)
        splitter.setStyleSheet(
            f"QSplitter::handle {{ background:transparent; width:4px; }}"
        )

        self._weather_card = WeatherCard()
        self._sight_card = SightCard()
        self._sight_card._btn_next.clicked.connect(self.next_sight)

        splitter.addWidget(self._weather_card)
        splitter.addWidget(self._sight_card)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([200, 400])

        layout.addWidget(splitter)

    def _load_data(self):
        weather = get_weather()
        self._weather_card.load_data(weather)

        self._sights_data = get_sights()
        if self._sights_data:
            self._current_sight_idx = 0
            self._sight_card.load_sight(self._sights_data[0])
            self._sight_card.set_index_label(0, len(self._sights_data))

    def next_sight(self):
        if not self._sights_data:
            return
        self._current_sight_idx = (self._current_sight_idx + 1) % len(self._sights_data)
        self._sight_card.load_sight(self._sights_data[self._current_sight_idx])
        self._sight_card.set_index_label(self._current_sight_idx, len(self._sights_data))

    def refresh(self):
        self._load_data()
        self._current_sight_idx = 0


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)
    w = QMainWindow()
    w.setWindowTitle("City Card Test")
    w.resize(560, 260)
    w.setStyleSheet(f"background-color:{C_BG};")
    w.setCentralWidget(CityCardWidget())
    w.show()
    sys.exit(app.exec())
