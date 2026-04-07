from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QMessageBox, QScrollArea, QGridLayout,
    QSizePolicy, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QPixmap, QMovie
from service.api_word_game import join, cancel, status, gain_roll, roll, get_quiz_question
from pages.WordGameQuiz import QuizChallengeDialog
from utils.path_utils import resource_path
import session


# =========================
# Theme helpers
# =========================
def apply_page_style(widget: QWidget):
    widget.setStyleSheet("""
        QWidget {
            background: transparent;
            color: #3a3126;
            font-family: "Segoe UI", "Microsoft YaHei";
            font-size: 14px;
        }

        QFrame#pageCard {
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid #f2d7a6;
            border-radius: 16px;
        }

        QLabel#pageTitle {
            font-size: 24px;
            font-weight: 700;
            color: #d97706;
            background: transparent;
        }

        QLabel#subTitle {
            font-size: 14px;
            color: #7c6a55;
            background: transparent;
        }

        QLabel#infoBox {
            background: rgba(255, 251, 240, 0.95);
            border: 1px solid #f4d8a8;
            border-radius: 12px;
            padding: 10px 12px;
            color: #4b3f2f;
        }

        QPushButton {
            background: #fffaf0;
            border: 1px solid #e7b85c;
            border-radius: 12px;
            min-height: 40px;
            max-height: 40px;
            padding: 0 16px;
            color: #6b4f1d;
            font-size: 14px;
            font-weight: 600;
            text-align: center;
        }

        QPushButton:hover {
            background: #fff3d9;
            border: 1px solid #d99a2b;
        }

        QPushButton:pressed {
            background: #fde7b2;
        }

        QPushButton:disabled {
            background: #f5f5f5;
            color: #a0a0a0;
            border: 1px solid #dddddd;
        }
    """)

def add_shadow(widget, blur=18, x=0, y=4, color_alpha=45):
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setOffset(x, y)
    shadow.setColor(Qt.black)
    shadow.color().setAlpha(color_alpha)
    widget.setGraphicsEffect(shadow)


def safe_user_id():
    if not hasattr(session, "user") or not session.user:
        return None
    return session.user.get("id")


def parse_match_info(data: dict):
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

    lines = [
        f"Match ID: {match_id}",
        f"Status: {match_status}",
        f"Players: {player_count} / 4",
    ]

    if match_status == "waiting":
        lines.append("Matching players...")
    elif match_status == "active":
        lines.append("Match started. You can enter Game Board now.")
    elif match_status == "finished":
        winner = match.get("winner_team", match.get("winner"))
        if winner:
            lines.append(f"Winner: {winner.capitalize()} Team")

    return "\n".join(lines), match


def current_player(match: dict, user_id: int):
    for p in match.get("players", []):
        if p.get("user_id") == user_id:
            return p
    return None

def get_match_value(match: dict, *keys, default=0):
    for k in keys:
        if k in match and match.get(k) is not None:
            return match.get(k)
    return default


def normalize_position(pos, total_cells):
    try:
        pos = int(pos)
    except Exception:
        pos = 0

    if pos < 0:
        pos = 0
    if pos >= total_cells:
        pos = total_cells - 1
    return pos

def team_summary(match: dict, team: str):
    players = [p for p in match.get("players", []) if p.get("team") == team]

    if team == "red":
        pos = get_match_value(match, "red_position", "red_pos", default=0)
        rolls = get_match_value(match, "red_available_rolls", "red_rolls", default=0)
    else:
        pos = get_match_value(match, "blue_position", "blue_pos", default=0)
        rolls = get_match_value(match, "blue_available_rolls", "blue_rolls", default=0)

    total_cells = get_match_value(match, "total_cells", default=84)
    winner = get_match_value(match, "winner_team", "winner", default=None)

    lines = [
        f"My Team: {team.capitalize()}",
        f"Current Position: {pos + 1} / {total_cells}",
        f"Available Rolls: {rolls}",
        "",
        "Today's contributions:"
    ]

    if players:
        for p in players:
            member_no = p.get("member_no")
            contrib = p.get("today_roll_contribute", p.get("roll_contribute", 0))

            if member_no:
                lines.append(f"Member {member_no}: {contrib}")
            else:
                lines.append(f"User {p.get('user_id')}: {contrib}")
    else:
        lines.append("No teammate data.")

    if winner:
        lines.extend(["", f"Winner: {winner.capitalize()} Team"])

    return "\n".join(lines)

