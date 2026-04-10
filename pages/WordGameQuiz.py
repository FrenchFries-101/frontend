from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame
)
from PySide6.QtCore import Qt
import re


def normalize_answer(text: str) -> str:
    if text is None:
        return ""
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


class QuizChallengeDialog(QDialog):
    def __init__(self, fetch_question_callback, parent=None, target_streak=5):
        super().__init__(parent)
        self.fetch_question_callback = fetch_question_callback
        self.target_streak = target_streak
        self.current_streak = 0
        self.current_question = None
        self.current_answer = ""

        self.setWindowTitle("Answer 5 Correctly to Gain 1 Roll")
        self.setModal(True)
        self.resize(560, 360)

        self.setStyleSheet("""
            QDialog {
                background: #fffaf0;
            }

            QFrame#card {
                background: rgba(255, 255, 255, 0.96);
                border: 1px solid #f2d7a6;
                border-radius: 16px;
            }

            QLabel#title {
                font-size: 20px;
                font-weight: 700;
                color: #d97706;
                background: transparent;
            }

            QLabel#sub {
                font-size: 13px;
                color: #7c6a55;
                background: transparent;
            }

            QLabel#questionBox {
                background: rgba(255, 251, 240, 0.95);
                border: 1px solid #f4d8a8;
                border-radius: 12px;
                padding: 12px;
                color: #4b3f2f;
                font-size: 14px;
            }

            QLabel#answerHint {
                background: #fff8ea;
                border: 1px dashed #e7b85c;
                border-radius: 10px;
                padding: 8px 10px;
                color: #8a5a00;
                font-size: 13px;
                font-weight: 600;
            }

            QLabel#status {
                color: #6b4f1d;
                font-size: 13px;
                font-weight: 600;
                background: transparent;
            }

            QLineEdit {
                background: white;
                border: 1px solid #e7b85c;
                border-radius: 10px;
                min-height: 40px;
                padding: 0 12px;
                font-size: 14px;
                color: #3a3126;
            }

            QLineEdit:focus {
                border: 1px solid #d99a2b;
            }

            QPushButton {
                background: #fffaf0;
                border: 1px solid #e7b85c;
                border-radius: 12px;
                min-height: 40px;
                padding: 0 16px;
                color: #6b4f1d;
                font-size: 14px;
                font-weight: 600;
            }

            QPushButton:hover {
                background: #fff3d9;
                border: 1px solid #d99a2b;
            }

            QPushButton:pressed {
                background: #fde7b2;
            }
        """)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)

        self.card = QFrame()
        self.card.setObjectName("card")
        outer.addWidget(self.card)

        root = QVBoxLayout(self.card)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        self.title_label = QLabel("Answer 5 Correctly to Gain 1 Roll")
        self.title_label.setObjectName("title")
        self.title_label.setAlignment(Qt.AlignCenter)
        root.addWidget(self.title_label)

        self.progress_label = QLabel("Progress: 0 / 5")
        self.progress_label.setObjectName("sub")
        self.progress_label.setAlignment(Qt.AlignCenter)
        root.addWidget(self.progress_label)

        self.question_label = QLabel("Loading question...")
        self.question_label.setObjectName("questionBox")
        self.question_label.setWordWrap(True)
        root.addWidget(self.question_label)

        # =========================
        # Test
        # =========================
        self.answer_hint_label = QLabel("Test Answer: -")
        self.answer_hint_label.setObjectName("answerHint")
        self.answer_hint_label.setWordWrap(True)
        root.addWidget(self.answer_hint_label)

        self.input_label = QLabel("Type the word:")
        self.input_label.setObjectName("sub")
        root.addWidget(self.input_label)

        self.answer_input = QLineEdit()
        self.answer_input.setPlaceholderText("Enter the answer here")
        self.answer_input.returnPressed.connect(self.submit_answer)
        root.addWidget(self.answer_input)

        self.status_label = QLabel("You must answer 5 questions correctly in a row.")
        self.status_label.setObjectName("status")
        self.status_label.setWordWrap(True)
        root.addWidget(self.status_label)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.submit_btn = QPushButton("Submit")
        self.next_btn = QPushButton("Quit")
        self.submit_btn.clicked.connect(self.submit_answer)
        self.next_btn.clicked.connect(self.fail_and_close)

        btn_row.addStretch(1)
        btn_row.addWidget(self.submit_btn)
        btn_row.addWidget(self.next_btn)
        btn_row.addStretch(1)

        root.addLayout(btn_row)

        self.load_next_question()

    def load_next_question(self):
        try:
            data = self.fetch_question_callback()
        except Exception as e:
            self.status_label.setText(f"Failed to load question: {e}")
            self.submit_btn.setEnabled(False)
            self.answer_input.setEnabled(False)
            return

        self.current_question = data
        self.current_answer = data.get("answer", "")

        self.progress_label.setText(f"Progress: {self.current_streak} / {self.target_streak}")
        self.question_label.setText(
            "Type the answer according to the explanation:\n\n"
            f"{data.get('question', '-')}"
        )

        # =========================
        # Test
        # =========================
        self.answer_hint_label.setText(f"Test Answer: {self.current_answer}")

        self.answer_input.clear()
        self.answer_input.setFocus()
        self.status_label.setText("Answer this question correctly to continue.")

    def submit_answer(self):
        user_text = normalize_answer(self.answer_input.text())
        correct_text = normalize_answer(self.current_answer)

        if not user_text:
            self.status_label.setText("Please type an answer first.")
            return

        if user_text == correct_text:
            self.current_streak += 1

            if self.current_streak >= self.target_streak:
                self.status_label.setText("Great! You answered 5 correctly in a row.")
                self.accept()
                return

            self.status_label.setText(
                f"Correct! Current streak: {self.current_streak} / {self.target_streak}"
            )
            self.load_next_question()
        else:
            # Show correct answer
            self.status_label.setText(
                f"Wrong answer. Correct answer: {self.current_answer}\n"
                "The streak is reset. Click Quit to close."
            )
            self.submit_btn.setEnabled(False)
            self.answer_input.setEnabled(False)
            self.next_btn.setText("Quit")

    def fail_and_close(self):
        self.status_label.setText("Quiz closed. The streak is reset.")
        self.reject()