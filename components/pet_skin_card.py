# advanced_pet_skin_test.py
import os
import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QScrollArea, QPushButton, QFrame, QHBoxLayout
)
from PySide6.QtGui import QPixmap, QMovie, QFont, QColor
from PySide6.QtCore import Qt, QSize
from service.api_pet import get_user_skins, set_current_skin
from utils.path_utils import resource_path
import requests
from service.api import BASE_URL


def _resolve_gif(gif_url: str, skin_id: int) -> str | None:
    """解析 GIF 路径：优先后端 URL，失败则回退本地 fox_{skin_id}.gif"""
    if gif_url and gif_url.startswith("/"):
        gif_url = f"{BASE_URL}{gif_url}"

    if gif_url and (gif_url.startswith("http://") or gif_url.startswith("https://")):
        try:
            res = requests.get(gif_url, timeout=10)
            res.raise_for_status()
            _, ext = os.path.splitext(gif_url)
            import tempfile
            tmp = tempfile.NamedTemporaryFile(suffix=ext or ".gif", delete=False)
            tmp.write(res.content)
            tmp.close()
            print(f"[PetSkinCard] skin_id={skin_id} → 使用后端图片: {gif_url}")
            return tmp.name
        except Exception as e:
            print(f"[PetSkinCard] 后端图片下载失败({e})，尝试本地回退")

    local_path = resource_path(f"resources/icons/fox_{skin_id}.gif")
    if os.path.exists(local_path):
        print(f"[PetSkinCard] skin_id={skin_id} → 使用本地回退: {local_path}")
        return local_path

    print(f"[PetSkinCard] skin_id={skin_id} → 后端和本地均无可用图片")
    return None


class PetSkinCard(QFrame):
    def __init__(self, skin_data: dict, user_id: int, on_skin_change=None, on_view_detail=None, parent=None):
        super().__init__(parent)
        self.skin_data = skin_data
        self.user_id = user_id
        self.on_skin_change = on_skin_change
        self.on_view_detail = on_view_detail

        # 初始化
        self.setFixedSize(220, 300)
        self.setFrameShape(QFrame.NoFrame)
        self.setObjectName("petSkinCard")
        self.setStyleSheet(self._get_style())

        # 布局
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(12, 14, 12, 12)
        layout.setSpacing(6)

        # 静态图片（解锁/锁定）
        self.img_label = QLabel()
        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_label.setStyleSheet("background: transparent; border: none;")
        self._set_skin_image()
        layout.addWidget(self.img_label)

        # 名字
        self.name_label = QLabel(self.skin_data["name"])
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setFont(QFont("", 13, QFont.Weight.Bold))
        self.name_label.setStyleSheet("color: #3B2F18; background: transparent;")
        layout.addWidget(self.name_label)

        # 简介
        self.desc_label = QLabel(self.skin_data["description"])
        self.desc_label.setWordWrap(True)
        self.desc_label.setAlignment(Qt.AlignCenter)
        self.desc_label.setStyleSheet("color: #7A6640; background: transparent; font-size: 11px;")
        layout.addWidget(self.desc_label)

        # 解锁等级
        if not self.skin_data["owned"]:
            level_hint = QLabel(f"🔒 Unlock at Lv.{self.skin_data.get('unlock_level', '?')}")
            level_hint.setAlignment(Qt.AlignCenter)
            level_hint.setStyleSheet("color: #999; font-size: 11px; background: transparent;")
            layout.addWidget(level_hint)

        layout.addSpacing(4)

        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.detail_btn = QPushButton("View Details")
        self.detail_btn.setCursor(Qt.PointingHandCursor)
        self.detail_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFF6EA; color: #B3886B; border: 1px solid #E8D5C0;
                border-radius: 8px; padding: 6px 10px; font-size: 12px; text-align: center;
            }
            QPushButton:hover { background-color: #FFE8D0; border-color: #B3886B; }
        """)
        self.detail_btn.clicked.connect(self._on_view_detail)
        btn_layout.addWidget(self.detail_btn)

        self.action_btn = QPushButton()
        self.action_btn.setCursor(Qt.PointingHandCursor)
        self._update_action_button()
        self.action_btn.clicked.connect(self._on_action)
        btn_layout.addWidget(self.action_btn)

        layout.addLayout(btn_layout)

    def _get_style(self):
        """卡片样式"""
        is_current = self.skin_data.get("current")
        if is_current:
            return """
                QFrame#petSkinCard {
                    background-color: #FFFAF5;
                    border: 2px solid #B3886B;
                    border-radius: 16px;
                }
            """
        return """
            QFrame#petSkinCard {
                background-color: #FFFFFF;
                border: 1px solid #E8D5C0;
                border-radius: 16px;
            }
            QFrame#petSkinCard:hover {
                border-color: #D4B896;
                background-color: #FFFCF8;
            }
        """

    def _set_skin_image(self):
        """根据 owned 状态加载 unlock/lock 图片"""
        skin_id = self.skin_data.get("skin_id", 1)
        prefix = "unlock" if self.skin_data.get("owned") else "lock"
        img_path = resource_path(f"resources/icons/{prefix}_{skin_id}.png")
        pixmap = QPixmap(img_path)
        if not pixmap.isNull():
            self.img_label.setPixmap(pixmap.scaled(
                150, 150,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))

    def _update_action_button(self):
        """切换按钮状态"""
        if not self.skin_data["owned"]:
            self.action_btn.hide()
        elif self.skin_data["current"]:
            self.action_btn.setText("✓ In Use")
            self.action_btn.setEnabled(False)
            self.action_btn.setStyleSheet("""
                QPushButton {
                    background-color: #B3886B; color: white; border: none;
                    border-radius: 8px; padding: 6px 10px; font-size: 12px; text-align: center;
                }
            """)
        else:
            self.action_btn.setText("Equip")
            self.action_btn.setEnabled(True)
            self.action_btn.setStyleSheet("""
                QPushButton {
                    background-color: #B3886B; color: white; border: none;
                    border-radius: 8px; padding: 6px 10px; font-size: 12px; font-weight: bold;
                    text-align: center;
                }
                QPushButton:hover { background-color: #9A7055; }
            """)
            self.action_btn.show()

    def _on_view_detail(self):
        """查看详情"""
        if self.on_view_detail:
            self.on_view_detail(self.skin_data)

    def _on_action(self):
        """装备/使用皮肤"""
        result = set_current_skin(self.user_id, self.skin_data["skin_id"])
        if result["success"]:
            self.skin_data["current"] = True
            self.setStyleSheet(self._get_style())
            self._update_action_button()
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