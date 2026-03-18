import os
import random
import sys

from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QSizePolicy, QPushButton, QApplication, QScrollArea
)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Qt, Signal
from PySide6.QtGui import QPixmap


class SingleReply(QWidget):

    liked = Signal(int)   # ⭐ 发出 reply_id

    def __init__(self, data):
        super().__init__()

        self.liked_by_user = False  # 初始状态：未点赞
        self.data = data
        self.reply_id = data["reply_id"]   # ⭐ 必须是 reply_id
        self.likes_count = data.get("likes", 0)

        # 随机头像
        avatar_id = random.randint(1, 10)
        self.avatar_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "resources", "icons",
            f"avatar{avatar_id}.png"
        )

        # 主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setAlignment(Qt.AlignTop)

        # 加载UI
        loader = QUiLoader()
        ui_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "ui",
            "single_reply.ui"
        )

        ui_file = QFile(ui_path)
        if not ui_file.open(QFile.ReadOnly):
            print(f"无法打开UI文件: {ui_path}")
            return

        self.ui = loader.load(ui_file, self)
        ui_file.close()

        self.main_layout.addWidget(self.ui)

        # 找控件
        self.name = self.ui.findChild(QLabel, "name")
        self.content = self.ui.findChild(QLabel, "label_content")
        self.time = self.ui.findChild(QLabel, "time")
        self.like_label = self.ui.findChild(QLabel, "like")
        self.avatar = self.ui.findChild(QLabel, "avatar")

        # ⭐ 点赞按钮（UI里必须有）
        self.like_btn = self.ui.findChild(QPushButton, "like_button")
        self.like_btn.setText("❤")

        if not self.like_btn:
            print("❌ 没找到 like_button，请检查 UI objectName")

        # 内容样式优化
        if self.content:
            self.content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
            self.content.setWordWrap(True)
            self.content.setMinimumWidth(200)

        for label in [self.name, self.time, self.like_label]:
            if label:
                label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # 绑定点赞
        if self.like_btn:
            self.like_btn.clicked.connect(self.handle_like)

        self.load_data()

    def load_data(self):
        self.name.setText(self.data.get("author", ""))
        self.content.setText(self.data.get("content", ""))
        self.time.setText(self.data.get("time", ""))
        self.like_label.setText(f"{self.likes_count}")

        # 初始化点赞按钮颜色
        self.like_btn.setStyleSheet("color: #555555;")  # 默认深灰

        pix = QPixmap(self.avatar_path)
        if not pix.isNull():
            self.avatar.setPixmap(
                pix.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
            self.avatar.setScaledContents(True)

    # def handle_like(self):
    #     # ⭐ 发信号给外部
    #     self.liked.emit(self.reply_id)
    #
    #     # ⭐ UI立即更新
    #     self.likes_count += 1
    #     self.like_label.setText(f"❤ {self.likes_count}")
    #
    #     # ⭐ 防止连点
    #     self.like_btn.setEnabled(False)

    def handle_like(self):
        # 切换状态
        self.liked_by_user = not self.liked_by_user

        # 更新 UI
        if self.liked_by_user:
            self.like_label.setText(f"{self.likes_count + 1}")  # 点赞
            self.like_btn.setStyleSheet("color: red;")  # 红色心
        else:
            self.like_label.setText(f"{self.likes_count}")  # 取消点赞
            self.like_btn.setStyleSheet("color: #555555;")  # 深灰色心

        # 发信号给外层，外层再调用接口
        self.liked.emit(self.reply_id)

    def sizeHint(self):
        return self.ui.sizeHint() if hasattr(self, 'ui') else super().sizeHint()


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

    # # 头像路径（请确认路径正确）
    # avatar_path = os.path.join(
    #     os.path.dirname(os.path.dirname(__file__)),
    #     "resources",
    #     "icons",
    #     "avatar1.png"
    # )
    # # 路径容错
    # if not os.path.exists(avatar_path):
    #     print(f"头像文件不存在: {avatar_path}")
    #     avatar_path = "placeholder.png"  # 替换为你的占位图路径

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