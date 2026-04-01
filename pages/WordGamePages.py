from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSizePolicy, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from service.api_word_game import join, cancel, status, gain_roll, roll
import session


# =========================
# Shared styles / helpers
# =========================
def make_panel(title_text: str):
    panel = QFrame()
    panel.setObjectName("wg_panel")
    panel.setStyleSheet("""
        QFrame#wg_panel {
            background: white;
            border: 2px solid #f3c4da;
            border-radius: 18px;
        }
        QLabel#wg_title {
            font-size: 22px;
            font-weight: 700;
            color: #9d174d;
        }
        QLabel#wg_subtitle {
            font-size: 14px;
            color: #666666;
        }
        QLabel#wg_text {
            font-size: 14px;
            color: #333333;
        }
        QLabel#wg_info {
            font-size: 14px;
            color: #444444;
            background: #fff7fb;
            border: 1px solid #f3c4da;
            border-radius: 12px;
            padding: 10px;
        }
        QPushButton {
            background: white;
            border: 2px solid #ec4899;
            border-radius: 14px;
            padding: 10px 16px;
            font-size: 14px;
            font-weight: 600;
            color: #333333;
        }
        QPushButton:hover {
            background: #fff1f7;
        }
        QPushButton:disabled {
            color: #999999;
            border-color: #d8b4c7;
            background: #fafafa;
        }
    """)

    root = QVBoxLayout(panel)
    root.setContentsMargins(24, 24, 24, 24)
    root.setSpacing(16)

    title = QLabel(title_text)
    title.setObjectName("wg_title")
    root.addWidget(title)

    return panel, root


def safe_user_id():
    if not hasattr(session, "user") or not session.user:
        return None
    return session.user.get("id")


def parse_match_info(data: dict):
    """
    将后端返回转换为更适合界面展示的文本。
    """
    if not data:
        return "No data.", None

    if data.get("in_match") is False:
        return "You have not joined any match yet.", None

    match = data.get("match")
    if not match:
        return "No active match information.", None

    match_id = match.get("id", "Unknown")
    match_status = match.get("status", "unknown")
    player_count = len(match.get("players", []))

    text = [
        f"Match ID: {match_id}",
        f"Status: {match_status}",
        f"Players joined: {player_count} / 4",
    ]

    if match_status == "waiting":
        text.append("Matching players... You can still cancel before the game starts.")
    elif match_status == "active":
        text.append("The match has started. You can now enter Game Board.")
    elif match_status == "finished":
        winner = match.get("winner")
        if winner:
            text.append(f"Winner: {winner.capitalize()} Team")
        else:
            text.append("The match has finished.")

    return "\n".join(text), match


def current_player(match: dict, user_id: int):
    for p in match.get("players", []):
        if p.get("user_id") == user_id:
            return p
    return None


def team_summary(match: dict, team: str):
    players = [p for p in match.get("players", []) if p.get("team") == team]
    if team == "red":
        pos = match.get("red_pos", 0)
        rolls = match.get("red_rolls", 0)
    else:
        pos = match.get("blue_pos", 0)
        rolls = match.get("blue_rolls", 0)

    lines = [
        f"Team: {team.capitalize()}",
        f"Current Position: {pos + 1}",
        f"Available Rolls: {rolls}",
        ""
    ]

    if not players:
        lines.append("No teammate info available yet.")
    else:
        lines.append("Today's roll contributions:")
        for idx, p in enumerate(players, start=1):
            contrib = p.get("roll_contribute", 0)
            lines.append(f"Member {idx}: {contrib}")

    return "\n".join(lines)


