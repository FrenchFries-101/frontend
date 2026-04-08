# components/restaurant_widget.py
# 美食推荐组件：筛选栏 + 推荐/刷新 + 结果展示

import os
import random
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QEvent
from PySide6.QtGui import QFont, QPixmap, QMovie

from service.api_restaurant import get_filters, get_recommend, get_refresh
from utils.path_utils import resource_path


# ─────────────────────────────────────────────
#  配色
# ─────────────────────────────────────────────
C_PRIMARY   = "#B3886B"
C_ACCENT    = "#E76F51"
C_BG        = "#FFF6EA"
C_CARD      = "white"
C_BORDER    = "#F0E0D0"
C_TEXT      = "#444444"
C_SUB       = "#999999"
C_TAG       = "#F5E6D3"

# ─────────────────────────────────────────────
#  随机趣味文案
# ─────────────────────────────────────────────
FUN_LINES = [
    "Perfect for a date with someone special \u2764",
    "Even eating alone deserves something good \u2728",
    "Treat yourself today, you deserve it \u2728",
    "Good food = good mood \u263a",
    "Regulars keep coming back for a reason \u2b50",
    "Tag your foodie buddy and go \ud83d\ude0b",
    "Diet starts tomorrow, eat up today \ud83d\ude05",
    "Nothing a good meal can't fix \ud83c\udf5c",
    "Savor life, one bite at a time \u2615",
    "Feeling lucky? This place won't disappoint \ud83c\udf1f",
    "Never skip a meal, always treat yourself well \ud83d\udc3e",
    "Go try it, might just become your new fav \u2764\ufe0f",
]


