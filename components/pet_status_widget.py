#最新
# pet_status_widget.py
# 宠物状态组件：等级、经验条、活力条、经验增长速率

from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QSizePolicy
from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import QFont, QPainter, QLinearGradient, QColor, QPainterPath, QBrush, QPen

import requests

BASE_URL = "http://127.0.0.1:8000/pet_module"

#


def get_pet_status(user_id: int) -> dict:
    """
    GET /pet/status?user_id={user_id}
    把后端字段名映射成前端组件需要的字段名
    """
    try:
        response = requests.get(
            f"{BASE_URL}/pet/status",
            params={"user_id": user_id}   # query参数用params=
        )
        raw = response.json()
        # 后端原始数据

        # 字段名转换 + 字符串转数字
        return {
            "level":        int(raw.get("level", 1)),
            "exp":          float(raw.get("exp", 0)),
            "exp_max":      int(raw.get("exp_required", 100)),
            "vitality":     float(raw.get("vitality", 100)),
            "vitality_max": 100,
            "exp_rate":     float(raw.get("exp_rate", 1.0)),
        }

    except Exception as e:
        print(f"[get_pet_status] 请求失败: {e}")
        return {                           # 后端挂了时的保底默认值
            "level": 1,
            "exp": 0,
            "exp_max": 100,
            "vitality": 100,
            "vitality_max": 100,
            "exp_rate": 1.0,
        }

# ─────────────────────────────────────────────
#  ② 自定义圆角渐变进度条
# ─────────────────────────────────────────────

class RoundedProgressBar(QWidget):
    """
    圆角渐变进度条，支持自定义颜色和动画过渡。
    参数:
        color_start  渐变起始色（左）
        color_end    渐变结束色（右）
        bg_color     轨道背景色
        height       控件高度（px）
    """

    def __init__(
        self,
        color_start: str = "#F4A261",
        color_end: str   = "#E76F51",
        bg_color: str    = "#EDE0D4",
        bar_height: int  = 14,
        parent=None,
    ):
        super().__init__(parent)
        self._value    = 0      # 当前值 0~100（百分比）
        self._displayed = 0.0   # 动画中间值
        self._color_start = QColor(color_start)
        self._color_end   = QColor(color_end)
        self._bg_color    = QColor(bg_color)

        self.setFixedHeight(bar_height + 4)   # 留出 2px 上下留白
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # 平滑动画计时器
        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(16)       # ~60 fps
        self._anim_timer.timeout.connect(self._tick_animation)

    # ── 公开 API ──────────────────────────────

    def set_value(self, value: int, maximum: int = 100):
        """设置进度值，支持任意最大值"""
        if maximum <= 0:
            maximum = 1
        percent = max(0, min(100, int(value / maximum * 100)))
        self._value = percent
        self._anim_timer.start()

    # ── 动画 ─────────────────────────────────

    def _tick_animation(self):
        diff = self._value - self._displayed
        if abs(diff) < 0.5:
            self._displayed = float(self._value)
            self._anim_timer.stop()
        else:
            self._displayed += diff * 0.12    # 缓动系数
        self.update()

    # ── 绘制 ─────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        bar_h  = h - 4
        bar_y  = 2
        radius = bar_h / 2

        # 1. 轨道背景
        bg_rect = QRectF(0, bar_y, w, bar_h)
        path_bg = QPainterPath()
        path_bg.addRoundedRect(bg_rect, radius, radius)
        painter.fillPath(path_bg, QBrush(self._bg_color))

        # 2. 填充部分
        fill_w = max(bar_h, w * self._displayed / 100)   # 最小宽度 = 直径，避免方形
        fill_rect = QRectF(0, bar_y, fill_w, bar_h)
        path_fill = QPainterPath()
        path_fill.addRoundedRect(fill_rect, radius, radius)

        gradient = QLinearGradient(0, 0, fill_w, 0)
        gradient.setColorAt(0.0, self._color_start)
        gradient.setColorAt(1.0, self._color_end)
        painter.fillPath(path_fill, QBrush(gradient))

        painter.end()


# ─────────────────────────────────────────────
#  ③ 主组件
# ─────────────────────────────────────────────

