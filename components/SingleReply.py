import os
from PySide6.QtWidgets import (QWidget, QLabel, QApplication, QVBoxLayout,
                               QScrollArea, QSizePolicy)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Qt
from PySide6.QtGui import QPixmap
import sys
import random


class SingleReply(QWidget):
    def __init__(self, data):
        super().__init__()

        # 随机头像
        avatar_id = random.randint(1, 10)

        self.avatar_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "resources",
            "icons",
            f"avatar{avatar_id}.png"
        )

        # 1. 主布局（关键：设置布局方向和边距）
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)  # 保留少量内边距
        self.main_layout.setAlignment(Qt.AlignTop)  # 控件向上对齐，避免垂直拉伸

        # 2. 加载UI文件
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

        # layout = self.layout()
        # if layout is None:
        #     layout = QVBoxLayout(self)
        # layout.addWidget(self.ui)

        # 3. 查找子控件（从self.ui中找）
        self.name = self.ui.findChild(QLabel, "name")
        self.content = self.ui.findChild(QLabel, "label_content")
        self.time = self.ui.findChild(QLabel, "time")
        self.like = self.ui.findChild(QLabel, "like")
        self.avatar = self.ui.findChild(QLabel, "avatar")


        # 4. 关键：设置文字区域的尺寸策略，防止被压缩
        if self.content:
            # 设置水平可扩展、垂直最小尺寸（根据内容自适应高度）
            self.content.setSizePolicy(
                QSizePolicy.Expanding,  # 水平方向：尽可能占满可用空间
                QSizePolicy.Minimum  # 垂直方向：至少显示内容所需的最小高度
            )
            # 允许文字换行（避免单行文字被截断）
            self.content.setWordWrap(True)
            # 可选：设置最小宽度，保证文字区域不被挤太窄
            self.content.setMinimumWidth(200)

        # 其他文字控件也优化尺寸策略
        for label in [self.name, self.time, self.like]:
            if label:
                label.setSizePolicy(
                    QSizePolicy.Expanding,
                    QSizePolicy.Fixed  # 固定高度，不被拉伸/压缩
                )

        # 5. 加载数据
        self.load_data(data)

    def load_data(self, data):
        if all([self.name, self.content, self.time, self.like, self.avatar]):
            self.name.setText(data["author"])
            self.content.setText(data["content"])
            self.time.setText(data["time"])
            self.like.setText(f"❤ {data['likes']}")

            pix = QPixmap(self.avatar_path)
            if not pix.isNull():
                self.avatar.setPixmap(
                    pix.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
                self.avatar.setScaledContents(True)

    def sizeHint(self):
        # 可选：自定义控件的默认大小提示，避免整体被压缩
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
            # "avatar": avatar_path
        }
        reply = SingleReply(data)
        container_layout.addWidget(reply)

    window.show()
    sys.exit(app.exec())