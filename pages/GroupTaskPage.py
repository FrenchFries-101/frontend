from datetime import datetime, timedelta

from PySide6.QtCore import Qt
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
)

import session
from service.api import (
    get_user_groups,
    create_group_task,
    get_group_tasks,
    get_group_ranking,
    get_group_my_stats,
    get_groups,
)


class GroupTaskPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
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
            QWidget {
                background: #fff6ea;
                color: #4a3b1f;
            }
            QFrame#sectionCard {
                background: #fffaf0;
                border: 1px solid #ffe08e;
                border-radius: 10px;
            }
            QLabel {
                background: transparent;
                border: none;
            }
            QLabel#titleLine {
                font-size: 15px;
                font-weight: 700;
                color: #3b2f18;
                padding: 2px 0;
            }
            QLabel#metaText {
                font-size: 12px;
                color: #7a6640;
            }
            QLabel#fieldLabel {
                font-size: 15px;
                font-weight: 700;
                color: #4a3b1f;
                min-width: 120px;
            }
            QComboBox {
                background: #fffdf7;
                border: 1px solid #f1d38a;
                border-radius: 9px;
                padding: 6px 34px 6px 10px;
                min-height: 28px;
                font-size: 13px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 28px;
                border-left: 1px solid #f1d38a;
                border-top-right-radius: 9px;
                border-bottom-right-radius: 9px;
                background: #fff1cf;
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
                border: 1px solid #f1d38a;
                border-radius: 8px;
                background: #fffdf7;
                text-align: center;
                color: #5b4518;
                min-height: 16px;
            }
            QProgressBar::chunk {
                border-radius: 7px;
                background: #e7bf5f;
            }
            QPushButton {
                border: 1px solid #f1d38a;
                border-radius: 8px;
                padding: 8px 12px;
                background: #ffe8a8;
                color: #5b4518;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #ffe08e;
                border: 1px solid #dfb75b;
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
                background: #fff3d4;
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

        left_col = QVBoxLayout()
        left_col.setSpacing(10)
        right_col = QVBoxLayout()
        right_col.setSpacing(10)

        weekly_title = QLabel("📊 Weekly Overview")
        weekly_title.setObjectName("titleLine")
        left_col.addWidget(weekly_title)

        weekly_row = QHBoxLayout()
        self.weekly_progress = QProgressBar()
        self.weekly_progress.setRange(0, 100)
        self.weekly_progress.setValue(0)
        self.weekly_progress.setFormat("%p%")
        self.weekly_percent = QLabel("0%")
        self.weekly_percent.setObjectName("metaText")
        weekly_row.addWidget(self.weekly_progress, 1)
        weekly_row.addWidget(self.weekly_percent)
        left_col.addLayout(weekly_row)

        current_title = QLabel("📌 Current Tasks")
        current_title.setObjectName("titleLine")
        left_col.addWidget(current_title)

        self.word_task_card, self.word_task_bar, self.word_task_current, self.word_task_reward = self._build_task_card(
            title="Word Task",
            percent=0,
            current_text="-- / --",
            reward_text="Reward: -- coins",
        )
        self.listening_task_card, self.listening_task_bar, self.listening_task_current, self.listening_task_reward = self._build_task_card(
            title="Listening Task",
            percent=0,
            current_text="-- / --",
            reward_text="Reward: -- coins",
        )
        left_col.addWidget(self.word_task_card)
        left_col.addWidget(self.listening_task_card)
        left_col.addStretch(1)

        rank_title = QLabel("🏆 Leaderboard")
        rank_title.setObjectName("titleLine")
        right_col.addWidget(rank_title)

        rank_card = QFrame()
        rank_card.setObjectName("sectionCard")
        rank_layout = QVBoxLayout(rank_card)
        rank_layout.setContentsMargins(10, 8, 10, 8)
        rank_layout.setSpacing(6)
        self.rank_labels = []
        for i in range(5):
            lb = QLabel(f"{i + 1}. --")
            lb.setObjectName("metaText")
            lb.setWordWrap(True)
            self.rank_labels.append(lb)
            rank_layout.addWidget(lb, 0)
        right_col.addWidget(rank_card)


        my_title = QLabel("👤 My Stats")
        my_title.setObjectName("titleLine")
        right_col.addWidget(my_title)

        my_card = QFrame()
        my_card.setObjectName("sectionCard")
        my_layout = QVBoxLayout(my_card)
        my_layout.setContentsMargins(10, 8, 10, 8)
        my_layout.setSpacing(4)

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
            w.setObjectName("metaText")
            w.setWordWrap(True)
            my_layout.addWidget(w)


        right_col.addWidget(my_card)
        right_col.addStretch(1)

        root.addLayout(left_col, 3)
        root.addLayout(right_col, 2)
        return page

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


        root.addWidget(card)
        root.addStretch(1)

        self._on_create_type_changed(0)
        return page

    def _build_task_card(self, title, percent, current_text, reward_text):
        card = QFrame()
        card.setObjectName("sectionCard")

        lay = QVBoxLayout(card)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(6)

        title_label = QLabel(title)
        title_label.setObjectName("titleLine")

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
        return card, bar, current_label, reward_label

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
        self.word_task_bar.setValue(0)
        self.word_task_current.setText("-- / --")
        self.word_task_reward.setText("Reward: -- coins")

        self.listening_task_bar.setValue(0)
        self.listening_task_current.setText("-- / --")
        self.listening_task_reward.setText("Reward: -- coins")

        self.weekly_progress.setValue(0)
        self.weekly_percent.setText("0%")

    def _reset_right_panels(self):
        for i, lb in enumerate(self.rank_labels):
            lb.setText(f"{i + 1}. --")

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

            if activity_type == "word":
                self.word_task_bar.setValue(percent)
                self.word_task_current.setText(f"{current} / {target}")
                self.word_task_reward.setText(f"Reward: {reward} coins")
            elif activity_type == "listening":
                self.listening_task_bar.setValue(percent)
                self.listening_task_current.setText(f"{current} / {target}")
                self.listening_task_reward.setText(f"Reward: {reward} coins")

        weekly_percent = int((total_current / total_target) * 100) if total_target > 0 else 0
        weekly_percent = max(0, min(100, weekly_percent))
        self.weekly_progress.setValue(weekly_percent)
        self.weekly_percent.setText(f"{weekly_percent}%")

        self.refresh_right_panels(group_id)

    def refresh_right_panels(self, group_id):
        self._reset_right_panels()

        ranking = get_group_ranking(group_id)
        if isinstance(ranking, list):
            for i, row in enumerate(ranking[: len(self.rank_labels)]):
                if not isinstance(row, dict):
                    continue
                rank = self._safe_int(row.get("rank"), i + 1)
                username = str(row.get("username") or "Unknown")
                total = self._safe_int(row.get("total_contribution"), 0)
                self.rank_labels[i].setText(f"{rank}. {username}  ({total})")

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
            self.refresh_task_cards()
            return

        data = self.group_combo.itemData(index)
        if not isinstance(data, dict):
            self._current_group = None
            self._set_create_task_visibility(None)
            self.refresh_task_cards()
            return

        self._current_group = data
        role = str(self.group_combo.itemData(index, Qt.UserRole + 1) or "member")
        self._set_create_task_visibility(role)
        self.refresh_task_cards()

    def _set_create_task_visibility(self, role):
        self._current_role = str(role or "")
        is_leader = self._current_role.lower() == "leader"
        self.create_task_btn.setVisible(is_leader)
        if not is_leader:
            self.content_stack.setCurrentIndex(0)
