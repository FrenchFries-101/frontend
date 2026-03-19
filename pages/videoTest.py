import sys
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import QApplication
import os

class TestVedioWindow(QWidget):

    def __init__(self):
        super().__init__()

        # ✅ 加载 UI
        loader = QUiLoader()
        base_dir = os.path.dirname(__file__)  # pages/
        ui_path = os.path.join(base_dir, "../ui/testVideo.ui")

        ui_file = QFile(ui_path)
        ui_file.open(QFile.ReadOnly)

        self.ui = loader.load(ui_file)
        ui_file.close()

        layout = QVBoxLayout()
        layout.addWidget(self.ui)
        self.setLayout(layout)

        # ✅ 初始化播放器
        self.init_player()

        # ✅ 绑定按钮（如果你有）
        if hasattr(self.ui, "play_button"):
            self.ui.play_button.clicked.connect(self.play_video)

    def init_player(self):
        # 🎬 播放器
        self.player = QMediaPlayer()

        # 🔊 音频输出（必须）
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)

        # 📺 创建视频控件
        self.video_widget = QVideoWidget()

        # 🔁 替换 UI 里的占位 widget
        layout = self.ui.video_widget.parent().layout()
        layout.replaceWidget(self.ui.video_widget, self.video_widget)
        self.ui.video_widget.deleteLater()

        # 🔗 绑定输出
        self.player.setVideoOutput(self.video_widget)

    def play_video(self):
        video_url = "http://124.223.33.28:7777/Video/1.mp4"

        print("Playing:", video_url)

        self.player.setSource(QUrl(video_url))

        self.player.play()

app = QApplication(sys.argv)

window = TestVedioWindow()
window.resize(1000, 700)
window.show()

sys.exit(app.exec())