# advanced_pet_skin_test.py
import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QScrollArea, QPushButton, QFrame
)
from PySide6.QtGui import QPixmap, QMovie, QFont, QColor
from PySide6.QtCore import Qt, QSize
from service.api_pet import get_user_skins, set_current_skin


class PetSkinCard(QFrame):
    def __init__(self, skin_data: dict, user_id: int, on_skin_change=None, parent=None):
        super().__init__(parent)
        self.skin_data = skin_data
        self.user_id = user_id
        self.on_skin_change = on_skin_change

        # 初始化
        self.setFixedSize(220, 320)
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet(self._get_style())

        # 布局
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # GIF/图片
        self.gif_label = QLabel()
        self.gif_label.setAlignment(Qt.AlignCenter)
        self._set_gif(self.skin_data["gif_url"])
        layout.addWidget(self.gif_label)

        # 名字
        self.name_label = QLabel(self.skin_data["name"])
        self.name_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        self.name_label.setFont(font)
        layout.addWidget(self.name_label)

        # 简介
        self.desc_label = QLabel(self.skin_data["description"])
        self.desc_label.setWordWrap(True)
        self.desc_label.setAlignment(Qt.AlignCenter)
        self.desc_label.setStyleSheet("color: #4A4A4A;")
        layout.addWidget(self.desc_label)

        # 按钮
        self.button = QPushButton()
        self.button.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.button)
        self._update_button()
        self.button.clicked.connect(self._on_click)

    def _get_style(self):
        """卡片样式"""
        border_color = "#B3886B" if self.skin_data.get("current") else "#DFE0DF"
        bg_color = "#FFF6EA" if self.skin_data.get("current") else "white"
        return f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: 15px;
            }}
        """

    def _set_gif(self, gif_path: str):
        """加载 GIF 动画"""
        self.movie = QMovie(gif_path)
        self.movie.setScaledSize(QSize(150, 150))
        self.gif_label.setMovie(self.movie)
        self.movie.start()

    def _update_button(self):
        """按钮状态"""
        if not self.skin_data["owned"]:
            self.button.setText("Locked")
            self.button.setEnabled(False)
            self.button.setStyleSheet(
                "background-color: #DFE0DF; color: #888888; border-radius: 8px; padding: 5px; margin: 0px; text-align: center;")
        elif self.skin_data["current"]:
            self.button.setText("In Use")
            self.button.setEnabled(False)
            self.button.setStyleSheet(
                "background-color: #B3886B; color: white; border-radius: 8px; padding: 5px; margin: 0px; text-align: center;")
        else:
            self.button.setText("Set as Current")
            self.button.setEnabled(True)
            self.button.setStyleSheet(
                "background-color: #FFF6EA; color: #B3886B; border: 1px solid #B3886B; border-radius: 8px; padding: 5px; margin: 0px; text-align: center;")

    def _on_click(self):
        print("点击按钮")
        result = set_current_skin(self.user_id, self.skin_data["skin_id"])
        if result["success"]:
            self.skin_data["current"] = True
            self.setStyleSheet(self._get_style())
            self._update_button()
            if self.on_skin_change:
                self.on_skin_change(self.skin_data["skin_id"])
        else:
            print("切换失败:", result["message"])




class PetSkinTestPage(QWidget):
    """测试页面，带滚动条"""
    def __init__(self, user_id=1):
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle("高级 PetSkinCard 测试页")
        self.resize(260, 600)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # 标题
        title = QLabel("宠物皮肤")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("", 14, QFont.Bold))
        layout.addWidget(title)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_widget)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # 创建皮肤卡片
        self.cards = []
        skins = get_user_skins(self.user_id)
        for skin in skins:
            card = PetSkinCard(skin, self.user_id, on_skin_change=self.on_skin_change)
            self.scroll_layout.addWidget(card)
            self.cards.append(card)

    def on_skin_change(self, skin_id):
        """切换皮肤后刷新其他卡片状态"""
        for card in self.cards:
            if card.skin_data["skin_id"] != skin_id:
                card.skin_data["current"] = False
                card.setStyleSheet(card._get_style())
                card._update_button()
        print(f"当前皮肤切换为: {skin_id}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = PetSkinTestPage()
    w.show()
    sys.exit(app.exec())