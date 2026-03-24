import random
from pathlib import Path
from datetime import datetime

import numpy as np
import sounddevice as sd
import soundfile as sf

from PySide6.QtCore import Qt, QTimer, QThread, QObject, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFrame, QScrollArea, QMessageBox
)

import session
from service.api_speaking import (
    get_sample_topics,
    start_speaking,
    finalize_speaking,
    abort_speaking,
)


class AudioRecorder:
    """
    Simple local WAV recorder based on sounddevice + soundfile.
    Records mono 16kHz float32 audio and saves it as .wav when stopped.
    """

    def __init__(self, sample_rate=16000, channels=1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.stream = None
        self.frames = []
        self.output_path = None
        self.is_recording = False
        self.submit_thread = None
        self.submit_worker = None

    def start(self, output_path: str):
        if self.is_recording:
            raise RuntimeError("Recorder is already running.")

        self.output_path = output_path
        self.frames = []

        def callback(indata, frames, time, status):
            if status:
                print("Recorder status:", status)
            self.frames.append(indata.copy())

        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="float32",
            callback=callback
        )
        self.stream.start()
        self.is_recording = True

    def stop(self):
        if not self.is_recording:
            return self.output_path

        try:
            if self.stream is not None:
                self.stream.stop()
                self.stream.close()
        finally:
            self.stream = None
            self.is_recording = False

        if not self.frames:
            raise RuntimeError("No audio was captured from microphone.")

        audio = np.concatenate(self.frames, axis=0)
        sf.write(self.output_path, audio, self.sample_rate)
        return self.output_path

    def abort(self):
        try:
            if self.stream is not None:
                self.stream.stop()
                self.stream.close()
        except Exception:
            pass
        finally:
            self.stream = None
            self.frames = []
            self.is_recording = False

class SubmitWorker(QObject):
    finished = Signal(dict)
    failed = Signal(str)

    def __init__(self, session_id, audio_path):
        super().__init__()
        self.session_id = session_id
        self.audio_path = audio_path

    def run(self):
        try:
            resp = finalize_speaking(self.session_id, self.audio_path)
            if not resp:
                self.failed.emit("Empty response from backend.")
                return

            if "error" in resp:
                self.failed.emit(str(resp["error"]))
                return

            self.finished.emit(resp)

        except Exception as e:
            self.failed.emit(str(e))

class SpeakingPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.session_id = None
        self.topic = ""
        self.current_audio_path = None
        self.has_submitted = False

        self.submit_thread = None
        self.submit_worker = None

        self.current_state = "ready"
        self.think_seconds_left = 15
        self.record_seconds_left = 60

        self.recorder = AudioRecorder(sample_rate=16000, channels=1)

        self.think_timer = QTimer(self)
        self.record_timer = QTimer(self)
        self.think_timer.timeout.connect(self.update_thinking_timer)
        self.record_timer.timeout.connect(self.update_recording_timer)

        self.init_ui()
        self.reset_page(skip_abort=True)

    def init_ui(self):
        self.setObjectName("SpeakingForm")
        self.setStyleSheet("""
        QWidget#SpeakingForm {
            background: transparent;
            font-family: "Segoe UI", "Microsoft YaHei";
            font-size: 14px;
            color: #333333;
        }

        QScrollArea {
            border: none;
            background: transparent;
        }

        QWidget#ContentWidget {
            background: transparent;
        }

        QFrame.section {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 10px;
        }

        QLabel#PageTitle {
            font-size: 20px;
            font-weight: 700;
            color: #111827;
        }

        QLabel#StateLabel {
            font-size: 13px;
            font-weight: 700;
            color: #6b7280;
            background: #f3f4f6;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 4px 10px;
        }

        QLabel#TimerLabel {
            font-size: 16px;
            font-weight: 600;
            color: #ff4f70;
        }

        QLabel.section_title {
            font-size: 15px;
            font-weight: 600;
            color: #374151;
        }

        QLabel#topic_box {
            background: #f9fafb;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 16px;
            color: #333333;
            font-size: 17px;
            line-height: 1.7;
        }

        QLabel#score_box {
            font-size: 20px;
            font-weight: 700;
            color: #ff4f70;
            background: #fff7f9;
            border: 1px solid #ffd6df;
            border-radius: 8px;
            padding: 16px;
        }

        QTextEdit {
            border: 1px solid #d1d5db;
            border-radius: 6px;
            padding: 8px 10px;
            background: white;
            color: #333333;
        }

        QTextEdit:hover {
            border: 1px solid #ffb6c3;
        }

        QTextEdit:focus {
            border: 1px solid #ff8aa1;
            background: #fffafb;
        }

        QTextEdit#feedback_text {
            border: 1px solid #e5e7eb;
            border-radius: 6px;
            padding: 8px 10px;
            background: #f9fafb;
            color: #333333;
        }

        QPushButton {
            background-color: white;
            border: 1px solid #f3b8c4;
            border-radius: 8px;
            padding: 8px 18px;
            font-size: 14px;
            font-weight: 600;
            color: #444444;
            min-height: 38px;
        }

        QPushButton:hover {
            background-color: #ffe4ea;
            border: 1px solid #ff9db2;
            color: #ff4f70;
        }

        QPushButton:pressed {
            background-color: #ffd2dc;
            border: 1px solid #ff8aa1;
        }

        QPushButton:disabled {
            background-color: #f5f5f5;
            color: #b0b0b0;
            border: 1px solid #e5e7eb;
        }

        QScrollBar:vertical {
            border: none;
            background: transparent;
            width: 6px;
        }

        QScrollBar::handle:vertical {
            background: #d1d5db;
            border-radius: 3px;
        }

        QScrollBar::handle:vertical:hover {
            background: #9ca3af;
        }

        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            height: 0;
        }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        root.addWidget(self.scroll, 1)

        self.content_widget = QWidget()
        self.content_widget.setObjectName("ContentWidget")
        self.scroll.setWidget(self.content_widget)

        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(2, 2, 2, 2)
        self.content_layout.setSpacing(12)

        header_section = QFrame()
        header_section.setProperty("class", "section")
        header_layout = QHBoxLayout(header_section)
        header_layout.setContentsMargins(16, 14, 16, 14)
        header_layout.setSpacing(12)

        self.page_title = QLabel("Speaking Practice")
        self.page_title.setObjectName("PageTitle")

        self.state_label = QLabel("Ready")
        self.state_label.setObjectName("StateLabel")
        self.state_label.setAlignment(Qt.AlignCenter)
        self.state_label.setMinimumWidth(90)
        self.state_label.setMaximumWidth(120)

        self.timer_label = QLabel("Think: 15s | Speak: 60s")
        self.timer_label.setObjectName("TimerLabel")
        self.timer_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        header_layout.addWidget(self.page_title, 4)
        header_layout.addWidget(self.state_label, 1)
        header_layout.addWidget(self.timer_label, 2)

        topic_section = QFrame()
        topic_section.setProperty("class", "section")
        topic_layout = QVBoxLayout(topic_section)
        topic_layout.setContentsMargins(16, 14, 16, 14)
        topic_layout.setSpacing(10)

        topic_title = QLabel("Topic")
        topic_title.setProperty("class", "section_title")

        self.topic_box = QLabel("Click Start to load the speaking topic.")
        self.topic_box.setObjectName("topic_box")
        self.topic_box.setWordWrap(True)
        self.topic_box.setMinimumHeight(130)
        self.topic_box.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        topic_layout.addWidget(topic_title)
        topic_layout.addWidget(self.topic_box)

        transcript_section = QFrame()
        transcript_section.setProperty("class", "section")
        transcript_layout = QVBoxLayout(transcript_section)
        transcript_layout.setContentsMargins(16, 14, 16, 14)
        transcript_layout.setSpacing(10)

        transcript_title = QLabel("Transcript")
        transcript_title.setProperty("class", "section_title")

        self.transcript_text = QTextEdit()
        self.transcript_text.setReadOnly(True)
        self.transcript_text.setPlaceholderText(
            "The transcript returned by the backend will appear here."
        )
        self.transcript_text.setMinimumHeight(140)

        transcript_layout.addWidget(transcript_title)
        transcript_layout.addWidget(self.transcript_text)

        score_section = QFrame()
        score_section.setProperty("class", "section")
        score_layout = QVBoxLayout(score_section)
        score_layout.setContentsMargins(16, 14, 16, 14)
        score_layout.setSpacing(10)

        score_title = QLabel("Score")
        score_title.setProperty("class", "section_title")

        self.score_box = QLabel("--")
        self.score_box.setObjectName("score_box")
        self.score_box.setAlignment(Qt.AlignCenter)
        self.score_box.setMinimumHeight(85)

        score_layout.addWidget(score_title)
        score_layout.addWidget(self.score_box)

        feedback_section = QFrame()
        feedback_section.setProperty("class", "section")
        feedback_layout = QVBoxLayout(feedback_section)
        feedback_layout.setContentsMargins(16, 14, 16, 14)
        feedback_layout.setSpacing(10)

        feedback_title = QLabel("AI Feedback")
        feedback_title.setProperty("class", "section_title")

        self.feedback_text = QTextEdit()
        self.feedback_text.setObjectName("feedback_text")
        self.feedback_text.setReadOnly(True)
        self.feedback_text.setPlaceholderText(
            "The feedback for this response will appear here."
        )
        self.feedback_text.setMinimumHeight(140)

        feedback_layout.addWidget(feedback_title)
        feedback_layout.addWidget(self.feedback_text)

        self.content_layout.addWidget(header_section)
        self.content_layout.addWidget(topic_section)
        self.content_layout.addWidget(transcript_section)
        self.content_layout.addWidget(score_section)
        self.content_layout.addWidget(feedback_section)
        self.content_layout.addStretch()

        button_section = QFrame()
        button_section.setProperty("class", "section")
        button_layout = QHBoxLayout(button_section)
        button_layout.setContentsMargins(16, 12, 16, 12)
        button_layout.setSpacing(12)

        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_session)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_recording_early)

        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_page)

        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.submit_audio_for_scoring)

        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.reset_button)
        button_layout.addStretch()
        button_layout.addWidget(self.submit_button)

        root.addWidget(button_section, 0)

    def set_state(self, state: str):
        self.current_state = state
        state_text = {
            "ready": "Ready",
            "thinking": "Thinking",
            "recording": "Recording",
            "uploading": "Scoring",
            "finished": "Finished",
        }.get(state, state)
        self.state_label.setText(state_text)

    def refresh_header_timer(self):
        if self.current_state == "uploading":
            self.timer_label.setText("Scoring in progress...")
        else:
            self.timer_label.setText(
                f"Think: {self.think_seconds_left}s | Speak: {self.record_seconds_left}s"
            )

    def update_buttons(self):
        self.start_button.setEnabled(self.current_state == "ready")
        self.stop_button.setEnabled(self.current_state == "recording")
        self.submit_button.setEnabled(
            self.current_state == "finished" and not self.has_submitted
        )
        self.reset_button.setEnabled(self.current_state != "uploading")

    def safe_abort_current_session(self):
        if self.session_id and not self.has_submitted and self.current_state != "ready":
            try:
                abort_speaking(self.session_id)
            except Exception:
                pass

    def reset_page(self, skip_abort=False):
        if not skip_abort:
            self.safe_abort_current_session()

        self.think_timer.stop()
        self.record_timer.stop()
        self.recorder.abort()

        self.session_id = None
        self.topic = ""
        self.current_audio_path = None
        self.has_submitted = False
        self.current_state = "ready"
        self.think_seconds_left = 15
        self.record_seconds_left = 60

        self.refresh_header_timer()
        self.topic_box.setText("Click Start to load the speaking topic.")
        self.transcript_text.clear()
        self.feedback_text.setPlainText("The feedback for this response will appear here.")
        self.score_box.setText("--")

        self.set_state("ready")
        self.update_buttons()

    def build_recording_path(self):
        recordings_dir = Path("recordings")
        recordings_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        user_id = session.user.get("id", "unknown") if session.user else "unknown"
        return str(recordings_dir / f"speaking_{user_id}_{timestamp}.wav")

    def start_session(self):
        try:
            if not session.user or "id" not in session.user:
                QMessageBox.warning(self, "Error", "User information is missing. Please log in again.")
                return

            user_id = session.user["id"]

            topic_resp = get_sample_topics()
            topics = topic_resp.get("topics", [])
            if not topics:
                QMessageBox.warning(self, "Error", "No topics returned from backend.")
                return

            self.topic = random.choice(topics)

            start_resp = start_speaking(
                student_id=str(user_id),
                topic=self.topic,
                think_seconds=15,
                answer_seconds=60
            )

            if not start_resp or "session_id" not in start_resp:
                QMessageBox.warning(self, "Start Failed", "Failed to create speaking session.")
                return

            self.session_id = start_resp["session_id"]
            self.current_audio_path = None
            self.has_submitted = False

            self.topic_box.setText(self.topic)
            self.transcript_text.clear()
            self.feedback_text.setPlainText("The feedback for this response will appear here.")
            self.score_box.setText("--")

            self.think_seconds_left = 15
            self.record_seconds_left = 60
            self.refresh_header_timer()

            self.set_state("thinking")
            self.update_buttons()
            self.think_timer.start(1000)

            print("Speaking start -> user_id:", user_id)
            print("Speaking start -> topic:", self.topic)
            print("Speaking start -> session_id:", self.session_id)

        except Exception as e:
            QMessageBox.warning(self, "Start Failed", str(e))
            self.set_state("ready")
            self.update_buttons()

    def update_thinking_timer(self):
        self.think_seconds_left -= 1
        self.refresh_header_timer()

        if self.think_seconds_left <= 0:
            self.think_timer.stop()
            self.start_recording_phase()

    def start_recording_phase(self):
        try:
            self.current_audio_path = self.build_recording_path()
            self.recorder.start(self.current_audio_path)

            self.set_state("recording")
            self.update_buttons()
            self.record_timer.start(1000)

            print("Speaking recording -> start:", self.current_audio_path)

        except Exception as e:
            QMessageBox.warning(
                self,
                "Recording Failed",
                f"Cannot access microphone.\n\n{e}\n\nPlease check microphone permission and device settings."
            )
            self.set_state("ready")
            self.update_buttons()

    def update_recording_timer(self):
        self.record_seconds_left -= 1
        self.refresh_header_timer()

        if self.record_seconds_left <= 0:
            self.record_timer.stop()
            self.finish_recording(auto_finished=True)

    def stop_recording_early(self):
        if self.current_state != "recording":
            return
        self.record_timer.stop()
        self.finish_recording(auto_finished=False)

    def finish_recording(self, auto_finished: bool):
        try:
            saved_path = self.recorder.stop()
            self.current_audio_path = saved_path

            print("Speaking recording -> saved:", self.current_audio_path)

            self.set_state("finished")
            self.update_buttons()

        except Exception as e:
            QMessageBox.warning(self, "Recording Failed", str(e))
            self.set_state("ready")
            self.update_buttons()

    def submit_audio_for_scoring(self):
        if not self.session_id:
            QMessageBox.warning(self, "Error", "No active speaking session.")
            return

        if not self.current_audio_path:
            QMessageBox.warning(self, "Error", "No recorded audio file found.")
            return

        # 防止重复点
        if self.submit_thread is not None:
            return

        self.set_state("uploading")
        self.update_buttons()

        self.submit_thread = QThread()
        self.submit_worker = SubmitWorker(self.session_id, self.current_audio_path)
        self.submit_worker.moveToThread(self.submit_thread)

        self.submit_thread.started.connect(self.submit_worker.run)

        self.submit_worker.finished.connect(self.on_submit_success)
        self.submit_worker.failed.connect(self.on_submit_failed)

        self.submit_worker.finished.connect(self.submit_thread.quit)
        self.submit_worker.failed.connect(self.submit_thread.quit)

        self.submit_worker.finished.connect(self.submit_worker.deleteLater)
        self.submit_worker.failed.connect(self.submit_worker.deleteLater)

        self.submit_thread.finished.connect(self.on_submit_thread_finished)
        self.submit_thread.finished.connect(self.submit_thread.deleteLater)

        self.submit_thread.start()

    def on_submit_success(self, resp):
        print("Speaking submit -> response:", resp)

        result = resp.get("result", {})
        if not result:
            QMessageBox.warning(self, "Submit Failed", "No result returned from backend.")
            self.set_state("finished")
            self.update_buttons()
            return

        transcript = result.get("transcript", "")
        overall_score = result.get("overall_score", "--")
        strengths = result.get("strengths", [])
        improvements = result.get("improvements", [])
        sample_better = result.get("sample_better_answer", "")

        self.transcript_text.setPlainText(transcript)
        self.score_box.setText(str(overall_score))

        feedback_lines = []

        if strengths:
            feedback_lines.append("Strengths:")
            feedback_lines.extend([f"- {item}" for item in strengths])

        if improvements:
            if feedback_lines:
                feedback_lines.append("")
            feedback_lines.append("Improvements:")
            feedback_lines.extend([f"- {item}" for item in improvements])

        if sample_better:
            if feedback_lines:
                feedback_lines.append("")
            feedback_lines.append("Sample Better Answer:")
            feedback_lines.append(sample_better)

        if not feedback_lines:
            feedback_lines.append("No feedback returned.")

        self.feedback_text.setPlainText("\n".join(feedback_lines))

        self.has_submitted = True
        self.set_state("finished")
        self.update_buttons()


    def on_submit_failed(self, error_message):
        QMessageBox.warning(self, "Submit Failed", error_message)
        self.set_state("finished")
        self.update_buttons()

    def on_submit_thread_finished(self):
        self.submit_thread = None
        self.submit_worker = None