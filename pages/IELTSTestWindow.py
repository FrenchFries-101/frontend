from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtUiTools import QUiLoader
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QFile,QUrl,QTimer

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout,QPushButton

from PySide6.QtCore import Signal,QEvent
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

        #这里后期直接从接口获取url 地址
        url = "http://124.223.33.28:7777/Listening/5/test1/01_section1-1.m4a"
        self.player.setSource(QUrl(url))
        self.ui.pushButton.clicked.connect(self.play_audio)

        self.player.positionChanged.connect(self.update_slider)
        self.player.durationChanged.connect(self.set_slider_range)

        self.player.positionChanged.connect(self.update_time)
        self.player.durationChanged.connect(self.update_duration)

        self.ui.horizontalSlider.sliderMoved.connect(self.player.setPosition)

        question_widget = self.ui.scrollAreaWidgetContents

        layout = QVBoxLayout(question_widget)

        self.image_list=[
            "resources/images/IELTSTest.png",
            "resources/images/IELTSTest2.jpg"
        ]
        self.current_image_index = 0
        self.question_image = QLabel()
        self.question_image.setScaledContents(True)

        layout.addWidget(self.question_image)
        self.show_image(0)

        #创建按钮

        self.prev_btn = QPushButton("◀", self.ui.scrollArea)
        self.next_btn = QPushButton("▶", self.ui.scrollArea)

        self.prev_btn.setFixedSize(40, 60)
        self.next_btn.setFixedSize(40, 60)

        self.prev_btn.hide()
        self.next_btn.hide()

        style = """
        QPushButton{
            background-color: rgba(0,0,0,120);
            color:white;
            border:none;
            border-radius:8px;
            font-size:20px;
        }
        QPushButton:hover{
            background-color: rgba(0,0,0,180);
        }
        """

        self.prev_btn.setStyleSheet(style)
        self.next_btn.setStyleSheet(style)

        self.prev_btn.clicked.connect(self.prev_image)
        self.next_btn.clicked.connect(self.next_image)

        self.seconds = 0  # 已经过了多少秒
        self.total_seconds = 600  # 4分30秒 = 270秒
        self.ui.Timer_label.setText("00:00")

        # 创建计时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
       # self.reset_timer()

        self.total_duration = 0

        self.ui.Exit_button.clicked.connect(self.confirm_exit)
        self.ui.pushButton_3.clicked.connect(self.submit_answers)
        self.ui.scrollArea.installEventFilter(self)


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

            self.reset_timer()

            self.exit_test_signal.emit()

    def exit_direct(self):

        self.player.stop()

        self.reset_timer()

        self.exit_test_signal.emit()

    def resizeEvent(self, event):

        w = self.ui.scrollArea.width()
        h = self.ui.scrollArea.height()

        self.prev_btn.move(10, h // 2 - 30)
        self.next_btn.move(w - 50, h // 2 - 30)

    def eventFilter(self, obj, event):

        if obj == self.ui.scrollArea:

            if event.type() == QEvent.Enter:
                self.prev_btn.show()
                self.next_btn.show()

            elif event.type() == QEvent.Leave:
                self.prev_btn.hide()
                self.next_btn.hide()

        return super().eventFilter(obj, event)

    def show_image(self, index):

        if 0 <= index < len(self.image_list):
            pixmap = QPixmap(self.image_list[index])
            self.question_image.setPixmap(pixmap)
            self.current_image_index = index

    def next_image(self):

        if self.current_image_index < len(self.image_list) - 1:
            self.show_image(self.current_image_index + 1)

    def prev_image(self):

        if self.current_image_index > 0:
            self.show_image(self.current_image_index - 1)

    def reset_timer(self):

        self.seconds = 0

        self.ui.Timer_label.setText("00:00")

        self.timer.stop()
        #self.timer.start(1000)

    def showEvent(self, event):

        super().showEvent(event)

        self.reset_timer()

        self.timer.start(1000)
