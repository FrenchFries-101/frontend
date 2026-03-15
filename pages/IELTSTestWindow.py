from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtUiTools import QUiLoader
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QFile,QUrl,QTimer

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QMessageBox

from pages.ExitDialog import ExitDialog

class IELTSTestWindow(QWidget):
    exit_test_signal = Signal()

    def __init__(self):
        super().__init__()

        loader = QUiLoader()
        ui_file = QFile("ui/IELTSTest.ui")   # 你的新界面
        ui_file.open(QFile.ReadOnly)

        self.ui = loader.load(ui_file)
        ui_file.close()

        layout = QVBoxLayout()
        layout.addWidget(self.ui)
        self.setLayout(layout)

        self.player = QMediaPlayer()
        self.audio = QAudioOutput()
        self.audio.setVolume(1.0)

        self.player.setAudioOutput(self.audio)

        self.player.setSource(QUrl.fromLocalFile("audio/listening.m4a"))
        self.ui.pushButton.clicked.connect(self.play_audio)

        self.player.positionChanged.connect(self.update_slider)
        self.player.durationChanged.connect(self.set_slider_range)

        self.player.positionChanged.connect(self.update_time)
        self.player.durationChanged.connect(self.update_duration)

        self.ui.horizontalSlider.sliderMoved.connect(self.player.setPosition)

        question_widget = self.ui.scrollAreaWidgetContents

        layout = QVBoxLayout(question_widget)

        self.question_image = QLabel()
        pixmap = QPixmap("resources/images/IELTSTest.png")

        self.question_image.setPixmap(pixmap)
        self.question_image.setScaledContents(True)

        layout.addWidget(self.question_image)

        self.seconds = 0  # 已经过了多少秒
        self.total_seconds = 270  # 4分30秒 = 270秒

        # 创建计时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)  # 每1000ms = 1秒触发

        self.total_duration = 0

        self.ui.Exit_button.clicked.connect(self.confirm_exit)
        self.ui.pushButton_3.clicked.connect(self.submit_answers)

    def submit_answers(self):

        correct_answers = [
            "hotel", "friday", "london", "train", "9:30",
            "passport", "credit", "bus", "ticket", "map"
        ]

        grid = self.ui.gridLayout

        correct_count = 0

        for i in range(10):

            line_edit = getattr(self.ui, f"lineEdit_{i + 1}" if i > 0 else "lineEdit")

            user_answer = line_edit.text().strip().lower()
            correct_answer = correct_answers[i]

            answer_label = QLabel(correct_answer)

            if user_answer == correct_answer:
                answer_label.setStyleSheet("color:#10b981;font-weight:bold;")
                line_edit.setStyleSheet("border:2px solid #10b981;")
                correct_count += 1
            else:
                answer_label.setStyleSheet("color:#ef4444;font-weight:bold;")
                line_edit.setStyleSheet("border:2px solid #ef4444;")

            grid.addWidget(answer_label, i, 2)

        line_edit.setReadOnly(True)

        # 显示总分
        self.ui.Score_label.setText(f"Correct {correct_count}/10")

        # 停止计时器
        self.timer.stop()

        # 隐藏 Submit 按钮
        self.ui.pushButton_3.hide()

        # 退出按钮直接退出
        self.ui.Exit_button.clicked.disconnect()
        self.ui.Exit_button.clicked.connect(self.exit_direct)

    def play_audio(self):

        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.ui.pushButton.setText("▶")
        else:
            self.player.play()
            self.ui.pushButton.setText("⏸")

    def update_slider(self, position):
        self.ui.horizontalSlider.setValue(position)

    def set_slider_range(self, duration):
        self.ui.horizontalSlider.setRange(0, duration)

    def format_time(self, ms):
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02}:{seconds:02}"

    def update_duration(self, duration):
        self.total_duration = duration

    def update_time(self, position):

        current = self.format_time(position)
        total = self.format_time(self.total_duration)

        self.ui.label.setText(f"{current}/{total}")

    def update_timer(self):

        self.seconds += 1

        current_min = self.seconds // 60
        current_sec = self.seconds % 60

        total_min = self.total_seconds // 60
        total_sec = self.total_seconds % 60

        self.ui.Timer_label.setText(
            f"{current_min:02}:{current_sec:02}/{total_min:02}:{total_sec:02}"
        )

        if self.seconds >= self.total_seconds:
            self.timer.stop()

    def confirm_exit(self):

        dialog = ExitDialog()

        if dialog.exec():
            self.player.stop()

            self.exit_test_signal.emit()

    def exit_direct(self):

        self.player.stop()

        self.exit_test_signal.emit()