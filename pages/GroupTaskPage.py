from datetime import datetime, timedelta

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QProgressBar,
    QPushButton,
    QFrame,
    QStackedLayout,
    QScrollArea,
)

import session
from service.api import (
    get_user_groups,
    create_group_task,
    get_group_tasks,
    get_group_ranking,
    get_group_my_stats,
    get_groups,
    get_user_rank,
)
from utils.path_utils import resource_path



class GroupTaskPage(QWidget):
    coin_points_updated = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("groupTaskPage")
        self._groups = []

        self._current_group = None
        self._current_role = None
        self._current_target_amount = 0
        self._current_reward_coins = 0

        self._task_rules = {
            "word": {"name": "Word", "unit": "words", "base_target": 200, "step": 50, "base_reward": 80},
            "listening": {"name": "Listening", "unit": "articles", "base_target": 5, "step": 1, "base_reward": 40},
            "speaking": {"name": "Speaking", "unit": "times", "base_target": 5, "step": 1, "base_reward": 60},
        }

        self._build_ui()
        self.refresh_groups()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(12)

        self.setStyleSheet(
            """
            QWidget#groupTaskPage {
                background: #fff3e8;
                color: #4a3b1f;
            }
            QFrame#sectionCard {
                background: #ffffff;
                border: 1px solid #efcfb7;
                border-radius: 0px;
            }

            QLabel {
                background: transparent;
                border: none;
            }
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }

            QLabel#titleLine {
                font-size: 19px;
                font-weight: 800;
                color: #3b2f18;
                padding: 2px 0;
            }
            QLabel#metaText {
                font-size: 14px;
                color: #7a6640;
            }
            QLabel#taskSectionTitle {
                font-size: 16px;
                font-weight: 700;
                color: #4d3c1f;
                padding-top: 4px;
            }
            QLabel#rankNameText {
                font-size: 14px;
                font-weight: 700;
                color: #3f3118;
            }

            QLabel#rankScoreText {
                font-size: 14px;
                color: #7a6640;
            }
            QLabel#statusText {
                font-size: 16px;
                font-weight: 600;
                color: #4a3b1f;
            }
            QLabel#fieldLabel {
                font-size: 15px;
                font-weight: 700;
                color: #4a3b1f;
                min-width: 120px;
            }
            QComboBox {
                background: #fff3e8;
                border: 1px solid #efcfb7;
                border-radius: 9px;
                padding: 6px 34px 6px 10px;
                min-height: 28px;
                font-size: 13px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 28px;
                border-left: 1px solid #efcfb7;
                border-top-right-radius: 9px;
                border-bottom-right-radius: 9px;
                background: #fbe7d8;
            }
            QComboBox::down-arrow {
                image: none;
                width: 0;
                height: 0;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #8a6a2d;
                margin-right: 9px;
            }
            QProgressBar {
                border: 1px solid #efcfb7;
                border-radius: 8px;
                background: #ffffff;
                text-align: center;
                color: #5b4518;
                min-height: 20px;
                font-size: 13px;
            }
            QProgressBar::chunk {
                border-radius: 7px;
                background: #e7bf5f;
            }
            QPushButton {
                border: 1px solid #efcfb7;
                border-radius: 8px;
                padding: 8px 12px;
                background: #fff3e8;
                color: #5b4518;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #ffe8d6;
                border: 1px solid #e2b89a;
            }
            QPushButton#taskTabBtn {
                min-height: 34px;
                font-size: 14px;
                font-weight: 700;
                background: #fff0e3;
            }
            QPushButton#taskTabBtn:checked {
                background: #ffe2cc;
                border: 1px solid #e2b89a;
            }
            QPushButton#tinyBtn {
                min-width: 36px;
                max-width: 36px;
                min-height: 34px;
                max-height: 34px;
                padding: 0;
                text-align: center;
                font-size: 18px;
                font-weight: 700;
            }
            QPushButton#secondaryBtn {
                background: #ffffff;
            }
            QPushButton#createTopBtn {
                padding: 8px 14px;
            }
            QPushButton#actionBtn {
                min-width: 110px;
            }
            """
        )

        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        selector_label = QLabel("Group")
        selector_label.setObjectName("metaText")
        self.group_combo = QComboBox()
        self.group_combo.currentIndexChanged.connect(self._on_group_changed)

        top_row.addWidget(selector_label)
        top_row.addWidget(self.group_combo, 1)
        top_row.addSpacing(14)

        self.create_task_btn = QPushButton("+ Create Task")
        self.create_task_btn.setObjectName("createTopBtn")
        self.create_task_btn.setVisible(False)
        self.create_task_btn.clicked.connect(self._enter_create_mode)
        top_row.addWidget(self.create_task_btn, alignment=Qt.AlignRight)

        root.addLayout(top_row)

        stack_host = QWidget()
        self.content_stack = QStackedLayout(stack_host)
        self.content_stack.setContentsMargins(0, 0, 0, 0)

        self.content_stack.addWidget(self._build_board_page())
        self.content_stack.addWidget(self._build_create_page())

        root.addWidget(stack_host, 1)

    def _build_board_page(self):
        page = QWidget()
        root = QHBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        left_panel = QFrame()
        left_panel.setObjectName("sectionCard")
        left_col = QVBoxLayout(left_panel)
        left_col.setContentsMargins(14, 12, 14, 12)
        left_col.setSpacing(10)

        left_col.addWidget(self._build_title_row("Weekly Overview", resource_path("resources/icons/file.png")))


        weekly_row = QHBoxLayout()
        self.weekly_progress = QProgressBar()
        self.weekly_progress.setRange(0, 100)
        self.weekly_progress.setValue(0)
        self.weekly_progress.setFormat("%p%")
        self.weekly_percent = QLabel("0%")
        self.weekly_percent.setObjectName("titleLine")
        weekly_row.addWidget(self.weekly_progress, 1)
        weekly_row.addWidget(self.weekly_percent)
        left_col.addLayout(weekly_row)

        left_col.addWidget(self._build_title_row("Tasks", resource_path("resources/icons/to-do-list.png")))


        tab_row = QHBoxLayout()
        tab_row.setSpacing(8)
        self.in_progress_btn = QPushButton("In Progress")
        self.in_progress_btn.setObjectName("taskTabBtn")
        self.in_progress_btn.setCheckable(True)
        self.in_progress_btn.setChecked(True)
        self.in_progress_btn.clicked.connect(lambda: self._switch_task_tab(0))

        self.finished_btn = QPushButton("Finished")
        self.finished_btn.setObjectName("taskTabBtn")
        self.finished_btn.setCheckable(True)
        self.finished_btn.clicked.connect(lambda: self._switch_task_tab(1))

        tab_row.addWidget(self.in_progress_btn)
        tab_row.addWidget(self.finished_btn)
        tab_row.addStretch(1)
        left_col.addLayout(tab_row)

        task_stack_host = QWidget()
        self.task_stack = QStackedLayout(task_stack_host)
        self.task_stack.setContentsMargins(0, 0, 0, 0)

        self.in_progress_page, self.unfinished_task_layout, self.completed_task_layout = self._make_task_tab_page(
            include_completed_block=True
        )
        self.finished_page, self.finished_task_layout, _ = self._make_task_tab_page(include_completed_block=False)
        self.task_stack.addWidget(self.in_progress_page)
        self.task_stack.addWidget(self.finished_page)
        self._switch_task_tab(0)

        left_col.addWidget(task_stack_host, 1)


        right_panel = QFrame()
        right_panel.setObjectName("sectionCard")
        right_col = QVBoxLayout(right_panel)
        right_col.setContentsMargins(14, 12, 14, 12)
        right_col.setSpacing(10)

        right_col.addWidget(self._build_title_row("Leader Board", resource_path("resources/icons/winner.png")))


        rank_card = QFrame()
        rank_card.setObjectName("sectionCard")
        rank_layout = QVBoxLayout(rank_card)
        rank_layout.setContentsMargins(10, 10, 10, 10)
        rank_layout.setSpacing(8)
        self.rank_rows = []
        for i in range(5):
            row = self._create_rank_row(i)
            self.rank_rows.append(row)
            rank_layout.addWidget(row["container"])
        right_col.addWidget(rank_card, 1)

        right_col.addWidget(self._build_title_row("My Status", resource_path("resources/icons/work-in-progress.png")))


        my_card = QFrame()
        my_card.setObjectName("sectionCard")
        my_layout = QVBoxLayout(my_card)
        my_layout.setContentsMargins(12, 10, 12, 10)
        my_layout.setSpacing(8)

        self.my_word_label = QLabel("Word: --")
        self.my_listening_label = QLabel("Listening: --")
        self.my_speaking_label = QLabel("Speaking: --")
        self.my_coins_label = QLabel("Coins This Week: --")
        self.my_rank_label = QLabel("Rank: --")
        for w in [
            self.my_word_label,
            self.my_listening_label,
            self.my_speaking_label,
            self.my_coins_label,
            self.my_rank_label,
        ]:
            w.setObjectName("statusText")
            w.setWordWrap(True)
            my_layout.addWidget(w)

        right_col.addWidget(my_card, 1)

        root.addWidget(left_panel, 1)
        root.addWidget(right_panel, 1)
        return page

    def _build_title_row(self, text, icon_rel_path):
        host = QWidget()
        row = QHBoxLayout(host)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        icon_label = QLabel()
        pix = self._load_icon_pixmap(icon_rel_path, 24)
        if pix is not None:
            icon_label.setPixmap(pix)
            icon_label.setFixedSize(24, 24)

        text_label = QLabel(text)
        text_label.setObjectName("titleLine")

        row.addWidget(icon_label, 0, Qt.AlignVCenter)
        row.addWidget(text_label, 0, Qt.AlignVCenter)
        row.addStretch(1)
        return host

    @staticmethod
    def _load_icon_pixmap(icon_rel_path, size):
        try:
            pix = QPixmap(resource_path(icon_rel_path))
            if pix.isNull():
                return None
            return pix.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        except Exception:
            return None

    def _make_task_tab_page(self, include_completed_block=True):
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)

        first_title_text = "Unfinished" if include_completed_block else "Finished Tasks"
        unfinished_title = QLabel(first_title_text)
        unfinished_title.setObjectName("taskSectionTitle")
        content_layout.addWidget(unfinished_title)


        unfinished_layout = QVBoxLayout()
        unfinished_layout.setSpacing(8)
        content_layout.addLayout(unfinished_layout)

        completed_layout = None
        if include_completed_block:
            completed_title = QLabel("Completed")
            completed_title.setObjectName("taskSectionTitle")
            content_layout.addWidget(completed_title)

            completed_layout = QVBoxLayout()
            completed_layout.setSpacing(8)
            content_layout.addLayout(completed_layout)

        content_layout.addStretch(1)
        scroll.setWidget(content)
        page_layout.addWidget(scroll)
        return page, unfinished_layout, completed_layout

    def _create_rank_row(self, index):
        row = QFrame()
        row.setObjectName("sectionCard")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(8, 6, 8, 6)
        row_layout.setSpacing(8)

        icon_label = QLabel()
        icon_label.setFixedSize(24, 24)
        if index == 0:
            icon_path = resource_path("resources/icons/first-rank.png")
        elif index == 1:
            icon_path = resource_path("resources/icons/second-rank.png")
        elif index == 2:
            icon_path = resource_path("resources/icons/third-rank.png")

        else:
            icon_path = ""

        if icon_path:
            pix = self._load_icon_pixmap(icon_path, 22)
            if pix is not None:
                icon_label.setPixmap(pix)

        text_host = QWidget()
        text_layout = QVBoxLayout(text_host)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        name_label = QLabel(f"{index + 1}. --")
        name_label.setObjectName("rankNameText")
        score_label = QLabel("Score: --")
        score_label.setObjectName("rankScoreText")

        text_layout.addWidget(name_label)
        text_layout.addWidget(score_label)

        row_layout.addWidget(icon_label)
        row_layout.addWidget(text_host, 1)
        return {"container": row, "name": name_label, "score": score_label}


    def _build_create_page(self):
        page = QWidget()
        root = QVBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        title = QLabel("🛠 Create Task")
        title.setObjectName("titleLine")
        root.addWidget(title)

        card = QFrame()
        card.setObjectName("sectionCard")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(10)

        type_row = QHBoxLayout()
        task_type_label = QLabel("Task Type")
        task_type_label.setObjectName("fieldLabel")
        type_row.addWidget(task_type_label)
        self.create_type_combo = QComboBox()
        self.create_type_combo.addItem("Word", "word")
        self.create_type_combo.addItem("Listening", "listening")
        self.create_type_combo.addItem("Speaking", "speaking")
        self.create_type_combo.currentIndexChanged.connect(self._on_create_type_changed)
        type_row.addWidget(self.create_type_combo, 1)
        lay.addLayout(type_row)

        qty_row = QHBoxLayout()
        target_label = QLabel("Target Amount")
        target_label.setObjectName("fieldLabel")
        qty_row.addWidget(target_label)

        target_ctrl = QHBoxLayout()
        target_ctrl.setSpacing(8)
        self.minus_btn = QPushButton("-")
        self.minus_btn.setObjectName("tinyBtn")
        self.minus_btn.clicked.connect(lambda: self._change_target(-1))
        self.plus_btn = QPushButton("+")
        self.plus_btn.setObjectName("tinyBtn")
        self.plus_btn.clicked.connect(lambda: self._change_target(1))
        self.target_value_label = QLabel("--")
        self.target_value_label.setObjectName("titleLine")
        self.target_value_label.setAlignment(Qt.AlignCenter)
        target_ctrl.addWidget(self.minus_btn, 0, Qt.AlignVCenter)
        target_ctrl.addWidget(self.target_value_label, 1)
        target_ctrl.addWidget(self.plus_btn, 0, Qt.AlignVCenter)

        qty_row.addLayout(target_ctrl, 1)
        lay.addLayout(qty_row)


        self.reward_label = QLabel("Reward Coins: --")
        self.reward_label.setObjectName("titleLine")
        lay.addWidget(self.reward_label)

        self.week_task_label = QLabel(self._current_week_text())
        self.week_task_label.setObjectName("metaText")
        lay.addWidget(self.week_task_label)

        self.preview_label = QLabel("Weekly Task: --")
        self.preview_label.setObjectName("metaText")
        lay.addWidget(self.preview_label)

        self.create_feedback_label = QLabel("")
        self.create_feedback_label.setObjectName("metaText")
        lay.addWidget(self.create_feedback_label)

        action_row = QHBoxLayout()
        action_row.setSpacing(20)
        action_row.addStretch(1)
        self.cancel_create_btn = QPushButton("Back")
        self.cancel_create_btn.setObjectName("secondaryBtn")
        self.cancel_create_btn.setMinimumWidth(110)
        self.cancel_create_btn.clicked.connect(self._leave_create_mode)
        self.submit_create_btn = QPushButton("Create")
        self.submit_create_btn.setObjectName("actionBtn")

        self.submit_create_btn.clicked.connect(self._submit_create_task)
        action_row.addWidget(self.cancel_create_btn, 0, Qt.AlignCenter)
        action_row.addWidget(self.submit_create_btn, 0, Qt.AlignCenter)
        action_row.addStretch(1)
        lay.addLayout(action_row)


        root.addWidget(card, 1)


        self._on_create_type_changed(0)
        return page

    def _build_task_card(self, title, percent, current_text, reward_text):
        card = QFrame()
        card.setObjectName("sectionCard")

        lay = QVBoxLayout(card)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(6)

        title_label = QLabel(title)
        title_label.setObjectName("taskSectionTitle")

        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(max(0, min(100, int(percent))))
        bar.setFormat("%p%")

        current_label = QLabel(current_text)
        current_label.setObjectName("metaText")

        reward_label = QLabel(reward_text)
        reward_label.setObjectName("metaText")

        lay.addWidget(title_label)
        lay.addWidget(bar)
        lay.addWidget(current_label)
        lay.addWidget(reward_label)
        return card

    def _task_name(self, activity_type):
        key = str(activity_type or "").lower()
        if key in self._task_rules:
            return str(self._task_rules[key].get("name") or key.title())
        return key.replace("_", " ").title() if key else "Task"

    def _task_unit(self, activity_type):
        key = str(activity_type or "").lower()
        if key in self._task_rules:
            return str(self._task_rules[key].get("unit") or "times")
        return "times"

    @staticmethod
    def _clear_layout_widgets(layout):
        if layout is None:
            return
        while layout.count() > 0:
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    @staticmethod
    def _parse_iso_date(value):
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except Exception:
            return None

    def _switch_task_tab(self, index):
        self.task_stack.setCurrentIndex(index)
        self.in_progress_btn.setChecked(index == 0)
        self.finished_btn.setChecked(index == 1)

    def _current_user_id(self):

        user = session.user
        if isinstance(user, dict):
            return user.get("user_id") or user.get("id")
        if hasattr(user, "user_id"):
            return getattr(user, "user_id")
        if hasattr(user, "id"):
            return getattr(user, "id")
        return None

    def _current_week_range(self):
        now = datetime.now()
        start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=6, hours=23, minutes=59, seconds=59)
        return start, end

    def _current_week_text(self):
        start, end = self._current_week_range()
        return f"Weekly Task: {start.strftime('%Y-%m-%d')} ~ {end.strftime('%Y-%m-%d')}"

    def _active_rule(self):
        key = self.create_type_combo.currentData()
        return self._task_rules.get(key, self._task_rules["word"])

    def _on_create_type_changed(self, _index):
        rule = self._active_rule()
        self._current_target_amount = int(rule["base_target"])
        self._update_create_preview()

    def _change_target(self, delta_steps):
        rule = self._active_rule()
        step = int(rule["step"])
        base_target = int(rule["base_target"])
        new_val = self._current_target_amount + delta_steps * step
        self._current_target_amount = max(base_target, new_val)
        self._update_create_preview()

    def _calc_reward(self):
        rule = self._active_rule()
        base_target = int(rule["base_target"])
        base_reward = int(rule["base_reward"])
        return max(base_reward, int(self._current_target_amount * base_reward / base_target))

    def _update_create_preview(self):
        rule = self._active_rule()
        unit = str(rule["unit"])
        name = str(rule["name"])
        self._current_reward_coins = self._calc_reward()

        self.target_value_label.setText(f"{self._current_target_amount} {unit}")
        self.reward_label.setText(f"Reward Coins: {self._current_reward_coins}")
        self.preview_label.setText(
            f"Weekly Task: {name} {self._current_target_amount} {unit}, reward {self._current_reward_coins} coins"
        )

    def _enter_create_mode(self):
        if str(self._current_role).lower() != "leader":
            return
        self.create_feedback_label.setText("")
        self._on_create_type_changed(self.create_type_combo.currentIndex())
        self.content_stack.setCurrentIndex(1)

    def _leave_create_mode(self):
        self.create_feedback_label.setText("")
        self.content_stack.setCurrentIndex(0)

    def _reset_task_cards(self):
        self._clear_layout_widgets(self.unfinished_task_layout)
        self._clear_layout_widgets(self.completed_task_layout)
        self._clear_layout_widgets(self.finished_task_layout)
        self.weekly_progress.setValue(0)
        self.weekly_percent.setText("0%")

    def _reset_right_panels(self):
        for i, row in enumerate(self.rank_rows):
            row["name"].setText(f"{i + 1}. --")
            row["score"].setText("Score: --")

        self.my_word_label.setText("Word: --")
        self.my_listening_label.setText("Listening: --")
        self.my_speaking_label.setText("Speaking: --")
        self.my_coins_label.setText("Coins This Week: --")
        self.my_rank_label.setText("Rank: --")

    @staticmethod
    def _safe_int(val, default=0):
        try:
            return int(val)
        except Exception:
            return default

    def _refresh_points_to_topbar(self):
        user_id = self._current_user_id()
        if user_id is None:
            return
        try:
            rank_data = get_user_rank(user_id)
            if isinstance(rank_data, dict) and rank_data.get("points") is not None:
                self.coin_points_updated.emit(self._safe_int(rank_data.get("points"), 0))
        except Exception:
            return

    def refresh_task_cards(self):
        if not isinstance(self._current_group, dict):
            self._reset_task_cards()
            self._reset_right_panels()
            return

        group_id = self._current_group.get("group_id")
        tasks = get_group_tasks(group_id)
        if not isinstance(tasks, list):
            self._reset_task_cards()
            self._reset_right_panels()
            return

        self._reset_task_cards()

        total_target = 0
        total_current = 0
        unfinished_count = 0
        completed_count = 0
        finished_count = 0

        now = datetime.now()

        completed_layout = self.completed_task_layout

        for item in tasks:
            if not isinstance(item, dict):
                continue


            activity_type = str(item.get("activity_type") or "")
            target = self._safe_int(item.get("target_amount"), 0)
            current = self._safe_int(item.get("current_amount"), 0)
            reward = self._safe_int(item.get("reward_coins"), 0)
            percent = int((current / target) * 100) if target > 0 else 0
            percent = max(0, min(100, percent))

            total_target += max(0, target)
            total_current += max(0, current)

            unit = self._task_unit(activity_type)
            name = self._task_name(activity_type)
            card = self._build_task_card(
                title=f"{name} Task",
                percent=percent,
                current_text=f"{current} / {target} {unit}",
                reward_text=f"Reward: {reward} coins",
            )

            completed = target > 0 and current >= target
            status_text = str(item.get("status") or "").strip().lower()
            end_at = self._parse_iso_date(item.get("end_date"))
            is_ended = status_text in {"finished", "ended", "closed"}
            if (not is_ended) and end_at is not None:
                try:
                    cmp_now = datetime.now(end_at.tzinfo) if end_at.tzinfo else now
                    is_ended = cmp_now > end_at
                except Exception:
                    is_ended = False


            if is_ended:
                self.finished_task_layout.addWidget(card)
                finished_count += 1
            elif completed:
                if completed_layout is not None:
                    completed_layout.addWidget(card)
                completed_count += 1

            else:
                self.unfinished_task_layout.addWidget(card)
                unfinished_count += 1

        if unfinished_count == 0:
            empty_unfinished = QLabel("No unfinished tasks")
            empty_unfinished.setObjectName("metaText")
            self.unfinished_task_layout.addWidget(empty_unfinished)

        if completed_count == 0 and completed_layout is not None:
            empty_completed = QLabel("No completed tasks")
            empty_completed.setObjectName("metaText")
            completed_layout.addWidget(empty_completed)


        if finished_count == 0:
            empty_finished = QLabel("No finished tasks")
            empty_finished.setObjectName("metaText")
            self.finished_task_layout.addWidget(empty_finished)

        weekly_percent = int((total_current / total_target) * 100) if total_target > 0 else 0
        weekly_percent = max(0, min(100, weekly_percent))
        self.weekly_progress.setValue(weekly_percent)
        self.weekly_percent.setText(f"{weekly_percent}%")

        self.refresh_right_panels(group_id)
        self._refresh_points_to_topbar()

    def refresh_right_panels(self, group_id):
        self._reset_right_panels()

        ranking = get_group_ranking(group_id)
        if isinstance(ranking, list):
            for i, row in enumerate(ranking[: len(self.rank_rows)]):
                if not isinstance(row, dict):
                    continue
                rank = self._safe_int(row.get("rank"), i + 1)
                username = str(row.get("username") or "Unknown")
                total = self._safe_int(row.get("total_contribution"), 0)
                self.rank_rows[i]["name"].setText(f"{rank}. {username}")
                self.rank_rows[i]["score"].setText(f"Score: {total}")

        user_id = self._current_user_id()
        if user_id is None:
            return

        my_stats = get_group_my_stats(group_id, user_id)
        if not isinstance(my_stats, dict):
            return

        contribution = my_stats.get("contribution") or {}
        if not isinstance(contribution, dict):
            contribution = {}

        self.my_word_label.setText(f"Word: {self._safe_int(contribution.get('word'), 0)}")
        self.my_listening_label.setText(f"Listening: {self._safe_int(contribution.get('listening'), 0)}")
        self.my_speaking_label.setText(f"Speaking: {self._safe_int(contribution.get('speaking'), 0)}")
        self.my_coins_label.setText(
            f"Coins This Week: {self._safe_int(my_stats.get('coins_earned_this_week'), 0)}"
        )
        self.my_rank_label.setText(f"Rank: {self._safe_int(my_stats.get('rank_in_group'), 0)}")

    def _submit_create_task(self):

        if not isinstance(self._current_group, dict):
            self.create_feedback_label.setStyleSheet("color:#b23a2d;")
            self.create_feedback_label.setText("Please select a valid group")
            return

        user_id = self._current_user_id()
        if user_id is None:
            self.create_feedback_label.setStyleSheet("color:#b23a2d;")
            self.create_feedback_label.setText("Please log in first")
            return

        group_id = self._current_group.get("group_id")
        activity_type = self.create_type_combo.currentData()
        start_date, end_date = self._current_week_range()

        resp = create_group_task(
            group_id=group_id,
            user_id=user_id,
            activity_type=activity_type,
            target_amount=self._current_target_amount,
            reward_coins=self._current_reward_coins,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )

        if isinstance(resp, dict) and resp.get("success"):
            self.create_feedback_label.setStyleSheet("color:#2c7b3f;")
            self.create_feedback_label.setText("Task created successfully")
            self.refresh_task_cards()
            self._leave_create_mode()
            return

        msg = "Failed to create task"
        if isinstance(resp, dict):
            msg = str(resp.get("detail") or resp.get("message") or msg)
        self.create_feedback_label.setStyleSheet("color:#b23a2d;")
        self.create_feedback_label.setText(msg)

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_groups()

    def _fetch_group_type_map(self):
        group_type_map = {}
        page = 1
        page_size = 100

        while True:
            data = get_groups(page=page, page_size=page_size)
            if not isinstance(data, dict):
                break

            rows = data.get("groups", [])
            if not isinstance(rows, list) or not rows:
                break

            for g in rows:
                if not isinstance(g, dict):
                    continue
                gid = g.get("group_id")
                if gid is None:
                    continue
                group_type_map[gid] = str(g.get("group_type") or "").lower()

            total = self._safe_int(data.get("total_count"), 0)
            if total <= page * page_size:
                break
            page += 1

        return group_type_map

    def refresh_groups(self):
        user_id = self._current_user_id()
        self.group_combo.blockSignals(True)
        self.group_combo.clear()
        self._groups = []

        if user_id is None:
            self.group_combo.addItem("Please log in", None)
            self.group_combo.blockSignals(False)
            self._set_create_task_visibility(None)
            self._current_group = None
            session.current_group_id = None
            self.refresh_task_cards()
            return

        data = get_user_groups(user_id)
        raw_groups = data.get("groups", []) if isinstance(data, dict) else []
        if not isinstance(raw_groups, list):
            raw_groups = []

        group_type_map = self._fetch_group_type_map()
        groups = []
        for g in raw_groups:
            if not isinstance(g, dict):
                continue
            gid = g.get("group_id")
            group_type = str(g.get("group_type") or group_type_map.get(gid) or "").lower()
            if group_type == "social":
                continue
            g["group_type"] = group_type or "study"
            groups.append(g)

        self._groups = groups

        if not groups:
            self.group_combo.addItem("No study groups", None)
            self.group_combo.blockSignals(False)
            self._set_create_task_visibility(None)
            self._current_group = None
            session.current_group_id = None
            self.refresh_task_cards()
            return


        for g in groups:
            name = str(g.get("group_name") or "Unnamed Group")
            gid = g.get("group_id")
            role = str(g.get("role") or "member")
            self.group_combo.addItem(f"{name}  (ID:{gid})", g)
            idx = self.group_combo.count() - 1
            self.group_combo.setItemData(idx, role, Qt.UserRole + 1)

        self.group_combo.blockSignals(False)
        self.group_combo.setCurrentIndex(0)
        self._on_group_changed(0)

    def _on_group_changed(self, index):
        if index < 0:
            self._set_create_task_visibility(None)
            self._current_group = None
            session.current_group_id = None
            self.refresh_task_cards()
            return

        data = self.group_combo.itemData(index)
        if not isinstance(data, dict):
            self._current_group = None
            self._set_create_task_visibility(None)
            session.current_group_id = None
            self.refresh_task_cards()
            return

        self._current_group = data
        session.current_group_id = data.get("group_id")
        role = str(self.group_combo.itemData(index, Qt.UserRole + 1) or "member")
        self._set_create_task_visibility(role)
        self.refresh_task_cards()


    def _set_create_task_visibility(self, role):
        self._current_role = str(role or "")
        is_leader = self._current_role.lower() == "leader"
        self.create_task_btn.setVisible(is_leader)
        if not is_leader:
            self.content_stack.setCurrentIndex(0)
