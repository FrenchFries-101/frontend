from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QFrame,
    QPushButton, QGridLayout, QTextEdit, QDialog, QSizePolicy, QStackedWidget
)
from PySide6.QtCore import Qt, QDate, QPoint
from PySide6.QtGui import QFont
import json
import os


# ── 共享配色（与 Plan widget 一致） ──
C_BG       = "rgba(255, 243, 232, 230)"
C_ACCENT   = "rgba(242, 141, 64, 0.3)"
C_ACCENT_H = "rgba(242, 141, 64, 0.6)"
C_TEXT     = "#333333"
C_SUB      = "#666666"
C_BORDER   = "rgba(242, 141, 64, 0.3)"
C_RADIUS   = 15

TASK_FILE = os.path.join(os.path.expanduser("~"), ".desktop_calendar_tasks.json")
COMPLETED_FILE = os.path.join(os.path.expanduser("~"), ".desktop_completed_tasks.json")

DEFAULT_TASKS = [
    "Memorize vocabulary",
    "Listen to audio materials",
    "Practice speaking",
    "Read English articles",
    "Review grammar",
]


# ══════════════════════════════════════
#  主弹窗：Tab 切换 Plan / Calendar
# ══════════════════════════════════════

class DesktopPlanWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.setFixedSize(310, 460)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.set_window_position()
        self._build_ui()

    def set_window_position(self):
        from PySide6.QtGui import QScreen
        screen = QScreen.availableGeometry(self.screen())
        x = screen.width() - self.width() - 100
        y = screen.height() - self.height() - 100
        self.move(x, y)

    # ──── UI ────

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background: {C_BG};
                border-radius: {C_RADIUS}px;
                border: none;
            }}
        """)
        main_layout = QVBoxLayout(frame)
        main_layout.setSpacing(6)
        main_layout.setContentsMargins(12, 12, 12, 12)

        # ── 标题栏 ──
        title_bar = QHBoxLayout()
        title = QLabel("My Schedule")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet(f"color: {C_TEXT}; border: none; background: transparent;")
        title.setAlignment(Qt.AlignCenter)
        title_bar.addWidget(title)
        title_bar.addStretch()

        close_btn = QPushButton("\u00d7")
        close_btn.setFixedSize(25, 25)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C_ACCENT}; border: none; border-radius: 12px;
                color: {C_TEXT}; font-size: 18px; font-weight: bold;
            }}
            QPushButton:hover {{ background: {C_ACCENT_H}; }}
        """)
        close_btn.clicked.connect(self.hide)
        title_bar.addWidget(close_btn)
        main_layout.addLayout(title_bar)

        # ── Tab 按钮栏 ──
        tab_bar = QHBoxLayout()
        tab_bar.setSpacing(6)

        self._tab_plan_btn = QPushButton("Today's Plan")
        self._tab_cal_btn = QPushButton("Calendar")
        for btn in (self._tab_plan_btn, self._tab_cal_btn):
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFont(QFont("Arial", 10, QFont.Bold))
            btn.setFixedHeight(30)
        self._tab_plan_btn.clicked.connect(lambda: self._switch_tab(0))
        self._tab_cal_btn.clicked.connect(lambda: self._switch_tab(1))
        tab_bar.addWidget(self._tab_plan_btn)
        tab_bar.addWidget(self._tab_cal_btn)
        main_layout.addLayout(tab_bar)

        # ── 分隔线 ──
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background: {C_BORDER}; border: none; max-height: 2px;")
        main_layout.addWidget(sep)

        # ── Stacked 内容 ──
        self._stack = QStackedWidget()
        self._plan_page = _PlanPage()
        self._cal_page = _CalendarPage()
        self._stack.addWidget(self._plan_page)
        self._stack.addWidget(self._cal_page)
        main_layout.addWidget(self._stack, stretch=1)

        outer.addWidget(frame)
        self._switch_tab(0)  # 默认 Plan

    def _switch_tab(self, index: int):
        self._stack.setCurrentIndex(index)
        if index == 0:
            self._plan_page.refresh()
        else:
            self._cal_page.refresh()
        active_ss = f"""
            QPushButton {{
                background: {C_ACCENT_H}; color: {C_TEXT};
                border: none; border-radius: 15px; padding: 0 14px;
            }}
        """
        inactive_ss = f"""
            QPushButton {{
                background: transparent; color: {C_SUB};
                border: none; border-radius: 15px; padding: 0 14px;
            }}
            QPushButton:hover {{ background: {C_ACCENT}; }}
        """
        btns = [self._tab_plan_btn, self._tab_cal_btn]
        for i, btn in enumerate(btns):
            btn.setStyleSheet(active_ss if i == index else inactive_ss)

    def showEvent(self, event):
        super().showEvent(event)
        self._plan_page.refresh()
        self._cal_page.refresh()

    # ── 拖动 ──

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self, '_drag_offset'):
            self.move(self.pos() + event.pos() - self._drag_offset)