def show_light_message(parent, title: str, text: str, icon=QMessageBox.Information):
    box = QMessageBox(parent)
    box.setIcon(icon)
    box.setWindowTitle(title)
    box.setText(text)
    box.setTextFormat(Qt.PlainText)
    box.setStandardButtons(QMessageBox.Ok)

    box.setStyleSheet("""
        QMessageBox {
            background: #fffaf0;
        }

        QLabel#qt_msgbox_label {
            color: #3a3126;
            font-size: 14px;
            min-width: 300px;
            max-width: 360px;
            padding: 4px 6px 4px 2px;
        }

        QLabel#qt_msgboxex_icon_label {
            min-width: 32px;
            max-width: 32px;
        }

        QPushButton {
            background: #fffaf0;
            border: 1px solid #e7b85c;
            border-radius: 10px;
            min-width: 80px;
            min-height: 32px;
            padding: 4px 12px;
            color: #6b4f1d;
            font-weight: 600;
        }

        QPushButton:hover {
            background: #fff3d9;
            border: 1px solid #d99a2b;
        }
    """)

    text_label = box.findChild(QLabel, "qt_msgbox_label")
    if text_label:
        text_label.setWordWrap(True)
        text_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

    box.exec()

# =========================
# Base page
# =========================
class BasePage(QWidget):
    def __init__(self, parent, title_text: str):
        super().__init__()
        self.parent = parent
        apply_page_style(self)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 14, 18, 14)
        outer.setSpacing(10)

        self.card = QFrame()
        self.card.setObjectName("pageCard")
        outer.addWidget(self.card)

        self.root = QVBoxLayout(self.card)
        self.root.setContentsMargins(18, 16, 18, 16)
        self.root.setSpacing(12)

        self.title = QLabel(title_text)
        self.title.setObjectName("pageTitle")
        self.title.setAlignment(Qt.AlignCenter)
        self.root.addWidget(self.title)

        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(10)
        self.root.addLayout(self.content_layout, 1)

        self.bottom_row = QHBoxLayout()
        self.bottom_row.setSpacing(10)
        self.root.addLayout(self.bottom_row)

    def add_bottom_back(self, target: str):
        self.bottom_row.addStretch(1)
        back_btn = QPushButton("Back")
        back_btn.setFixedWidth(120)
        back_btn.clicked.connect(lambda: self.parent.goto(target))
        self.bottom_row.addWidget(back_btn)


# =========================
# Page 1
# =========================
class GameMenuPage(BasePage):
    def __init__(self, parent):
        super().__init__(parent, "Word Challenge")

        btn_row = QHBoxLayout()
        btn_row.setSpacing(14)

        btn_start = QPushButton("Start Game")
        btn_instruction = QPushButton("Instruction")

        btn_start.setFixedWidth(180)
        btn_instruction.setFixedWidth(180)

        btn_row.addStretch(1)
        btn_row.addWidget(btn_start)
        btn_row.addWidget(btn_instruction)
        btn_row.addStretch(1)

        self.content_layout.addStretch(1)
        self.content_layout.addLayout(btn_row)
        self.content_layout.addStretch(1)

        btn_start.clicked.connect(lambda: parent.goto("start"))
        btn_instruction.clicked.connect(lambda: parent.goto("instruction"))