class PetStatusWidget(QWidget):
    """
    宠物状态面板：等级、经验条、活力条、经验增长速率。
    用法：
        status_widget = PetStatusWidget(user_id=1, parent=some_parent)
    """

    # 主色系（与 pet_current_widget.py 保持一致）
    COLOR_PRIMARY   = "#B3886B"
    COLOR_BG_PANEL  = "rgba(255,246,234,200)"

    # 经验条配色：暖橙渐变
    EXP_START  = "#F4A261"
    EXP_END    = "#E76F51"
    # 活力条配色：薄荷绿渐变
    VIT_START  = "#74C69D"
    VIT_END    = "#40916C"
    # 进度条轨道
    BAR_BG     = "#EDE0D4"

    def __init__(self, user_id: int, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(16, 12, 16, 12)
        self._main_layout.setSpacing(10)

        self._create_level_row()
        self._create_exp_row()
        self._create_vitality_row()

        # 初始化数据
        self.load_status()

    # ─────────────────────────────────────────
    #  子组件构建
    # ─────────────────────────────────────────

    def _create_level_row(self):
        """等级 + 经验增长速率"""
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)

        # 等级标签
        self.level_label = QLabel("Lv. --")
        self.level_label.setFont(QFont("", 15, QFont.Weight.Bold))
        self.level_label.setStyleSheet(f"color: {self.COLOR_PRIMARY}; background: transparent;")

        # 经验增长速率标签
        self.rate_label = QLabel("⚡ EXP Rate  ×--")
        self.rate_label.setFont(QFont("", 10))
        self.rate_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.rate_label.setStyleSheet("color: #E76F51; background: transparent;")

        row.addWidget(self.level_label)
        row.addStretch()
        row.addWidget(self.rate_label)

        row_widget = QWidget()
        row_widget.setLayout(row)
        row_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._main_layout.addWidget(row_widget)

    def _create_exp_row(self):
        """经验条"""
        self._main_layout.addWidget(self._make_bar_label("EXP"))
        self.exp_bar = RoundedProgressBar(
            color_start=self.EXP_START,
            color_end=self.EXP_END,
            bg_color=self.BAR_BG,
            bar_height=14,
        )
        self.exp_value_label = QLabel("0 / 0")
        self._main_layout.addWidget(self._wrap_bar_with_value(self.exp_bar, self.exp_value_label))

    def _create_vitality_row(self):
        """活力条"""
        self._main_layout.addWidget(self._make_bar_label("Vitality"))
        self.vit_bar = RoundedProgressBar(
            color_start=self.VIT_START,
            color_end=self.VIT_END,
            bg_color=self.BAR_BG,
            bar_height=14,
        )
        self.vit_value_label = QLabel("0 / 0")
        self._main_layout.addWidget(self._wrap_bar_with_value(self.vit_bar, self.vit_value_label))

    # ─────────────────────────────────────────
    #  辅助构建方法
    # ─────────────────────────────────────────

    def _make_bar_label(self, text: str) -> QLabel:
        """进度条上方小标题"""
        lbl = QLabel(text)
        lbl.setFont(QFont("", 9))
        lbl.setStyleSheet(f"color: {self.COLOR_PRIMARY}; background: transparent;")
        return lbl

    def _wrap_bar_with_value(
        self,
        bar: RoundedProgressBar,
        value_label: QLabel,
    ) -> QWidget:
        """将进度条和数值标签横向组合"""
        value_label.setFixedWidth(72)
        value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        value_label.setFont(QFont("", 9))
        value_label.setStyleSheet("color: #888888; background: transparent;")

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        row.addWidget(bar)
        row.addWidget(value_label)

        wrapper = QWidget()
        wrapper.setLayout(row)
        wrapper.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        return wrapper

    # ─────────────────────────────────────────
    #  数据加载
    # ─────────────────────────────────────────

    def load_status(self):
        """拉取并渲染宠物状态数据"""
        data = get_pet_status(self.user_id)

        level    = data.get("level", 1)
        exp      = data.get("exp", 0)
        exp_max  = data.get("exp_max", 100)
        vit      = data.get("vitality", 100)
        vit_max  = data.get("vitality_max", 100)
        rate     = data.get("exp_rate", 1.0)

        # 更新等级
        self.level_label.setText(f"Lv. {level}")

        # 更新速率（高于1倍时用高亮色，否则用灰色）
        rate_color = "#E76F51" if rate > 1.0 else "#AAAAAA"
        self.rate_label.setStyleSheet(f"color: {rate_color}; background: transparent;")
        self.rate_label.setText(f"⚡ EXP Rate  ×{rate:.1f}")

        # 更新经验条
        self.exp_bar.set_value(exp, exp_max)
        self.exp_value_label.setText(f"{exp} / {exp_max}")

        # 更新活力条
        self.vit_bar.set_value(vit, vit_max)
        self.vit_value_label.setText(f"{vit} / {vit_max}")

    def refresh(self):
        """外部调用：手动刷新数据（如答题后经验变化）"""
        self.load_status()


# ─────────────────────────────────────────────
#  ④ 本地测试入口
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget

    app = QApplication(sys.argv)

    window = QMainWindow()
    window.setWindowTitle("PetStatusWidget Demo")
    window.resize(360, 220)
    window.setStyleSheet("background-color: #FFF6EA;")

    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    status_widget = PetStatusWidget(user_id=1)
    layout.addWidget(status_widget)

    window.setCentralWidget(container)
    window.show()
    sys.exit(app.exec())
