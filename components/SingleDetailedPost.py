import os

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Signal, Qt
#
#
# class SingleDetailedPost(QWidget):
#
#     clicked = Signal(dict)
#     liked = Signal(int)   # ⭐ 新增：点赞信号
#
#     def __init__(self, post_data):
#         super().__init__()
#
#         self.post = post_data   # ⭐ 保存数据
#         self.post_id = post_data["id"]
#         self.likes_count = post_data.get("likes", 0)
#
#         loader = QUiLoader()
#
#         ui_path = os.path.join(
#             os.path.dirname(os.path.dirname(__file__)),
#             "ui",
#             "SingleDetailedPost.ui"
#         )
#
#         ui_file = QFile(ui_path)
#         ui_file.open(QFile.ReadOnly)
#
#         self.ui = loader.load(ui_file, self)
#         ui_file.close()
#
#         # 加入布局
#         layout = self.layout()
#         if layout is None:
#             layout = QVBoxLayout(self)
#         layout.addWidget(self.ui)
#
#         # 找控件
#         self.title = self.findChild(QLabel, "post_title")
#         self.author = self.findChild(QLabel, "auther_time")
#         self.likes_label = self.findChild(QLabel, "post_likes")
#         self.contents = self.findChild(QLabel, "contents")
#         self.avatar_image = self.findChild(QLabel, "label")
#
#         # ⭐ 点赞按钮（你UI里要有这个objectName）
#         self.like_btn = self.findChild(QPushButton, "like_button")
#
#         # 头像
#         pixmap = QPixmap(self.get_icon("writer.png"))
#         pixmap = pixmap.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
#         self.avatar_image.setPixmap(pixmap)
#
#         # 绑定点赞
#         if self.like_btn:
#             self.like_btn.clicked.connect(self.handle_like)
#
#         self.load_data()
#
#     def get_icon(self, name):
#         base_dir = os.path.dirname(__file__)
#         return os.path.join(base_dir, "..", "resources", "icons", name)
#
#     def handle_like(self):
#         self.like_btn.setEnabled(False)
#         self.liked.emit(self.post_id)
#
#     def load_data(self):
#         self.title.setText(self.post.get("title", ""))
#         self.contents.setText(self.post.get("content", ""))
#         self.author.setText(f'{self.post.get("author", "")}  {self.post.get("time", "")}')
#         self.likes_label.setText(f'❤ {self.likes_count}')
#
#     def mousePressEvent(self, event):
#         self.clicked.emit(self.post)
# SingleDetailedPost.py
class SingleDetailedPost(QWidget):
    clicked = Signal(dict)
    liked = Signal(int)  # 发信号给外层处理

    def __init__(self, post_data):
        super().__init__()

        self.post = post_data
        self.post_id = post_data["id"]
        self.likes_count = post_data.get("likes", 0)
        self.liked_by_user = post_data.get("liked_by_user", False)  # 支持外层传入状态

        # 加载UI
        loader = QUiLoader()
        ui_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ui", "SingleDetailedPost.ui")
        ui_file = QFile(ui_path)
        ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(ui_file, self)
        ui_file.close()

        layout = self.layout() or QVBoxLayout(self)
        layout.addWidget(self.ui)

        # 找控件
        self.title = self.findChild(QLabel, "post_title")
        self.author = self.findChild(QLabel, "auther_time")
        self.likes_label = self.findChild(QLabel, "post_likes")
        self.contents = self.findChild(QLabel, "contents")
        self.avatar_image = self.findChild(QLabel, "label")
        self.like_btn = self.findChild(QPushButton, "like_button")

        pixmap = QPixmap(self.get_icon("writer.png")).scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.avatar_image.setPixmap(pixmap)
        self.like_btn.setText("❤")

        if self.like_btn:
            self.like_btn.clicked.connect(self.handle_like)

        self.load_data()
        self.update_like_ui()  # 初始化红心颜色

    def handle_like(self):
        # 切换状态
        self.liked_by_user = not self.liked_by_user
        # 更新 UI
        self.update_like_ui()
        # 发信号给外层处理接口
        self.liked.emit(self.post_id)

    def update_like_ui(self):
        if self.liked_by_user:
            self.like_btn.setStyleSheet("color: red;")  # 红心
        else:
            self.like_btn.setStyleSheet("color: #555555;")  # 灰心

    def load_data(self):
        self.title.setText(self.post.get("title", ""))
        self.contents.setText(self.post.get("content", ""))
        self.author.setText(f'{self.post.get("author", "")}  {self.post.get("time", "")}')
        self.likes_label.setText(f'{self.likes_count}')

    def mousePressEvent(self, event):
        self.clicked.emit(self.post)

    def get_icon(self, name):
        base_dir = os.path.dirname(__file__)
        return os.path.join(base_dir, "..", "resources", "icons", name)


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    fake_post = {
        "id": 1,
        "title": "关于中南大学23级朱*柔的瓜",
        "content": "njkdsbnfajkdbnfjk",
        "author": "Andy",
        "time": "2026-03-12",
        "likes": 12
    }

    post = SingleDetailedPost(fake_post)

    # ⭐ 测试点击信号
    def on_click(data):
        print("点击帖子:", data)

    # ⭐ 测试点赞信号
    def on_like(post_id):
        print("点赞帖子 ID:", post_id)

    post.clicked.connect(on_click)
    post.liked.connect(on_like)

    post.show()

    sys.exit(app.exec())