# ══════════════════════════════════════
#  Plan 页（今日任务清单）
# ══════════════════════════════════════

class _PlanPage(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 6, 4, 0)
        layout.setSpacing(0)

        date_label = QLabel(QDate.currentDate().toString("yyyy-MM-dd  dddd"))
        date_label.setFont(QFont("Arial", 10))
        date_label.setStyleSheet(f"color: {C_SUB}; border: none; background: transparent;")
        date_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(date_label)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background: {C_BORDER}; border: none; max-height: 1px;")
        layout.addWidget(sep)

        self._tasks_layout = QVBoxLayout()
        self._tasks_layout.setSpacing(8)
        self._tasks_layout.setContentsMargins(4, 8, 4, 4)
        layout.addLayout(self._tasks_layout)
        layout.addStretch()

    def refresh(self):
        # 清除
        while self._tasks_layout.count():
            item = self._tasks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()

        today = QDate.currentDate().toString("yyyy-MM-dd")
        tasks = {}
        try:
            with open(TASK_FILE, "r", encoding="utf-8") as f:
                tasks = json.load(f)
        except Exception:
            pass

        if today in tasks and tasks[today].strip():
            task_list = [t.strip() for t in tasks[today].split('\n') if t.strip()]
        else:
            task_list = list(DEFAULT_TASKS)

        completed_tasks = {}
        if os.path.exists(COMPLETED_FILE):
            try:
                with open(COMPLETED_FILE, "r", encoding="utf-8") as f:
                    all_c = json.load(f)
                    completed_tasks = all_c.get(today, {})
            except Exception:
                pass

        for i, task in enumerate(task_list):
            cb = QCheckBox(task)
            cb.setFont(QFont("Arial", 11))
            cb.setStyleSheet(f"""
                QCheckBox {{
                    color: {C_TEXT}; border: none; background: transparent; spacing: 8px;
                }}
                QCheckBox::indicator {{
                    width: 18px; height: 18px;
                    border: 2px solid #F28D40; border-radius: 4px; background: white;
                }}
                QCheckBox::indicator:checked {{
                    background: #F28D40; border: 2px solid #F28D40;
                }}
                QCheckBox::indicator:hover {{ border: 2px solid #D77A35; }}
            """)
            if completed_tasks.get(str(i), False):
                cb.setChecked(True)
            cb.stateChanged.connect(lambda state, idx=i: self._save_state(idx, state))
            self._tasks_layout.addWidget(cb)

    @staticmethod
    def _save_state(task_index, state):
        today = QDate.currentDate().toString("yyyy-MM-dd")
        all_c = {}
        if os.path.exists(COMPLETED_FILE):
            try:
                with open(COMPLETED_FILE, "r", encoding="utf-8") as f:
                    all_c = json.load(f)
            except Exception:
                pass
        if today not in all_c:
            all_c[today] = {}
        all_c[today][str(task_index)] = (state == 2)
        try:
            with open(COMPLETED_FILE, "w", encoding="utf-8") as f:
                json.dump(all_c, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


# ══════════════════════════════════════
#  Calendar 页（内嵌日历 + 编辑）
# ══════════════════════════════════════

class _CalendarPage(QWidget):
    def __init__(self):
        super().__init__()
        self._tasks = {}
        self._load_tasks()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 6, 4, 4)
        layout.setSpacing(6)

        # ── 月份导航 ──
        nav = QHBoxLayout()
        self._prev_btn = QPushButton("\u25c0")
        self._next_btn = QPushButton("\u25b6")
        for btn in (self._prev_btn, self._next_btn):
            btn.setFixedSize(32, 26)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {C_ACCENT}; border: none; border-radius: 13px;
                    color: {C_TEXT}; font-size: 12px;
                }}
                QPushButton:hover {{ background: {C_ACCENT_H}; }}
            """)
        self._prev_btn.clicked.connect(self._prev_month)
        self._next_btn.clicked.connect(self._next_month)

        self._month_label = QLabel()
        self._month_label.setFont(QFont("Arial", 12, QFont.Bold))
        self._month_label.setStyleSheet(f"color: {C_TEXT}; border: none; background: transparent;")
        self._month_label.setAlignment(Qt.AlignCenter)
        nav.addWidget(self._prev_btn)
        nav.addWidget(self._month_label, 1)
        nav.addWidget(self._next_btn)
        layout.addLayout(nav)

        # ── 星期标题 ──
        week_row = QHBoxLayout()
        week_row.setSpacing(2)
        for d in ["S", "M", "T", "W", "T", "F", "S"]:
            lbl = QLabel(d)
            lbl.setFont(QFont("Arial", 9, QFont.Bold))
            lbl.setStyleSheet(f"color: {C_SUB}; border: none; background: transparent;")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setFixedWidth(36)
            week_row.addWidget(lbl)
        layout.addLayout(week_row)

        # ── 日期网格 ──
        self._grid = QGridLayout()
        self._grid.setSpacing(4)
        layout.addLayout(self._grid)

        self._current_date = QDate.currentDate()
        self._update_calendar()

    def refresh(self):
        self._load_tasks()
        self._update_calendar()

    # ── 日历逻辑 ──

    def _update_calendar(self):
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._month_label.setText(self._current_date.toString("MMMM yyyy"))
        first_day = QDate(self._current_date.year(), self._current_date.month(), 1)
        start_col = first_day.dayOfWeek() % 7
        days = self._current_date.daysInMonth()

        today = QDate.currentDate()
        day = 1
        for row in range(6):
            for col in range(7):
                if (row == 0 and col < start_col) or day > days:
                    lbl = QLabel()
                    self._grid.addWidget(lbl, row, col)
                else:
                    date = QDate(self._current_date.year(), self._current_date.month(), day)
                    btn = QPushButton(str(day))
                    btn.setFixedSize(36, 32)
                    btn.setFont(QFont("Arial", 10))

                    is_today = (date == today)
                    has_task = date.toString("yyyy-MM-dd") in self._tasks

                    if is_today:
                        bg, fw = C_ACCENT_H, "bold"
                    elif has_task:
                        bg, fw = "rgba(242, 141, 64, 0.18)", "bold"
                    else:
                        bg, fw = "transparent", "normal"

                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background: {bg}; border: none; border-radius: 8px;
                            color: {C_TEXT}; font-weight: {fw}; text-align: center;
                        }}
                        QPushButton:hover {{ background: {C_ACCENT}; }}
                    """)
                    btn.clicked.connect(lambda _, d=date: self._on_date_clicked(d))
                    self._grid.addWidget(btn, row, col)
                    day += 1

    def _prev_month(self):
        self._current_date = self._current_date.addMonths(-1)
        self._update_calendar()

    def _next_month(self):
        self._current_date = self._current_date.addMonths(1)
        self._update_calendar()

    def _on_date_clicked(self, date):
        date_str = date.toString("yyyy-MM-dd")
        existing = self._tasks.get(date_str, "")
        # 当天无数据时，预填默认任务
        if not existing.strip() and date == QDate.currentDate():
            existing = "\n".join(DEFAULT_TASKS)
        dlg = _TaskEditDialog(date, existing)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            task = dlg.get_task()
            if task:
                self._tasks[date_str] = task
            elif date_str in self._tasks:
                del self._tasks[date_str]
            self._save_tasks()
            self._update_calendar()

    # ── 任务持久化 ──

    def _load_tasks(self):
        try:
            with open(TASK_FILE, "r", encoding="utf-8") as f:
                self._tasks = json.load(f)
        except Exception:
            self._tasks = {}

    def _save_tasks(self):
        try:
            with open(TASK_FILE, "w", encoding="utf-8") as f:
                json.dump(self._tasks, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


# ══════════════════════════════════════
#  任务编辑弹窗（风格统一）
# ══════════════════════════════════════

class _TaskEditDialog(QDialog):
    def __init__(self, date: QDate, existing_text: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Task")
        self.setFixedSize(300, 320)
        self.setStyleSheet(f"""
            QDialog {{
                background: {C_BG}; border-radius: {C_RADIUS}px;
            }}
        """)
        self._build_ui(date, existing_text)

    def _build_ui(self, date, existing_text):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # 标题
        title = QLabel(f"Tasks for {date.toString('MMM d')}")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setStyleSheet(f"color: {C_TEXT}; background: transparent;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background: {C_BORDER}; border: none; max-height: 1px;")
        layout.addWidget(sep)

        self._edit = QTextEdit()
        self._edit.setPlaceholderText("Enter your tasks (one per line)...")
        self._edit.setPlainText(existing_text)
        self._edit.setStyleSheet(f"""
            QTextEdit {{
                background: rgba(255, 255, 255, 0.85);
                border: 1px solid {C_BORDER};
                border-radius: 10px;
                padding: 10px;
                font-size: 13px;
                color: {C_TEXT};
            }}
        """)
        layout.addWidget(self._edit, stretch=1)

        # 按钮
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        ok_btn = QPushButton("Save")
        ok_btn.setFont(QFont("Arial", 11, QFont.Bold))
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background: #F28D40; color: white; border: none;
                border-radius: 10px; padding: 8px 0;
            }}
            QPushButton:hover {{ background: #D77A35; }}
        """)
        ok_btn.clicked.connect(self.accept)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFont(QFont("Arial", 11, QFont.Bold))
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C_ACCENT}; color: {C_TEXT}; border: none;
                border-radius: 10px; padding: 8px 0;
            }}
            QPushButton:hover {{ background: {C_ACCENT_H}; }}
        """)
        cancel_btn.clicked.connect(self.reject)

        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    def get_task(self) -> str:
        return self._edit.toPlainText().strip()
