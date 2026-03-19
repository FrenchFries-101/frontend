import os
import random
import sys
from utils.path_utils import resource_path
from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QSizePolicy, QPushButton, QApplication, QScrollArea
)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Qt, Signal, QSize
from PySide6.QtGui import QPixmap, QIcon


# ⭐ 关键改动版 SingleReply

class SingleReply(QWidget):

    liked = Signal(int)

    def __init__(self, data):
        super().__init__()


        self.liked_by_user = False
        self.data = data
        self.reply_id = data["reply_id"]
        self.likes_count = data.get("likes", 0)

        self.setProperty("reply_id", self.reply_id)

        self.heart_gray = self.get_icon("heart.png")
        self.heart_red = self.get_icon("heart2.png")

        avatar_id = random.randint(1, 10)

        self.avatar_path = resource_path(
            os.path.join("resources", "icons", f"avatar{avatar_id}.png")
        )
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setAlignment(Qt.AlignTop)

        # 加载UI
        loader = QUiLoader()
        ui_path = resource_path(
            os.path.join("ui", "single_reply.ui")
        )

        ui_file = QFile(ui_path)
        ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(ui_file, self)
        ui_file.close()

        self.main_layout.addWidget(self.ui)

        # 找控件
        self.name = self.ui.findChild(QLabel, "name")
        self.content = self.ui.findChild(QLabel, "label_content")
        self.time = self.ui.findChild(QLabel, "time")
        self.like_label = self.ui.findChild(QLabel, "like")
        self.avatar = self.ui.findChild(QLabel, "avatar")
        self.like_btn = self.ui.findChild(QPushButton, "like_button")

        self.like_btn.setStyleSheet("""
        QPushButton {
            background-color: pink;
            color: white;
            border-radius: 8px;
        }
                QPushButton:hover {
            background-color: #ff9aa2;   /* 悬停稍深 */
        }
        
        QPushButton:pressed {
            background-color: #ff6f91;   /* 点击时更深 */
        }
        """)

        self.like_btn.setFixedSize(40, 15)
        self.like_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        # self.like_btn.setIcon(QIcon(QPixmap(self.heart_red)))
        # 图标大小适配按钮（留边距，避免溢出）
        # self.like_btn.setIconSize(QSize(10, 10))
        self.like_btn.setFlat(True)
        self.like_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        #只绑定一次（你之前绑了两次）
        self.like_btn.clicked.connect(self.handle_like)

        # 内容优化
        self.content.setWordWrap(True)
        self.content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        # 初始化UI
        self.load_data()
        self.update_like_ui()

    def load_data(self):
        self.name.setText(self.data.get("author", ""))
        self.content.setText(self.data.get("content", ""))
        self.time.setText(self.data.get("time", ""))
        # self.like_label.setText(f'❤ {self.likes_count}')
        self.like_label.setText(str(self.likes_count))

        pix = QPixmap(self.avatar_path)
        if not pix.isNull():
            self.avatar.setPixmap(
                pix.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )

    def handle_like(self):
        self.like_btn.setEnabled(False)  # 防止连点
        self.liked.emit(self.reply_id)

    def update_like_ui(self):
        if self.liked_by_user:
            self.like_btn.setIcon(QIcon(self.heart_red))
        else:
            self.like_btn.setIcon(QIcon(self.heart_gray))

    def get_icon(self, name):
        path = resource_path(os.path.join("resources", "icons", name))

        if not os.path.exists(path):
            print(f"图标不存在: {path}")

        return path


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 测试窗口
    window = QWidget()
    window.setWindowTitle("SingleReply 测试")
    window.resize(600, 800)  # 设置窗口初始大小

    main_layout = QVBoxLayout(window)
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    container = QWidget()
    container_layout = QVBoxLayout(container)
    # 关键：容器布局也设置向上对齐，避免评论项之间的空白拉伸
    container_layout.setAlignment(Qt.AlignTop)
    scroll.setWidget(container)
    main_layout.addWidget(scroll)

    # 创建测试评论（包含长文本，验证换行）
    for i in range(10):
        data = {
            "author": f"用户{i + 1}",
            "content": f"第{i + 1}条评论：哈哈哈哈哈哈，这是一段比较长的评论内容，用来测试文字是否会被压缩或者截断，确保能正常换行显示！",
            "time": f"2026-03-13 1{i}:00",
            "likes": i * 2,
            "reply_id":1
            # "avatar": avatar_path
        }
        reply = SingleReply(data)
        container_layout.addWidget(reply)

    window.show()
    sys.exit(app.exec())