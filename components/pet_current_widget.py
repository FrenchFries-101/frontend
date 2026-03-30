# pet_widget.py
import os
from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QLineEdit, QPushButton
)
from PySide6.QtGui import QMovie, QFont, QPixmap
from PySide6.QtCore import Qt, QTimer, QSize
from service.api_petshow import get_current_skin, modify_pet_name, get_pet_quote


class PetWidget(QWidget):
    """可复用宠物展示组件"""

    def __init__(self, user_id: int, parent=None):
        super().__init__(parent)
        self.user_id = user_id

        # 布局
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignTop)
        self.layout.setSpacing(10)

        # GIF
        self.gif_label = QLabel()
        self.gif_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.gif_label)

        # 名字
        self.name_input = QLineEdit()
        self.name_input.setAlignment(Qt.AlignCenter)
        self.name_input.setFont(QFont("", 12, QFont.Bold))
        self.layout.addWidget(self.name_input)

        # 修改名字按钮
        self.modify_btn = QPushButton("修改名字")
        self.modify_btn.clicked.connect(self.modify_name)
        self.layout.addWidget(self.modify_btn)

        # 语录
        self.quote_label = QLabel()
        self.quote_label.setAlignment(Qt.AlignCenter)
        self.quote_label.setWordWrap(True)
        self.layout.addWidget(self.quote_label)

        # 定时刷新语录
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_quote)
        self.timer.start(5000)  # 每5秒刷新

        # 初始化数据
        self.load_pet_data()

    def load_pet_data(self):
        """加载宠物数据"""
        data = get_current_skin(self.user_id)
        self.skin_id = data.get("skin_id")
        self.name_input.setText(data.get("name", ""))
        self.gif_url = data.get("gif_url")
        self.set_gif(self.gif_url)
        self.update_quote()

    def set_gif(self, gif_path: str):
        """加载图片/GIF，自动识别格式"""
        if not os.path.isabs(gif_path):
            gif_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), gif_path)
        if not os.path.exists(gif_path):
            print(f"[PetWidget] 文件不存在: {gif_path}")
            return
        _, ext = os.path.splitext(gif_path)
        if ext.lower() == ".gif":
            self.movie = QMovie(gif_path)
            self.movie.setScaledSize(QSize(150, 150))
            self.gif_label.setMovie(self.movie)
            self.movie.start()
        else:
            pixmap = QPixmap(gif_path)
            if not pixmap.isNull():
                self.gif_label.setPixmap(pixmap.scaled(
                    150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def modify_name(self):
        """修改宠物名字"""
        new_name = self.name_input.text()
        result = modify_pet_name(self.user_id, new_name)
        if result["success"]:
            print(result["message"])
        else:
            print("修改失败:", result["message"])

    def update_quote(self):
        """刷新语录"""
        quote = get_pet_quote(self.user_id)
        self.quote_label.setText(quote.get("content", ""))




# pet_widget.py （在原来的 PetWidget 后面添加 main 测试函数）
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QMainWindow, QScrollArea, QWidget, QVBoxLayout
    app = QApplication(sys.argv)
    # 主窗口
    window = QMainWindow()
    window.setWindowTitle("PetWidget Demo")
    window.resize(400, 600)

    # 中心Widget + 布局
    central_widget = QWidget()
    layout = QVBoxLayout(central_widget)
    layout.setContentsMargins(10, 10, 10, 10)
    layout.setSpacing(20)

    # 滚动区域
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setWidget(central_widget)
    window.setCentralWidget(scroll)


    user_id = 1
    pet_widget = PetWidget(user_id=user_id)
    layout.addWidget(pet_widget)
    window.show()
    sys.exit(app.exec())