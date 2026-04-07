from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer


class SpellDialog(QDialog):
    """Dialog that shows a Chinese definition and asks the user to spell the English word."""

    def __init__(self, word_data: dict, parent=None):
        super().__init__(parent)
        self.word_data = word_data
        self.setWindowTitle("Spell the Word")
        self.setFixedSize(380, 250)
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet("""
            QDialog {
                background: white;
                font-family: "Microsoft YaHei";
            }
            QLabel#hint_label {
                font-size: 11px;
                color: #bbb;
                letter-spacing: 0.5px;
            }
            QLabel#cn_label {
                font-size: 15px;
                color: #333;
                font-weight: 600;
            }
            QLineEdit#spell_input {
                border: 1px solid #ffc0cb;
                border-radius: 8px;
                padding: 7px 12px;
                font-size: 14px;
                color: #333;
            }
            QLineEdit#spell_input:focus {
                border: 2px solid #ff6b81;
            }
            QPushButton#check_btn {
                background: #ff6b81;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
                min-width: 100px;
                max-width: 140px;
                height: 34px;
            }
            QPushButton#check_btn:hover {
                background: #ff4d6d;
            }
            QPushButton#check_btn:pressed {
                background: #e63952;
            }
            QPushButton#check_btn:disabled {
                background: #fca5a5;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 20, 28, 20)
        layout.setSpacing(10)

        # Hint text
        hint = QLabel("What is the English word for:")
        hint.setObjectName("hint_label")
        layout.addWidget(hint)

        # Chinese definition
        cn_label = QLabel(self.word_data.get("chinese", ""))
        cn_label.setObjectName("cn_label")
        cn_label.setWordWrap(True)
        layout.addWidget(cn_label)

        # Input field
        self.input = QLineEdit()
        self.input.setObjectName("spell_input")
        self.input.setPlaceholderText("Type the English word…")
        self.input.returnPressed.connect(self._check)
        layout.addWidget(self.input)

        # Feedback label
        self.feedback_label = QLabel("")
        self.feedback_label.setAlignment(Qt.AlignCenter)
        self.feedback_label.setMinimumHeight(18)
        layout.addWidget(self.feedback_label)

        # Check button — centered, compact
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 10, 0, 0)  # 上面留点呼吸感

        self.check_btn = QPushButton("Check")
        self.check_btn.setObjectName("check_btn")
        self.check_btn.setFixedSize(160, 44)
        self.check_btn.setStyleSheet("""
        QPushButton {
            background-color: #fb7185;
            color: white;
            border-radius: 12px;
            padding: 0px;
            text-align: center;
            font-weight: bold;
        }
        """)



        self.check_btn.clicked.connect(self._check)

        btn_row.addStretch()
        btn_row.addWidget(self.check_btn, alignment=Qt.AlignCenter)
        btn_row.addStretch()



        layout.addLayout(btn_row)

        self.input.setFocus()

    def _check(self):
        user_ans = self.input.text().strip().lower()
        correct_ans = self.word_data.get("english", "").strip().lower()

        if user_ans == correct_ans:
            self.feedback_label.setText("✓  Correct!")
            self.feedback_label.setStyleSheet(
                "color: #22c55e; font-weight: bold; font-size: 13px;"
            )
            self.check_btn.setEnabled(False)
            self.input.setReadOnly(True)
            QTimer.singleShot(700, self.accept)
        else:
            self.feedback_label.setText("✗  Incorrect — try again.")
            self.feedback_label.setStyleSheet(
                "color: #ef4444; font-weight: bold; font-size: 13px;"
            )
            self.input.clear()
            self.input.setFocus()