# =========================
# Game menu page
# =========================
class GameMenuPage(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        panel, root = make_panel("Game")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(panel)

        subtitle = QLabel("Choose what you want to do.")
        subtitle.setObjectName("wg_subtitle")
        root.addWidget(subtitle)

        btn_start = QPushButton("Start Game")
        btn_instruction = QPushButton("Instruction")

        btn_start.clicked.connect(lambda: parent.goto("start"))
        btn_instruction.clicked.connect(lambda: parent.goto("instruction"))

        root.addWidget(btn_start)
        root.addWidget(btn_instruction)
        root.addStretch(1)


# =========================
# Instruction page
# =========================
class InstructionPage(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        panel, root = make_panel("Game Instruction")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(panel)

        top = QHBoxLayout()
        back_btn = QPushButton("Back")
        back_btn.clicked.connect(lambda: parent.goto("game_menu"))
        top.addWidget(back_btn)
        top.addStretch(1)
        root.addLayout(top)

        text = QLabel(
            "1. A match requires exactly 4 players.\n\n"
            "2. Before the match is formed, players may cancel matching.\n\n"
            "3. Once 4 players are matched and the game starts, "
            "the match is locked to these 4 players only.\n\n"
            "4. No new player can join or replace them until the match ends.\n\n"
            "5. Players can operate at any time.\n\n"
            "6. A team can move only when it has available rolls.\n\n"
            "7. In the current stage, 'Gain 1 Roll' is used as a temporary demo action.\n\n"
            "8. The match ends only when one team reaches the goal."
        )
        text.setWordWrap(True)
        text.setObjectName("wg_info")
        root.addWidget(text)
        root.addStretch(1)


# =========================
# Start game page
# =========================
class StartGamePage(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        panel, root = make_panel("Start Game")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(panel)

        top = QHBoxLayout()
        back_btn = QPushButton("Back")
        back_btn.clicked.connect(lambda: parent.goto("game_menu"))
        top.addWidget(back_btn)
        top.addStretch(1)
        root.addLayout(top)

        subtitle = QLabel("Choose to join a match or enter the current game board.")
        subtitle.setObjectName("wg_subtitle")
        root.addWidget(subtitle)

        btn_join = QPushButton("Join Game")
        btn_board = QPushButton("Game Board")

        btn_join.clicked.connect(lambda: parent.goto("join"))
        btn_board.clicked.connect(lambda: parent.goto("board"))

        root.addWidget(btn_join)
        root.addWidget(btn_board)
        root.addStretch(1)


# =========================
# Join page
# =========================
class JoinPage(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        panel, root = make_panel("Join Game")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(panel)

        top = QHBoxLayout()
        back_btn = QPushButton("Back")
        back_btn.clicked.connect(lambda: parent.goto("start"))
        top.addWidget(back_btn)
        top.addStretch(1)
        root.addLayout(top)

        desc = QLabel("Join a match and wait until 4 players are ready.")
        desc.setObjectName("wg_subtitle")
        root.addWidget(desc)

        self.info = QLabel("You have not joined any match yet.")
        self.info.setObjectName("wg_info")
        self.info.setWordWrap(True)
        root.addWidget(self.info)

        btn_row = QHBoxLayout()
        self.join_btn = QPushButton("Join Game")
        self.cancel_btn = QPushButton("Cancel Matching")
        self.refresh_btn = QPushButton("Refresh Status")

        self.join_btn.clicked.connect(self.join_game)
        self.cancel_btn.clicked.connect(self.cancel_matching)
        self.refresh_btn.clicked.connect(self.refresh_status)

        btn_row.addWidget(self.join_btn)
        btn_row.addWidget(self.cancel_btn)
        btn_row.addWidget(self.refresh_btn)
        root.addLayout(btn_row)

        root.addStretch(1)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_status)
        self.timer.start(3000)

        self.refresh_status()

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_status()

    def refresh_status(self):
        user_id = safe_user_id()
        if user_id is None:
            self.info.setText("Please log in first.")
            self.join_btn.setEnabled(False)
            self.cancel_btn.setEnabled(False)
            self.refresh_btn.setEnabled(False)
            return

        try:
            res = status(user_id)
            text, match = parse_match_info(res)
            self.info.setText(text)

            if res.get("in_match") is False:
                self.join_btn.setEnabled(True)
                self.cancel_btn.setEnabled(False)
                return

            if match:
                if match.get("status") == "waiting":
                    self.join_btn.setEnabled(False)
                    self.cancel_btn.setEnabled(True)
                else:
                    self.join_btn.setEnabled(False)
                    self.cancel_btn.setEnabled(False)

        except Exception as e:
            self.info.setText(f"Failed to load match status.\n{e}")

    def join_game(self):
        user_id = safe_user_id()
        if user_id is None:
            QMessageBox.warning(self, "Warning", "Please log in first.")
            return

        try:
            res = join(user_id)
            match_id = res.get("match_id", "Unknown")
            state = res.get("status", "unknown")
            count = res.get("players", 0)

            if res.get("message") == "already joined":
                self.info.setText(
                    f"You have already joined Match {match_id}.\n"
                    f"Please wait for the match or enter Game Board."
                )
            else:
                if state == "waiting":
                    self.info.setText(
                        f"You joined Match {match_id} successfully.\n"
                        f"Current players: {count} / 4\n"
                        "Matching players..."
                    )
                elif state == "active":
                    self.info.setText(
                        f"Match {match_id} is ready.\n"
                        "4 players matched successfully.\n"
                        "You can now enter Game Board."
                    )

            self.refresh_status()

        except Exception as e:
            QMessageBox.warning(self, "Join Failed", str(e))

    def cancel_matching(self):
        user_id = safe_user_id()
        if user_id is None:
            QMessageBox.warning(self, "Warning", "Please log in first.")
            return

        try:
            res = cancel(user_id)
            msg = res.get("message", "")

            if msg == "cancelled":
                self.info.setText("Matching cancelled. You can join again later.")
            elif msg == "not in match":
                self.info.setText("You are not currently in any waiting match.")
            else:
                self.info.setText("Cancel request completed.")

            self.refresh_status()

        except Exception as e:
            QMessageBox.warning(self, "Cancel Failed", str(e))


# =========================
# Simple board widget replacement
# =========================
class MiniBoardWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("wg_panel")
        self.setStyleSheet("""
            QFrame#wg_panel {
                background: #fffafd;
                border: 2px solid #f3c4da;
                border-radius: 18px;
            }
            QLabel {
                font-size: 14px;
                color: #333333;
            }
        """)
        self.total_cells = 20

        self.layout_main = QVBoxLayout(self)
        self.layout_main.setContentsMargins(16, 16, 16, 16)

        self.title = QLabel("Game Board")
        self.title.setStyleSheet("font-size:18px; font-weight:700; color:#9d174d;")
        self.layout_main.addWidget(self.title)

        self.cells_label = QLabel("")
        self.cells_label.setWordWrap(True)
        self.layout_main.addWidget(self.cells_label)

    def update_board(self, red_pos: int, blue_pos: int):
        parts = []
        for i in range(self.total_cells):
            cell_num = i + 1
            tags = []
            if i == red_pos:
                tags.append("R")
            if i == blue_pos:
                tags.append("B")

            if tags:
                parts.append(f"[{cell_num}:{'/'.join(tags)}]")
            else:
                parts.append(f"[{cell_num}]")

        self.cells_label.setText(" ".join(parts))


# =========================
# Board page
# =========================
class BoardPage(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(16)

        # top area
        top_panel, top_root = make_panel("Game Board")
        outer.addWidget(top_panel)

        top = QHBoxLayout()
        self.back_btn = QPushButton("Back")
        self.back_btn.clicked.connect(lambda: parent.goto("start"))
        top.addWidget(self.back_btn)
        top.addStretch(1)
        top_root.addLayout(top)

        desc = QLabel("View your current match and operate for your team.")
        desc.setObjectName("wg_subtitle")
        top_root.addWidget(desc)

        # board
        self.board_widget = MiniBoardWidget()
        outer.addWidget(self.board_widget, 1)

        # info + actions
        bottom = QHBoxLayout()
        bottom.setSpacing(16)
        outer.addLayout(bottom)

        info_panel, info_root = make_panel("My Team Info")
        bottom.addWidget(info_panel, 1)

        self.info = QLabel("No active match.")
        self.info.setObjectName("wg_info")
        self.info.setWordWrap(True)
        info_root.addWidget(self.info)
        info_root.addStretch(1)

        action_panel, action_root = make_panel("Actions")
        bottom.addWidget(action_panel, 1)

        self.action_tip = QLabel("You can gain rolls or roll dice when rolls are available.")
        self.action_tip.setObjectName("wg_subtitle")
        self.action_tip.setWordWrap(True)
        action_root.addWidget(self.action_tip)

        self.gain_btn = QPushButton("Gain 1 Roll")
        self.roll_btn = QPushButton("Roll Dice")
        self.refresh_btn = QPushButton("Refresh")

        self.gain_btn.clicked.connect(self.gain_one_roll)
        self.roll_btn.clicked.connect(self.roll_dice)
        self.refresh_btn.clicked.connect(self.refresh_board)

        action_root.addWidget(self.gain_btn)
        action_root.addWidget(self.roll_btn)
        action_root.addWidget(self.refresh_btn)
        action_root.addStretch(1)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_board)
        self.timer.start(3000)

        self.refresh_board()

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_board()

    def refresh_board(self):
        user_id = safe_user_id()
        if user_id is None:
            self.info.setText("Please log in first.")
            self.gain_btn.setEnabled(False)
            self.roll_btn.setEnabled(False)
            return

        try:
            res = status(user_id)
            text, match = parse_match_info(res)

            if not match:
                self.info.setText("You have not joined a match yet.\nPlease go to Join Game first.")
                self.board_widget.update_board(0, 0)
                self.gain_btn.setEnabled(False)
                self.roll_btn.setEnabled(False)
                return

            player = current_player(match, user_id)
            if not player:
                self.info.setText("Your player information is missing in this match.")
                self.gain_btn.setEnabled(False)
                self.roll_btn.setEnabled(False)
                return

            team = player.get("team")
            if team not in ("red", "blue"):
                self.info.setText(
                    f"{text}\n\n"
                    "You are still waiting for the match to be formed."
                )
                self.board_widget.update_board(
                    match.get("red_pos", 0),
                    match.get("blue_pos", 0)
                )
                self.gain_btn.setEnabled(False)
                self.roll_btn.setEnabled(False)
                return

            self.info.setText(team_summary(match, team))
            self.board_widget.update_board(
                match.get("red_pos", 0),
                match.get("blue_pos", 0)
            )

            if match.get("status") == "active":
                self.gain_btn.setEnabled(True)
                team_rolls = match.get("red_rolls", 0) if team == "red" else match.get("blue_rolls", 0)
                self.roll_btn.setEnabled(team_rolls > 0)
            else:
                self.gain_btn.setEnabled(False)
                self.roll_btn.setEnabled(False)

        except Exception as e:
            self.info.setText(f"Failed to load board data.\n{e}")
            self.gain_btn.setEnabled(False)
            self.roll_btn.setEnabled(False)

    def gain_one_roll(self):
        user_id = safe_user_id()
        if user_id is None:
            QMessageBox.warning(self, "Warning", "Please log in first.")
            return

        try:
            res = gain_roll(user_id)
            msg = res.get("message", "Operation completed.")
            QMessageBox.information(self, "Success", msg)
            self.refresh_board()
        except Exception as e:
            QMessageBox.warning(self, "Gain Roll Failed", str(e))

    def roll_dice(self):
        user_id = safe_user_id()
        if user_id is None:
            QMessageBox.warning(self, "Warning", "Please log in first.")
            return

        try:
            res = roll(user_id)
            step = res.get("step")
            if step is not None:
                QMessageBox.information(self, "Dice Result", f"Your team moved forward by {step} step(s).")
            else:
                QMessageBox.information(self, "Dice Result", "Roll completed.")
            self.refresh_board()
        except Exception as e:
            QMessageBox.warning(self, "Roll Failed", str(e))