# =========================
# Instruction
# =========================
class InstructionPage(BasePage):
    def __init__(self, parent):
        super().__init__(parent, "Instruction")

        info = QLabel(
            "1. A match requires exactly 4 players.\n\n"
            "2. Before the match is formed, players may cancel matching.\n\n"
            "3. Once 4 players are matched and the game starts, the match is locked to these 4 players only.\n\n"
            "4. No new player can join or replace them until the match ends.\n\n"
            "5. Players can operate at any time.\n\n"
            "6. A team can move only when it has available rolls.\n\n"
            "7. In the current stage, 'Gain 1 Roll' is only a temporary demo action.\n\n"
            "8. The match ends only when one team reaches the goal."
        )
        info.setObjectName("infoBox")
        info.setWordWrap(True)

        self.content_layout.addWidget(info)
        self.content_layout.addStretch(1)

        self.add_bottom_back("game_menu")


# =========================
# Start Game
# =========================
class StartGamePage(BasePage):
    def __init__(self, parent):
        super().__init__(parent, "Start Game")

        btn_row = QHBoxLayout()
        btn_row.setSpacing(14)

        btn_join = QPushButton("Join Game")
        btn_board = QPushButton("Game Board")

        btn_join.setFixedWidth(180)
        btn_board.setFixedWidth(180)

        btn_row.addStretch(1)
        btn_row.addWidget(btn_join)
        btn_row.addWidget(btn_board)
        btn_row.addStretch(1)

        self.content_layout.addStretch(1)
        self.content_layout.addLayout(btn_row)
        self.content_layout.addStretch(1)

        btn_join.clicked.connect(lambda: parent.goto("join"))
        btn_board.clicked.connect(self.enter_board)

        self.add_bottom_back("game_menu")
    
    def enter_board(self):
        user_id = safe_user_id()
        if user_id is None:
            QMessageBox.warning(self, "Warning", "Please log in first.")
            return

        try:
            res = status(user_id)
            match = res.get("match")
            last_match = res.get("last_match")

            if match:
                if match.get("status") == "waiting":
                    show_light_message(
                        self,
                        "Game Board",
                        "Your match has not started yet.\nPlease wait until 4 players are matched."
                    )
                    return

                self.parent.goto("board")
                return

            if last_match and last_match.get("status") == "finished":
                self.parent.goto("board")
                return

            show_light_message(
                self,
                "Game Board",
                "You have not joined any game yet.\nPlease join a match first."
            )

        except Exception as e:
            QMessageBox.warning(self, "Game Board", f"Failed to check match status.\n{e}")


# =========================
# Join page
# =========================
class JoinPage(BasePage):
    def __init__(self, parent):
        super().__init__(parent, "Join Game")

        self.info = QLabel("You have not joined any match yet.")
        self.info.setObjectName("infoBox")
        self.info.setWordWrap(True)
        self.content_layout.addWidget(self.info)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.join_btn = QPushButton("Join")
        self.cancel_btn = QPushButton("Cancel Matching")
        self.refresh_btn = QPushButton("Refresh Status")

        self.join_btn.setFixedWidth(140)
        self.cancel_btn.setFixedWidth(170)
        self.refresh_btn.setFixedWidth(150)

        btn_row.addStretch(1)
        btn_row.addWidget(self.join_btn)
        btn_row.addWidget(self.cancel_btn)
        btn_row.addWidget(self.refresh_btn)
        btn_row.addStretch(1)

        self.content_layout.addLayout(btn_row)
        self.content_layout.addStretch(1)

        self.join_btn.clicked.connect(self.join_game)
        self.cancel_btn.clicked.connect(self.cancel_matching)
        self.refresh_btn.clicked.connect(self.refresh_status)

        self.add_bottom_back("start")

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
            self.info.setText("User not found in session.")
            self.join_btn.setEnabled(False)
            self.cancel_btn.setEnabled(False)
            self.refresh_btn.setEnabled(True)
            return

        try:
            res = status(user_id)
            text, match = parse_match_info(res)
            self.info.setText(text)

            if res.get("in_match") is False:
                self.join_btn.setEnabled(True)
                self.cancel_btn.setEnabled(False)
                self.refresh_btn.setEnabled(True)
                return

            if match:
                if match.get("status") == "waiting":
                    self.join_btn.setEnabled(False)
                    self.cancel_btn.setEnabled(True)
                    self.refresh_btn.setEnabled(True)
                else:
                    self.join_btn.setEnabled(False)
                    self.cancel_btn.setEnabled(False)
                    self.refresh_btn.setEnabled(True)

        except Exception as e:
            self.info.setText(f"Failed to load match status.\n{e}")
            self.refresh_btn.setEnabled(True)

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
                    "Please wait or enter Game Board."
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


