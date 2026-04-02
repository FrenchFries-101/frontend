from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QScrollArea, QFrame, QButtonGroup, QRadioButton,
    QSizePolicy, QMessageBox
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import Signal, QUrl, Qt, QTimer
from PySide6.QtWidgets import QSlider
from service.api import get_ted_questions, submit_ted_answer, get_ted_analysis
import session


TALK_CREDITS = {
    1: '"Computer Science Is for Everyone" Hadi Partovi · TEDxRainier\n© TED Conferences, LLC · CC BY-NC-ND 4.0',
    2: '"A Beginner\'s Guide to Quantum Computing" Shohini Ghose · TEDWomen 2018\n© TED Conferences, LLC · CC BY-NC-ND 4.0',
    3: '"Why You Should Make Useless Things" Simone Giertz · TED2018\n© TED Conferences, LLC · CC BY-NC-ND 4.0',
    4: '"The Five Deadly Engineering Sins" Myranda New · TEDxUTulsa\n© TED Conferences, LLC · CC BY-NC-ND 4.0',
    5: '"Reimagining Construction" Siobhan Cox · TEDxQueensUniversityBelfast\n© TED Conferences, LLC · CC BY-NC-ND 4.0',
    6: '"The Power of Planning Cities" Sybil Derrible · TEDxWalterPaytonCollegePrep\n© TED Conferences, LLC · CC BY-NC-ND 4.0',
    7: '"How Can We Build Greener Roads?" Jeralee Anderson · TEDxEverett\n© TED Conferences, LLC · CC BY-NC-ND 4.0',
    8: '"The Coming Transportation Revolution" Rhonda Young · TEDxSpokane\n© TED Conferences, LLC · CC BY-NC-ND 4.0',
    9: '"The Zipper Merge" Oliver Asis · TEDxWilsonPark\n© TED Conferences, LLC · CC BY-NC-ND 4.0',
    10: '"FY24 Creator Content" Michael Lim · Creator Video Source: Original creator-produced content\nAll rights reserved by the respective content creator.',
}
_TED_TRADEMARK = 'TED® and TEDx® are registered trademarks of TED Conferences, LLC. Use of these materials is for non-commercial educational purposes only.'


