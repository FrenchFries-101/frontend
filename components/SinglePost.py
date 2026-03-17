import os

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Signal


class SinglePost(QWidget):

    clicked = Signal(dict)

    def __init__(self, post_data):
        super().__init__()

        loader = QUiLoader()

        ui_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "ui",
            "single_post.ui"
        )

        ui_file = QFile(ui_path)
        ui_file.open(QFile.ReadOnly)

        self.ui = loader.load(ui_file, self)
        ui_file.close()

        self.post = post_data

        # 将 ui 加到 widget 布局
        layout = self.layout()
        if layout is None:
            layout = QVBoxLayout(self)
        layout.addWidget(self.ui)

        self.title = self.findChild(QLabel, "post_title")
        self.author = self.findChild(QLabel, "auther_time")
        self.likes = self.findChild(QLabel, "post_likes")

        self.load_data()

    def load_data(self):

        self.title.setText(self.post["title"])
        self.author.setText(f'{self.post["author"]}  {self.post["time"]}')
        self.likes.setText(f'❤ {self.post["likes"]}')

    def mousePressEvent(self, event):

        self.clicked.emit(self.post)



if __name__ == "__main__":

    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # 假数据
    fake_post = {
        "title": "关于中南大学23级朱*柔的瓜",
        "author": "Andy",
        "time": "2026-03-12",
        "likes": 100
    }

    # 创建组件
    post = SinglePost(fake_post)

    # 测试点击信号
    def test_click(data):
        print("点击了帖子:", data)

    post.clicked.connect(test_click)

    post.show()

    sys.exit(app.exec())