class BoardCell(QFrame):
    def __init__(self, index: int):
        super().__init__()
        self.index = index
        self.setFixedSize(56, 56)
        self.setObjectName("boardCell")

        self.red_pawn_pixmap = QPixmap(resource_path("resources/icons/red_pawn.png"))
        self.blue_pawn_pixmap = QPixmap(resource_path("resources/icons/blue_pawn.png"))
        self.flag_pixmap = QPixmap(resource_path("resources/icons/flag.png"))

        self.setStyleSheet("""
            QFrame#boardCell {
                background: #fffaf2;
                border: 1px solid #ead3a4;
                border-radius: 14px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        self.number_label = QLabel(str(index + 1))
        self.number_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.number_label.setStyleSheet("""
            QLabel {
                font-size: 10px;
                font-weight: 700;
                color: #9c7b4b;
                background: transparent;
            }
        """)
        layout.addWidget(self.number_label)

        self.center_wrap = QHBoxLayout()
        self.center_wrap.setSpacing(3)
        self.center_wrap.setAlignment(Qt.AlignCenter)

        self.red_label = QLabel()
        self.red_label.setFixedSize(32, 32)
        self.red_label.setScaledContents(True)
        self.red_label.hide()

        self.blue_label = QLabel()
        self.blue_label.setFixedSize(32, 32)
        self.blue_label.setScaledContents(True)
        self.blue_label.hide()

        self.center_wrap.addWidget(self.red_label)
        self.center_wrap.addWidget(self.blue_label)

        layout.addStretch(1)
        layout.addLayout(self.center_wrap)
        layout.addStretch(1)

        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFixedHeight(18)

        layout.addWidget(self.icon_label)

        self.special_label = QLabel("")
        self.special_label.setAlignment(Qt.AlignCenter)
        self.special_label.setStyleSheet("""
            QLabel {
                font-size: 8px;
                font-weight: 800;
                color: #b8860b;
                background: transparent;
            }
        """)
        layout.addWidget(self.special_label)

    def _set_pawn(self, label: QLabel, pixmap: QPixmap):
        if not pixmap.isNull():
            label.setPixmap(
                pixmap.scaled(
                    32, 32,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
            )
        else:
            label.clear()

    def set_state(self, has_red=False, has_blue=False, is_start=False, is_goal=False):
        bg = "#fffaf2"
        border = "1px solid #ead3a4"
        special = ""

        if is_start:
            bg = "#fdf3dc"
            border = "2px solid #e7b85c"
            self.special_label.setText("START")

        elif is_goal:
            bg = "#fff1c9"
            border = "2px solid #d99a2b"

            if not self.flag_pixmap.isNull():
                self.icon_label.setPixmap(
                    self.flag_pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
                self.icon_label.show()

            self.special_label.setText("END")

        else:
            self.icon_label.clear()
            self.special_label.clear()
        
        self.setStyleSheet(f"""
            QFrame#boardCell {{
                background: {bg};
                border: {border};
                border-radius: 14px;
            }}
        """)

        if has_red:
            self._set_pawn(self.red_label, self.red_pawn_pixmap)
            self.red_label.show()
        else:
            self.red_label.hide()

        if has_blue:
            self._set_pawn(self.blue_label, self.blue_pawn_pixmap)
            self.blue_label.show()
        else:
            self.blue_label.hide()


class BoardWidget(QFrame):
    def __init__(self, total_cells=84, columns=10):
        super().__init__()
        self.total_cells = total_cells
        self.columns = columns
        self.cells = []

        self.setObjectName("pageCard")
        self.setStyleSheet("""
            QFrame#pageCard {
                background: rgba(255, 255, 255, 0.96);
                border: 1px solid #f0d7a6;
                border-radius: 18px;
            }
        """)
        add_shadow(self, blur=20, y=5)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 14, 14, 14)
        outer.setSpacing(10)

        title = QLabel("Board")
        title.setObjectName("pageTitle")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; color: #d97706; background: transparent;")
        outer.addWidget(title)

        self.grid_wrap = QWidget()
        outer.addWidget(self.grid_wrap)

        self.grid = QVBoxLayout(self.grid_wrap)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(8)

        self.build_board()

    def clear_board(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()
                item.layout().deleteLater()
            elif item.widget():
                item.widget().deleteLater()
        self.cells = []

    def build_board(self):
        self.clear_board()

        rows = (self.total_cells + self.columns - 1) // self.columns
        index = 0

        for row in range(rows):
            row_layout = QHBoxLayout()
            row_layout.setSpacing(8)

            row_widgets = []

            for _ in range(self.columns):
                if index < self.total_cells:
                    cell = BoardCell(index)
                    self.cells.append(cell)
                    row_widgets.append(cell)
                    index += 1
                else:
                    placeholder = QWidget()
                    placeholder.setFixedSize(56, 56)
                    placeholder.setStyleSheet("background: transparent;")
                    row_widgets.append(placeholder)

            if row % 2 == 1:
                row_widgets.reverse()

            for w in row_widgets:
                row_layout.addWidget(w)

            self.grid.addLayout(row_layout)

    def set_total_cells(self, total_cells):
        total_cells = max(1, int(total_cells))
        if total_cells != self.total_cells:
            self.total_cells = total_cells
            self.build_board()

    def update_board(self, red_pos, blue_pos, total_cells=None):
        if total_cells is not None:
            self.set_total_cells(total_cells)

        red_pos = max(0, min(int(red_pos), self.total_cells - 1))
        blue_pos = max(0, min(int(blue_pos), self.total_cells - 1))

        for i, cell in enumerate(self.cells):
            cell.set_state(
                has_red=(i == red_pos),
                has_blue=(i == blue_pos),
                is_start=(i == 0),
                is_goal=(i == self.total_cells - 1)
            )

class GameSidePanel(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("pageCard")
        self.setFixedWidth(230)
        self.setStyleSheet("""
            QFrame#pageCard {
                background: rgba(255, 255, 255, 0.97);
                border: 1px solid #f0d7a6;
                border-radius: 18px;
            }
            QLabel#sideTitle {
                font-size: 16px;
                font-weight: 700;
                color: #d97706;
                background: transparent;
            }
            QLabel#sideValue {
                font-size: 14px;
                font-weight: 700;
                color: #4b3f2f;
                background: #fff8ea;
                border: 1px solid #efd3a0;
                border-radius: 10px;
                padding: 8px 10px;
            }
        """)
        add_shadow(self, blur=20, y=5)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        title = QLabel("Match Info")
        title.setObjectName("sideTitle")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.team_label = QLabel("My Team: -")
        self.team_label.setObjectName("sideValue")
        layout.addWidget(self.team_label)

        self.roll_label = QLabel("Available Rolls: 0")
        self.roll_label.setObjectName("sideValue")
        layout.addWidget(self.roll_label)

        self.pos_label = QLabel("Position: 1")
        self.pos_label.setObjectName("sideValue")
        layout.addWidget(self.pos_label)

        self.last_dice_text = QLabel("Step: -")
        self.last_dice_text.setObjectName("sideValue")
        layout.addWidget(self.last_dice_text)

        dice_title = QLabel("Dice")
        dice_title.setObjectName("sideTitle")
        dice_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(dice_title)

        self.dice_label = QLabel()
        self.dice_label.setFixedSize(96, 96)
        self.dice_label.setAlignment(Qt.AlignCenter)
        self.dice_label.setStyleSheet("""
            QLabel {
                background: #fff8ea;
                border: 1px solid #efd3a0;
                border-radius: 16px;
            }
        """)
        layout.addWidget(self.dice_label, alignment=Qt.AlignCenter)

        self.tip_label = QLabel("Ready to roll.")
        self.tip_label.setWordWrap(True)
        self.tip_label.setAlignment(Qt.AlignCenter)
        self.tip_label.setStyleSheet("""
            QLabel {
                background: transparent;
                color: #7b6650;
                font-size: 13px;
            }
        """)
        layout.addWidget(self.tip_label)

        layout.addStretch(1)

        self.movie = None
        self.set_dice_face(1)

    def set_info(self, team: str, rolls: int, pos: int):
        self.team_label.setText(f"My Team: {team.capitalize() if team else '-'}")
        self.roll_label.setText(f"Available Rolls: {rolls}")
        self.pos_label.setText(f"Position: {pos + 1}")

    def set_tip(self, text: str):
        self.tip_label.setText(text)

    def set_dice_face(self, n: int):
        path = resource_path(f"resources/icons/dice{n}.gif")

        if self.movie is not None:
            self.movie.stop()
            self.dice_label.clear()

        self.movie = QMovie(path, parent=self.dice_label)
        self.movie.setCacheMode(QMovie.CacheAll)
        self.movie.setScaledSize(QSize(88, 88))

        self.dice_label.setMovie(self.movie)
        self.movie.start()

        # 很短暂停一下，保留第一轮后的画面
        QTimer.singleShot(250, self.movie.stop)
        self.last_dice_text.setText(f"Step: {n}")


    def play_dice_result(self, n: int):
        path = resource_path(f"resources/icons/dice{n}.gif")

        if self.movie is not None:
            self.movie.stop()
            self.dice_label.clear()

        self.movie = QMovie(path, parent=self.dice_label)
        self.movie.setCacheMode(QMovie.CacheAll)
        self.movie.setScaledSize(QSize(88, 88))

        self.dice_label.setMovie(self.movie)
        self.movie.start()
        self.last_dice_text.setText(f"Step: {n}")

# =========================
# Game Board
# =========================
class BoardPage(BasePage):
    def __init__(self, parent):
        super().__init__(parent, "Game Board")

        self.board = BoardWidget(total_cells=84, columns=10)
        self.board.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.board_scroll = QScrollArea()
        self.board_scroll.setWidgetResizable(True)
        self.board_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.board_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.board_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)
        self.board_scroll.setWidget(self.board)
        self.board_scroll.setFixedHeight(360)

        self.side_panel = GameSidePanel()
        self.side_panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        top_row = QHBoxLayout()
        top_row.setSpacing(14)
        top_row.addWidget(self.board_scroll, 1)
        top_row.addWidget(self.side_panel, 0)

        self.content_layout.addLayout(top_row)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.gain_btn = QPushButton("Gain 1 Roll")
        self.roll_btn = QPushButton("Roll Dice")
        self.refresh_btn = QPushButton("Refresh")

        self.gain_btn.setFixedWidth(140)
        self.roll_btn.setFixedWidth(140)
        self.refresh_btn.setFixedWidth(120)

        btn_row.addStretch(1)
        btn_row.addWidget(self.gain_btn)
        btn_row.addWidget(self.roll_btn)
        btn_row.addWidget(self.refresh_btn)
        btn_row.addStretch(1)

        self.content_layout.addLayout(btn_row)

        self.gain_btn.clicked.connect(self.gain_one_roll)
        self.roll_btn.clicked.connect(self.roll_dice)
        self.refresh_btn.clicked.connect(self.refresh_board)

        self.add_bottom_back("start")

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_board)
        #self.timer.start(3000)

        self.is_rolling = False
        self.last_finished_match_id = None

        self.refresh_board()

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_board()

    def refresh_board(self):
        user_id = safe_user_id()
        if user_id is None:
            self.reset_board_view("Please log in first.")
            return

        try:
            res = status(user_id)
            match = res.get("match")
            last_match = res.get("last_match")

            # 1. 当前没有 active/waiting 的比赛
            if not match:
                # 如果只是上一局结束了，可以提示一次，但不要一直拿旧棋盘渲染
                if last_match and last_match.get("status") == "finished":
                    winner_team = last_match.get("winner_team")
                    match_id = last_match.get("id")

                    if self.last_finished_match_id != match_id:
                        self.last_finished_match_id = match_id
                        if winner_team:
                            show_light_message(
                                self,
                                "Match Finished",
                                f"The match has ended.\n{winner_team.capitalize()} Team won."
                            )

                    self.reset_board_view("Previous match has finished. Please join a new game.")
                    return

                self.last_finished_match_id = None
                self.reset_board_view("You have not joined a match yet.")
                return

            player = current_player(match, user_id)
            if not player:
                self.reset_board_view("Player data not found.")
                return

            team = player.get("team")
            red_pos = match.get("red_position", match.get("red_pos", 0))
            blue_pos = match.get("blue_position", match.get("blue_pos", 0))
            total_cells = match.get("total_cells", 84)

            self.board.update_board(red_pos, blue_pos, total_cells)

            if team not in ("red", "blue"):
                if not self.is_rolling:
                    self.gain_btn.setEnabled(False)
                    self.roll_btn.setEnabled(False)
                    self.refresh_btn.setEnabled(True)
                self.side_panel.set_info("-", 0, 0)
                self.side_panel.set_tip("Waiting for 4 players.")
                return

            team_rolls = (
                match.get("red_available_rolls", match.get("red_rolls", 0))
                if team == "red"
                else match.get("blue_available_rolls", match.get("blue_rolls", 0))
            )
            team_pos = red_pos if team == "red" else blue_pos
            self.side_panel.set_info(team, team_rolls, team_pos)

            match_status = match.get("status")
            winner_team = match.get("winner_team")

            if match_status == "active":
                self.last_finished_match_id = None
                if not self.is_rolling:
                    self.gain_btn.setEnabled(True)
                    self.roll_btn.setEnabled(team_rolls > 0)
                    self.refresh_btn.setEnabled(True)
                self.side_panel.set_tip("Your team can act now.")

            elif match_status == "waiting":
                self.last_finished_match_id = None
                if not self.is_rolling:
                    self.gain_btn.setEnabled(False)
                    self.roll_btn.setEnabled(False)
                    self.refresh_btn.setEnabled(True)
                self.side_panel.set_tip("Waiting for 4 players.")

            elif match_status == "finished":
                self.gain_btn.setEnabled(False)
                self.roll_btn.setEnabled(False)
                self.refresh_btn.setEnabled(True)

                if winner_team:
                    if winner_team == team:
                        self.side_panel.set_tip("Victory! Your team won the match.")
                    else:
                        self.side_panel.set_tip(f"Match finished. {winner_team.capitalize()} Team won.")

                match_id = match.get("id")
                if self.last_finished_match_id != match_id:
                    self.last_finished_match_id = match_id
                    if winner_team == team:
                        show_light_message(self, "Victory", "Congratulations! Your team won the match.")
                    else:
                        show_light_message(
                            self,
                            "Match Finished",
                            f"The match has ended.\n{winner_team.capitalize()} Team won."
                        )

            else:
                if not self.is_rolling:
                    self.gain_btn.setEnabled(False)
                    self.roll_btn.setEnabled(False)
                    self.refresh_btn.setEnabled(True)
                self.side_panel.set_tip(f"Match status: {match_status}")

        except Exception as e:
            self.reset_board_view(f"Failed to load board data: {e}")

    def gain_one_roll(self):
        user_id = safe_user_id()
        if user_id is None:
            QMessageBox.warning(self, "Warning", "Please log in first.")
            return

        if self.is_rolling:
            return

        try:
            # 先检查今天已经成功获得了几次 roll
            res_status = status(user_id)
            match = res_status.get("match")

            if not match:
                show_light_message(
                    self,
                    "Gain 1 Roll",
                    "You are not in an active match."
                )
                return

            player = current_player(match, user_id)
            if not player:
                show_light_message(
                    self,
                    "Gain 1 Roll",
                    "Player data not found."
                )
                return

            today_count = player.get("today_roll_contribute", 0) or 0

            if today_count >= 3:
                show_light_message(
                    self,
                    "Daily Limit Reached",
                    "You have already gained 3 rolls today.\n"
                    "You cannot start another quiz today."
                )
                self.side_panel.set_tip("Daily limit reached. You have already gained 3 rolls today.")
                return

            # 还没到 3 次，允许开始答题
            quiz = QuizChallengeDialog(
                fetch_question_callback=lambda: get_quiz_question(user_id),
                parent=self,
                target_streak=5
            )

            result = quiz.exec()

            if result == QuizChallengeDialog.Accepted:
                res = gain_roll(user_id)

                if res.get("detail"):
                    raise Exception(res["detail"])

                remaining = res.get("remaining_gain_times_today")
                if remaining is None:
                    tip_text = "Great job! You answered 5 correctly and gained 1 roll."
                else:
                    tip_text = (
                        f"Great job! You answered 5 correctly and gained 1 roll.\n"
                        f"You can gain {remaining} more time(s) today."
                    )

                self.side_panel.set_tip(tip_text)
                show_light_message(self, "Success", tip_text)
                self.refresh_board()
            else:
                self.side_panel.set_tip("Quiz ended. You can challenge again.")

        except Exception as e:
            QMessageBox.warning(self, "Gain Roll Failed", str(e))

    def roll_dice(self):
        user_id = safe_user_id()
        if user_id is None:
            QMessageBox.warning(self, "Warning", "Please log in first.")
            return

        if self.is_rolling:
            return

        try:
            self.is_rolling = True
            self.gain_btn.setEnabled(False)
            self.roll_btn.setEnabled(False)
            self.refresh_btn.setEnabled(False)

            res = roll(user_id)
            step = res.get("step")

            if step is not None:
                self.side_panel.play_dice_result(step)
                self.side_panel.set_tip(f"Rolling... Step = {step}")

                def finish_roll():
                    self.is_rolling = False
                    self.refresh_board()

                QTimer.singleShot(1000, finish_roll)
            else:
                self.is_rolling = False
                self.side_panel.set_tip("Roll completed.")
                self.refresh_board()

        except Exception as e:
            self.is_rolling = False
            self.refresh_btn.setEnabled(True)
            QMessageBox.warning(self, "Roll Failed", str(e))
            self.refresh_board()

    def enter_board(self):
        user_id = safe_user_id()
        if user_id is None:
            QMessageBox.warning(self, "Warning", "Please log in first.")
            return

        try:
            res = status(user_id)
            match = res.get("match")

            if not match:
                QMessageBox.information(
                    self,
                    "Game Board",
                    "You have not joined any game yet.\nPlease join a match first."
                )
                return

            if match.get("status") == "waiting":
                QMessageBox.information(
                    self,
                    "Game Board",
                    "Your match has not started yet.\nPlease wait until 4 players are matched."
                )
                return

            self.parent.goto("board")

        except Exception as e:
            QMessageBox.warning(self, "Game Board", f"Failed to check match status.\n{e}")
    
    
    def set_action_buttons_enabled(self, enabled: bool):
        if self.is_rolling:
            self.gain_btn.setEnabled(False)
            self.roll_btn.setEnabled(False)
            self.refresh_btn.setEnabled(False)
        else:
            self.gain_btn.setEnabled(enabled)
            self.refresh_btn.setEnabled(True)
    
    def reset_board_view(self, tip="You have not joined a match yet."):
        self.board.update_board(0, 0, 84)
        self.side_panel.set_info("-", 0, 0)
        self.side_panel.last_dice_text.setText("Step: -")
        self.side_panel.set_tip(tip)

        if not self.is_rolling:
            self.gain_btn.setEnabled(False)
            self.roll_btn.setEnabled(False)
            self.refresh_btn.setEnabled(True)