class TedTestWindow(QWidget):
    exit_signal = Signal()

    def __init__(self):
        super().__init__()

        self.talk_id = None
        self.questions = []
        self.answer_widgets = {}   # {question_id: widget or QButtonGroup}
        self.question_types = {}   # {question_id: type_str}
        self.submitted = False

        self._build_ui()
        self._setup_player()

    # ──────────────────────────────────────────
    #  UI construction
    # ──────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)

        # ── Header ──
        header = QHBoxLayout()
        self.exit_btn = QPushButton("← Back")
        self.exit_btn.setFixedWidth(90)
        self.exit_btn.clicked.connect(self._confirm_exit)

        self.title_label = QLabel("TED Talk")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size:17px; font-weight:bold; color:#111827;")

        self.score_label = QLabel("")
        self.score_label.setFixedWidth(120)
        self.score_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.score_label.setStyleSheet("font-size:15px; font-weight:bold; color:#10b981;")

        header.addWidget(self.exit_btn)
        header.addWidget(self.title_label, 1)
        header.addWidget(self.score_label)
        root.addLayout(header)

        # ── Audio player ──
        player_frame = QFrame()
        player_frame.setObjectName("player_frame")
        player_frame.setStyleSheet(
            "QFrame#player_frame { background:white; border:1px solid #e5e7eb; "
            "border-radius:12px; padding:6px; }"
        )
        player_layout = QHBoxLayout(player_frame)
        player_layout.setSpacing(10)

        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedSize(40, 40)
        self.play_btn.clicked.connect(self._toggle_play)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 0)
        self.slider.sliderMoved.connect(self._seek)

        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setFixedWidth(110)
        self.time_label.setStyleSheet("color:#6b7280; font-size:12px;")

        player_layout.addWidget(self.play_btn)
        player_layout.addWidget(self.slider, 1)
        player_layout.addWidget(self.time_label)
        root.addWidget(player_frame)

        # ── Attribution ──
        self.credit_label = QLabel("")
        self.credit_label.setWordWrap(True)
        self.credit_label.setAlignment(Qt.AlignLeft)
        self.credit_label.setStyleSheet(
            "font-size:11px; color:#9ca3af; padding:2px 4px 0 4px;"
        )
        root.addWidget(self.credit_label)

        # ── Questions scroll ──
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border:none;")
        self.scroll.setMinimumHeight(0)

        self.q_container = QWidget()
        self.q_layout = QVBoxLayout(self.q_container)
        self.q_layout.setSpacing(14)
        self.q_layout.setContentsMargins(0, 4, 0, 4)
        self.q_layout.addStretch()

        self.scroll.setWidget(self.q_container)
        root.addWidget(self.scroll, 1)

        # ── Submit button ──
        self.submit_btn = QPushButton("Submit Answers")
        self.submit_btn.setFixedHeight(42)
        self.submit_btn.setStyleSheet(
            "QPushButton { background:#3b82f6; color:white; border-radius:10px; "
            "font-size:15px; font-weight:bold; }"
            "QPushButton:hover { background:#2563eb; }"
            "QPushButton:pressed { background:#1d4ed8; }"
        )
        self.submit_btn.clicked.connect(self._submit_answers)
        root.addWidget(self.submit_btn)

    def _setup_player(self):
        self.player = QMediaPlayer()
        self.audio_out = QAudioOutput()
        self.audio_out.setVolume(1.0)
        self.player.setAudioOutput(self.audio_out)
        self.player.positionChanged.connect(self._on_position)
        self.player.durationChanged.connect(self._on_duration)

    # ──────────────────────────────────────────
    #  Data loading
    # ──────────────────────────────────────────

    def set_data(self, talk_id, title, audio_path):
        self.talk_id = talk_id
        self.submitted = False
        self.score_label.setText("")
        self.submit_btn.show()
        self.submit_btn.setEnabled(True)
        self.title_label.setText(title)

        credit = TALK_CREDITS.get(talk_id, "")
        if credit:
            self.credit_label.setText(credit + "\n" + _TED_TRADEMARK)
        else:
            self.credit_label.setText("")

        # reset player
        self.player.stop()
        self.player.setSource(QUrl(audio_path))
        self.play_btn.setText("▶")
        self.slider.setValue(0)
        self.time_label.setText("00:00 / 00:00")

        # load questions
        data = get_ted_questions(talk_id)
        if not data:
            QMessageBox.warning(self, "Error", "Failed to load questions.")
            return
        self.questions = data.get("questions", [])
        self._build_questions()

    def _build_questions(self):
        # clear old widgets (keep the trailing stretch)
        while self.q_layout.count() > 1:
            item = self.q_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.answer_widgets.clear()
        self.question_types.clear()

        # group by type for section headers
        type_labels = {
            "sentence_completion": "Sentence Completion",
            "true_false_not_given": "True / False / Not Given",
            "multiple_choice": "Multiple Choice",
        }
        last_type = None
        q_num = 1

        for q in self.questions:
            qtype = q["question_type"]
            qid = q["question_id"]
            self.question_types[qid] = qtype

            # section header when type changes
            if qtype != last_type:
                header = QLabel(type_labels.get(qtype, qtype))
                header.setStyleSheet(
                    "font-size:13px; font-weight:bold; color:#6b7280; "
                    "padding:6px 0 2px 0;"
                )
                self.q_layout.insertWidget(self.q_layout.count() - 1, header)
                last_type = qtype

            card = self._make_question_card(q_num, q)
            self.q_layout.insertWidget(self.q_layout.count() - 1, card)
            q_num += 1

    def _make_question_card(self, num, q):
        qid = q["question_id"]
        qtype = q["question_type"]

        card = QFrame()
        card.setObjectName("talk_card")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(8)

        # question text
        q_label = QLabel(f"Q{num}. {q['question_text']}")
        q_label.setWordWrap(True)
        q_label.setStyleSheet("font-size:14px; color:#111827;")
        card_layout.addWidget(q_label)

        # answer area by type
        if qtype == "sentence_completion":
            line = QLineEdit()
            line.setPlaceholderText("Type your answer…")
            line.setStyleSheet(
                "border:1px solid #e5e7eb; border-radius:6px; padding:6px; font-size:13px;"
            )
            card_layout.addWidget(line)
            self.answer_widgets[qid] = line

        elif qtype == "true_false_not_given":
            btn_row = QHBoxLayout()
            btn_row.setSpacing(8)
            group = QButtonGroup(card)
            group.setExclusive(True)
            for text in ["True", "False", "Not Given"]:
                btn = QPushButton(text)
                btn.setCheckable(True)
                btn.setFixedHeight(34)
                btn.setStyleSheet(self._tfng_style())
                group.addButton(btn)
                btn_row.addWidget(btn)
            btn_row.addStretch()
            card_layout.addLayout(btn_row)
            self.answer_widgets[qid] = group

        elif qtype == "multiple_choice":
            options = q.get("options") or []
            group = QButtonGroup(card)
            group.setExclusive(True)
            for opt in options:
                rb = QRadioButton(opt)
                rb.setStyleSheet("font-size:13px; color:#374151; padding:2px 0;")
                group.addButton(rb)
                card_layout.addWidget(rb)
            self.answer_widgets[qid] = group

        # placeholder for result feedback (added after submit)
        result_label = QLabel("")
        result_label.setObjectName(f"result_{qid}")
        result_label.setWordWrap(True)
        result_label.setStyleSheet("font-size:12px;")
        card_layout.addWidget(result_label)

        return card

    # ──────────────────────────────────────────
    #  Submit & results
    # ──────────────────────────────────────────

    def _submit_answers(self):
        if self.submitted:
            return

        answer_list = []
        for q in self.questions:
            qid = q["question_id"]
            qtype = self.question_types[qid]
            widget = self.answer_widgets.get(qid)
            answer = self._get_answer(qtype, widget)
            answer_list.append(answer)

        user_id = session.user["id"]
        result = submit_ted_answer(user_id, self.talk_id, answer_list)
        if not result:
            QMessageBox.warning(self, "Error", "Failed to submit answers.")
            return

        self.submitted = True
        self.submit_btn.setEnabled(False)

        correct = result["correct_num"]
        total = result["total_num"]
        self.score_label.setText(f"Score: {correct}/{total}")

        # show per-question feedback
        feedback_map = {f["question_id"]: f["is_correct"] for f in result["feedback"]}
        for q in self.questions:
            qid = q["question_id"]
            is_correct = feedback_map.get(qid, False)
            self._apply_feedback(q, is_correct, answer_list[self.questions.index(q)])

    def _get_answer(self, qtype, widget):
        if widget is None:
            return ""
        if qtype == "sentence_completion":
            return widget.text().strip()
        else:  # QButtonGroup
            checked = widget.checkedButton()
            if checked is None:
                return ""
            text = checked.text()
            # For MC, extract just the letter (e.g. "A. Reform" → "A")
            if qtype == "multiple_choice" and ". " in text:
                return text.split(".")[0].strip()
            return text

    def _apply_feedback(self, q, is_correct, user_answer):
        qid = q["question_id"]
        qtype = self.question_types[qid]
        widget = self.answer_widgets.get(qid)

        color = "#10b981" if is_correct else "#ef4444"

        # lock input widgets
        if qtype == "sentence_completion" and widget:
            widget.setReadOnly(True)
            border_color = "#10b981" if is_correct else "#ef4444"
            widget.setStyleSheet(
                f"border:2px solid {border_color}; border-radius:6px; "
                f"padding:6px; font-size:13px;"
            )
        elif widget:
            for btn in widget.buttons():
                btn.setEnabled(False)
                if qtype == "true_false_not_given" and btn.isChecked():
                    bg = "#d1fae5" if is_correct else "#fee2e2"
                    border = "#10b981" if is_correct else "#ef4444"
                    btn.setStyleSheet(
                        f"QPushButton {{ border:2px solid {border}; border-radius:6px; "
                        f"background:{bg}; padding:4px 12px; }}"
                    )

        # result label: show correct answer + explanation if wrong
        result_label = self.q_container.findChild(QLabel, f"result_{qid}")
        if result_label:
            if is_correct:
                result_label.setText("✔ Correct")
                result_label.setStyleSheet("font-size:12px; color:#10b981; font-weight:bold;")
            else:
                analysis = get_ted_analysis(self.talk_id, qid)
                explanation = analysis.get("Analysis", "") if analysis else ""
                correct_ans = q.get("answer", "")
                msg = f"✘ Correct answer: {correct_ans}"
                if explanation:
                    msg += f"\n{explanation}"
                result_label.setText(msg)
                result_label.setStyleSheet("font-size:12px; color:#ef4444;")

    # ──────────────────────────────────────────
    #  Audio player helpers
    # ──────────────────────────────────────────

    def _toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.play_btn.setText("▶")
        else:
            self.player.play()
            self.play_btn.setText("⏸")

    def _seek(self, pos):
        self.player.setPosition(pos)

    def _on_position(self, pos):
        self.slider.setValue(pos)
        self.time_label.setText(
            f"{self._fmt(pos)} / {self._fmt(self.player.duration())}"
        )

    def _on_duration(self, dur):
        self.slider.setRange(0, dur)

    @staticmethod
    def _fmt(ms):
        s = ms // 1000
        return f"{s // 60:02}:{s % 60:02}"

    # ──────────────────────────────────────────
    #  Exit
    # ──────────────────────────────────────────

    def _confirm_exit(self):
        self.player.stop()
        self.play_btn.setText("▶")
        self.exit_signal.emit()

    # ──────────────────────────────────────────
    #  Styles
    # ──────────────────────────────────────────

    @staticmethod
    def _tfng_style():
        return (
            "QPushButton { border:1px solid #e5e7eb; border-radius:6px; "
            "padding:4px 12px; background:white; font-size:13px; }"
            "QPushButton:hover { border:1px solid #3b82f6; background:#eff6ff; }"
            "QPushButton:checked { border:2px solid #3b82f6; background:#dbeafe; font-weight:bold; }"
        )