class FilterRow(QWidget):
    """一行筛选条件：icon + 标签 + 横排选项"""

    def __init__(self, icon_path: str, label: str, options: list, parent=None):
        super().__init__(parent)
        self.options = options
        self.selected_index = -1
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        icon_label = QLabel()
        icon_label.setFixedSize(18, 18)
        icon_label.setScaledContents(True)
        if os.path.exists(icon_path):
            icon_label.setPixmap(QPixmap(icon_path))
        icon_label.setStyleSheet("background: transparent;")
        layout.addWidget(icon_label)

        title = QLabel(label)
        title.setFixedWidth(36)
        title.setFont(QFont("", 10, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {C_PRIMARY}; background: transparent;")
        layout.addWidget(title)

        self._buttons = []
        for i, opt in enumerate(options):
            btn = QPushButton(opt.get("display", opt.get("label", "")))
            btn.setFixedHeight(26)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFont(QFont("", 9))
            btn.setStyleSheet(self._btn_style(False))
            btn.clicked.connect(lambda _, idx=i: self._select(idx))
            self._buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

    def _select(self, index: int):
        self.selected_index = index
        for i, btn in enumerate(self._buttons):
            btn.setStyleSheet(self._btn_style(i == index))

    def get_selected_value(self) -> str:
        if 0 <= self.selected_index < len(self.options):
            opt = self.options[self.selected_index]
            return opt.get("value", "") or opt.get("display", opt.get("label", ""))
        return ""

    def get_selected_display(self) -> str:
        """返回当前选中项的 display 文本"""
        if 0 <= self.selected_index < len(self.options):
            return self.options[self.selected_index].get("display", self.options[self.selected_index].get("label", ""))
        return ""

    def reset(self):
        self.selected_index = -1
        for btn in self._buttons:
            btn.setStyleSheet(self._btn_style(False))

    @staticmethod
    def _btn_style(active: bool) -> str:
        if active:
            return (f"QPushButton {{ background:{C_PRIMARY}; color:white; border:none; "
                    f"border-radius:13px; padding:0 12px; font-weight:bold; }}")
        return (f"QPushButton {{ background:{C_TAG}; color:{C_PRIMARY}; border:none; "
                f"border-radius:13px; padding:0 12px; }}"
                f"QPushButton:hover {{ background:#EDD9C4; }}")


class RestaurantWidget(QWidget):
    """美食推荐组件（紧凑布局）"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMinimumHeight(420)

        self._anim = None  # no longer used, kept for compat
        self._movie_food = None  # 标题 gif
        self._movie_broccoli = None  # 空状态 gif

        self._icon_loc   = resource_path("resources/icons/land-layer-location.png")
        self._icon_food  = resource_path("resources/icons/r_food.gif")
        self._icon_spice = resource_path("resources/icons/pepper.png")
        self._gif_broccoli = resource_path("resources/icons/r_Broccoli.gif")

        self._build_ui()
        self._load_filters()
        self._first_show = True

    def showEvent(self, event):
        super().showEvent(event)
        if self._first_show:
            self._first_show = False
            # ensure initial state labels are visible after parent layout settles
            QTimer.singleShot(0, self._ensure_initial_state)

    # ──── UI 构建 ────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(10)

        # 标题
        hdr = QHBoxLayout()
        hdr.setContentsMargins(0, 0, 0, 0)
        hdr.setSpacing(8)

        ico = QLabel()
        ico.setFixedSize(24, 24)
        ico.setStyleSheet("background:transparent;")
        if os.path.exists(self._icon_food):
            self._movie_food = QMovie(self._icon_food)
            self._movie_food.setScaledSize(ico.size())
            ico.setMovie(self._movie_food)
            self._movie_food.start()

        ttl = QLabel("Little Fox's Food Map")
        ttl.setFont(QFont("", 14, QFont.Weight.Bold))
        ttl.setStyleSheet(f"color:{C_PRIMARY}; background:transparent;")

        hdr.addWidget(ico)
        hdr.addWidget(ttl)
        hdr.addStretch()

        root.addLayout(hdr)

        # 筛选卡片
        self._filter_frame = QFrame()
        self._filter_frame.setObjectName("fc")
        self._filter_frame.setStyleSheet(
            f"QFrame#fc {{ background:{C_TAG}; border:none; border-radius:12px; }}")
        fl = QVBoxLayout(self._filter_frame)
        fl.setContentsMargins(16, 12, 16, 12)
        fl.setSpacing(8)

        self._filter_loc = self._filter_food = self._filter_spice = None
        self._loading = QLabel("Loading...")
        self._loading.setStyleSheet(f"color:{C_SUB}; background:transparent; font-size:10px;")
        fl.addWidget(self._loading)

        root.addWidget(self._filter_frame)

        # 按钮行
        brow = QHBoxLayout()
        brow.setSpacing(10)

        self._btn_rec = QPushButton("Recommend")
        self._btn_rec.setMinimumHeight(38)
        self._btn_rec.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_rec.setFont(QFont("", 11, QFont.Weight.Bold))
        self._btn_rec.setStyleSheet(self._abtn(C_PRIMARY, "#9E7658", "white"))
        self._btn_rec.clicked.connect(self._on_recommend)

        self._btn_ref = QPushButton("Refresh")
        self._btn_ref.setMinimumHeight(38)
        self._btn_ref.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_ref.setFont(QFont("", 11, QFont.Weight.Bold))
        self._btn_ref.setStyleSheet(self._abtn("white", "#FFF6EA", C_PRIMARY))
        self._btn_ref.clicked.connect(self._on_refresh)

        brow.addWidget(self._btn_rec)
        brow.addWidget(self._btn_ref)
        root.addLayout(brow)

        # 结果卡片
        self._result_frame = QFrame()
        self._result_frame.setObjectName("rc")
        self._result_frame.setStyleSheet(
            f"QFrame#rc {{ background:{C_TAG}; border:none; border-radius:12px; }}")
        self._result_frame.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        self._result_frame.setMinimumHeight(180)  # ✅ 保底高度
        rl = QVBoxLayout(self._result_frame)
        rl.setContentsMargins(14, 8, 14, 8)
        rl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._r_broccoli = QLabel()
        self._r_broccoli.setFixedSize(64, 64)
        self._r_broccoli.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._r_broccoli.setStyleSheet("background:transparent;")
        if os.path.exists(self._gif_broccoli):
            self._movie_broccoli = QMovie(self._gif_broccoli)
            self._movie_broccoli.setScaledSize(self._r_broccoli.size())
            self._r_broccoli.setMovie(self._movie_broccoli)
            self._movie_broccoli.start()

        self._r_name = QLabel("Waiting for recommendation...")
        self._r_name.setFont(QFont("", 13, QFont.Weight.Bold))
        self._r_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._r_name.setStyleSheet(f"color:{C_TEXT}; background:transparent;")
        self._r_name.setWordWrap(True)

        self._r_detail = QLabel("Waiting for your choice")
        self._r_detail.setFont(QFont("", 10))
        self._r_detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._r_detail.setStyleSheet(f"color:{C_SUB}; background:transparent;")

        self._r_fun = QLabel("")
        self._r_fun.setFont(QFont("", 10))
        self._r_fun.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._r_fun.setStyleSheet(f"color:{C_ACCENT}; background:transparent;")

        rl.addWidget(self._r_broccoli)
        rl.addWidget(self._r_name)
        rl.addWidget(self._r_detail)
        rl.addWidget(self._r_fun)

        root.addWidget(self._result_frame, stretch=1)

    # ──── 数据 ────

    def _load_filters(self):
        data = get_filters()
        locs, cuis, spis = data.get("locations", []), data.get("cuisines", []), data.get("spice_levels", [])
        if not locs and not cuis:
            if self._loading and not self._loading.isHidden():
                self._loading.setText("Failed to load, please try again")
            return

        # 首次加载时删除 "加载中..." 占位标签
        if self._loading is not None:
            self._loading.deleteLater()
            self._loading = None

        pl = self._filter_frame.layout()
        # 清理旧的筛选行（refresh 时重建）
        while pl.count():
            item = pl.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._filter_loc   = FilterRow(self._icon_loc,   "Area", locs)
        self._filter_food  = FilterRow(self._icon_food,  "Type", cuis)
        self._filter_spice = FilterRow(self._icon_spice, "Spice", spis)
        pl.addWidget(self._filter_loc)
        pl.addWidget(self._filter_food)
        pl.addWidget(self._filter_spice)

    # ──── 按钮 ────

    def _cur_filters(self):
        l = self._filter_loc.get_selected_value()   if self._filter_loc   else ""
        f = self._filter_food.get_selected_value()  if self._filter_food  else ""
        s = self._filter_spice.get_selected_value() if self._filter_spice else ""
        return l or None, f or None, s or None

    def _on_recommend(self):
        filters = self._cur_filters()
        print(f"[Restaurant] recommend with filters: {filters}")
        self._show_result(get_recommend(*filters))

    def _on_refresh(self):
        filters = self._cur_filters()
        print(f"[Restaurant] refresh with filters: {filters}")
        self._show_result(get_refresh(*filters))

    # ──── 结果展示（淡入淡出，引用防 GC） ────

    def _show_result(self, data: dict):
        self._r_broccoli.hide()
        if not data or "name" not in data:
            self._r_broccoli.show()
            # 检查是否是错误响应
            if data.get("error"):
                self._r_name.setText("No Results Found")
                self._r_detail.setText(data.get("message", "Try different filters"))
                self._r_fun.setText("")
            else:
                self._r_name.setText("Waiting for recommendation...")
                self._r_detail.setText("Waiting for your choice")
                self._r_fun.setText("")
            return

        # detail 展示 API 返回的餐厅属性
        parts = [x for x in (data.get("location", ""), data.get("cuisine", ""), data.get("spice_level", "")) if x]
        detail = "  \u00b7  ".join(parts) if parts else ""
        fun = random.choice(FUN_LINES)

        # 先淡出文字，再更新，再淡入
        self._r_name.setStyleSheet(f"color:{C_TEXT}; background:transparent; opacity:0;")
        self._r_detail.setStyleSheet(f"color:{C_SUB}; background:transparent; opacity:0;")
        self._r_fun.setStyleSheet(f"color:{C_ACCENT}; background:transparent; opacity:0;")

        QTimer.singleShot(120, lambda: self._apply_result(name=data["name"], detail=detail, fun=fun))

    def _apply_result(self, name: str, detail: str, fun: str):
        self._r_name.setText(name)
        self._r_detail.setText(detail)
        self._r_fun.setText(fun)
        # 淡入
        self._r_name.setStyleSheet(f"color:{C_TEXT}; background:transparent;")
        self._r_detail.setStyleSheet(f"color:{C_SUB}; background:transparent;")
        self._r_fun.setStyleSheet(f"color:{C_ACCENT}; background:transparent;")

    def _selected_display(self, row: 'FilterRow') -> str:
        """获取用户选中的筛选条件的显示文本"""
        if row and row.selected_index >= 0:
            return row.get_selected_display()
        return ""

    def _label_of(self, row: FilterRow, value: str) -> str:
        if not row or not value:
            return ""
        for o in row.options:
            if o.get("value") == value:
                return o.get("display", o.get("label", value))
        return value

    # ──── 样式 ────

    @staticmethod
    def _abtn(bg, hover, text) -> str:
        bc = bg if bg != "white" else C_BORDER
        return (f"QPushButton {{ background:{bg}; color:{text}; border:1px solid {bc}; "
                f"border-radius:19px; padding:4px 20px; }}"
                f"QPushButton:hover {{ background:{hover}; }}"
                f"QPushButton:pressed {{ background:{C_ACCENT}; color:white; }}")

    def _ensure_initial_state(self):
        """确保初始占位界面可见"""
        if self._r_broccoli.isHidden():
            self._r_broccoli.show()
        self._r_name.setText("Waiting for recommendation...")
        self._r_detail.setText("Waiting for your choice")
        self._r_fun.setText("")
        self._r_name.setStyleSheet(f"color:{C_TEXT}; background:transparent;")
        self._r_detail.setStyleSheet(f"color:{C_SUB}; background:transparent;")
        self._r_fun.setStyleSheet(f"color:{C_ACCENT}; background:transparent;")
        self._result_frame.setMinimumHeight(180)

    def refresh(self):
        self._load_filters()
        self._r_broccoli.show()
        self._r_name.setText("Waiting for recommendation...")
        self._r_detail.setText("Waiting for your choice")
        self._r_fun.setText("")


# ──── 测试入口 ────

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)
    w = QMainWindow()
    w.setWindowTitle("美食推荐 测试")
    w.resize(480, 520)
    w.setStyleSheet(f"background-color:{C_BG};")
    w.setCentralWidget(RestaurantWidget())
    w.show()
    sys.exit(app.exec())
