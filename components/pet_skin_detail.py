# pet_skin_detail.py
# 皮肤详情页 —— 展示皮肤 GIF、介绍、装备按钮

import os
import tempfile
from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QFrame
)
from PySide6.QtGui import QMovie, QFont, QPixmap
from PySide6.QtCore import Qt, QSize
import requests
from service.api import BASE_URL
from service.api_pet import set_current_skin
from utils.path_utils import resource_path


def _resolve_gif(gif_url: str, skin_id: int) -> str | None:
    """解析 GIF 路径：优先后端 URL，失败则回退本地 fox_{skin_id}.gif"""
    if gif_url and gif_url.startswith("/"):
        gif_url = f"{BASE_URL}{gif_url}"

    if gif_url and (gif_url.startswith("http://") or gif_url.startswith("https://")):
        try:
            res = requests.get(gif_url, timeout=10)
            res.raise_for_status()
            _, ext = os.path.splitext(gif_url)
            tmp = tempfile.NamedTemporaryFile(suffix=ext or ".gif", delete=False)
            tmp.write(res.content)
            tmp.close()
            print(f"[SkinDetail] skin_id={skin_id} → 使用后端图片: {gif_url}")
            return tmp.name
        except Exception as e:
            print(f"[SkinDetail] 后端图片下载失败({e})，尝试本地回退")

    local_path = resource_path(f"resources/icons/fox_{skin_id}.gif")
    if os.path.exists(local_path):
        print(f"[SkinDetail] skin_id={skin_id} → 使用本地回退: {local_path}")
        return local_path

    print(f"[SkinDetail] skin_id={skin_id} → 后端和本地均无可用图片")
    return None


class PetSkinDetailPage(QWidget):
    """
    皮肤详情页

    ┌──────────────────────────────────┐
    │  ← Back          [Equip 按钮]    │
    ├──────────────────────────────────┤
    │                                  │
    │         [GIF 展示]               │
    │                                  │
    │  ┌──────────────────────────┐    │
    │  │  Fox Lv1                 │    │
    │  │  Default fox skin        │    │
    │  │  Unlock Level: 1         │    │
    │  │  Status: In Use / Owned  │    │
    │  └──────────────────────────┘    │
    └──────────────────────────────────┘

    Signals:
        back(): 返回按钮
        skin_equipped(int): 装备成功
    """

    def __init__(self, user_id: int, skin_data: dict, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.skin_data = skin_data

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        # ========== 顶部栏：返回 + 装备按钮 ==========
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        self.back_btn = QPushButton("← Back")
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.setFixedHeight(32)
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: #DFE0DF; color: #666; border: none;
                border-radius: 8px; padding: 0 16px; font-size: 13px;
            }
            QPushButton:hover { background-color: #C8C8C8; }
        """)
        top_bar.addWidget(self.back_btn)

        top_bar.addStretch()

        self.equip_btn = QPushButton()
        self.equip_btn.setCursor(Qt.PointingHandCursor)
        self.equip_btn.setFixedHeight(32)
        self._update_equip_btn()
        top_bar.addWidget(self.equip_btn)

        main_layout.addLayout(top_bar)

        # ========== GIF 展示区域 ==========
        self.gif_label = QLabel()
        self.gif_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gif_label.setFixedSize(300, 300)
        self._load_gif()
        main_layout.addWidget(self.gif_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # ========== 信息卡片 ==========
        info_card = QFrame()
        info_card.setObjectName("infoCard")
        info_card.setStyleSheet("""
            QFrame#infoCard {
                background-color: white;
                border: 1px solid #F0E0D0;
                border-radius: 15px;
            }
        """)
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(24, 20, 24, 20)
        info_layout.setSpacing(12)

        # 皮肤名称
        name_label = QLabel(self.skin_data.get("name", ""))
        name_label.setFont(QFont("", 16, QFont.Weight.Bold))
        name_label.setStyleSheet("color: #333; background: transparent;")
        info_layout.addWidget(name_label)

        # 皮肤描述
        desc_label = QLabel(self.skin_data.get("description", ""))
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; background: transparent; font-size: 13px;")
        info_layout.addWidget(desc_label)

        # 分割线
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #F0E0D0; border: none; max-height: 1px;")
        info_layout.addWidget(sep)

        # 详细信息
        unlock_level = self.skin_data.get("unlock_level", "?")
        owned = self.skin_data.get("owned", False)
        current = self.skin_data.get("current", False)

        detail_text = f"Unlock Level: {unlock_level}"
        if owned:
            detail_text += "\nStatus: Owned"
            if current:
                detail_text += " · In Use"
        else:
            detail_text += "\nStatus: Locked"

        detail_label = QLabel(detail_text)
        detail_label.setStyleSheet("color: #888; background: transparent; font-size: 12px;")
        info_layout.addWidget(detail_label)

        info_card.setFixedWidth(360)
        main_layout.addWidget(info_card, alignment=Qt.AlignmentFlag.AlignHCenter)

    def _load_gif(self):
        """加载皮肤 GIF"""
        gif_url = self.skin_data.get("gif_url", "")
        skin_id = self.skin_data.get("skin_id", 1)
        gif_path = _resolve_gif(gif_url, skin_id)

        if not gif_path:
            return

        _, ext = os.path.splitext(gif_path)
        if ext.lower() == ".gif":
            self.movie = QMovie(gif_path)
            self.movie.setScaledSize(QSize(280, 280))
            self.gif_label.setMovie(self.movie)
            self.movie.start()
        else:
            pixmap = QPixmap(gif_path)
            if not pixmap.isNull():
                self.gif_label.setPixmap(pixmap.scaled(
                    280, 280,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                ))

    def _update_equip_btn(self):
        """更新装备按钮状态"""
        owned = self.skin_data.get("owned", False)
        current = self.skin_data.get("current", False)

        if current:
            self.equip_btn.setText("Currently Using")
            self.equip_btn.setEnabled(False)
            self.equip_btn.setStyleSheet("""
                QPushButton {
                    background-color: #B3886B; color: white; border: none;
                    border-radius: 8px; padding: 0 20px; font-size: 13px;
                }
            """)
        elif owned:
            self.equip_btn.setText("Equip Skin")
            self.equip_btn.setEnabled(True)
            self.equip_btn.setStyleSheet("""
                QPushButton {
                    background-color: #B3886B; color: white; border: none;
                    border-radius: 8px; padding: 0 20px; font-size: 13px; font-weight: bold;
                }
                QPushButton:hover { background-color: #9A7055; }
            """)
            self.equip_btn.clicked.connect(self._on_equip)
        else:
            self.equip_btn.setText("Locked")
            self.equip_btn.setEnabled(False)
            self.equip_btn.setStyleSheet("""
                QPushButton {
                    background-color: #DFE0DF; color: #888; border: none;
                    border-radius: 8px; padding: 0 20px; font-size: 13px;
                }
            """)

    def _on_equip(self):
        """装备皮肤"""
        result = set_current_skin(self.user_id, self.skin_data["skin_id"])
        if result.get("success"):
            self.skin_data["current"] = True
            self._update_equip_btn()
            print(f"[SkinDetail] 已装备 skin_id={self.skin_data['skin_id']}")
        else:
            print("[SkinDetail] 装备失败:", result.get("message"))
