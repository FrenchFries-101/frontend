from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QProgressBar, QGridLayout, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from components.pet_current_widget import PetWidget
from components.pet_service_widget import PetServiceWidget
from components.pet_skin_card import PetSkinCard
from service.api_pet import get_user_skins


# ============================================================
#  PetHomePage  ──  Slot 1 : 状态 + 宠物展示 + 服务
# ============================================================

class PetHomePage(QWidget):
    """
    宠物主页

    ┌──────────────────────────────────────────────────┐
    │  🐾 宠物主页                                      │
    ├──────────────────────────────────────────────────┤
    │  Lv.1   [████████░░ 活力 50/100]   ⭐ 500 积分   │
    ├──────────────┬───────────────────────────────────┤
    │              │  [食物]  [清洁]  [陪玩]             │
    │   [Pet GIF]  │  ┌───────────────────────────┐    │
    │              │  │ 投喂水       -1 积分       │    │
    │  DOGName ✏   │  └───────────────────────────┘    │
    │ "今天背单词了"│  ...                             │
    └──────────────┴───────────────────────────────────┘

    Signals:
        skin_changed(int): 当前皮肤被切换时触发（与 PetSkinPage 联动）
    """

    skin_changed = Signal(int)

    def __init__(self, user_id: int = 1, parent=None):
        super().__init__(parent)
        self.user_id = user_id

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # ========== 创建子组件 ==========
        self._create_title()
        self._create_status_bar()
        self._create_content_area()

        # ========== 按顺序添加到布局 ==========
        main_layout.addWidget(self.title_label)
        main_layout.addWidget(self.status_bar)
        main_layout.addWidget(self.content_area, stretch=1)

    # ---- 创建子组件 ----

    def _create_title(self):
        self.title_label = QLabel("🐾 宠物主页")
        self.title_label.setFont(QFont("", 18, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #B3886B; background: transparent;")

    def _create_status_bar(self):
        self.status_bar = QFrame()
        self.status_bar.setFixedHeight(50)
        self.status_bar.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #F0E0D0;
                border-radius: 12px;
            }
        """)
        bar_layout = QHBoxLayout(self.status_bar)
        bar_layout.setContentsMargins(20, 8, 20, 8)

        # 等级
        self.level_label = QLabel("Lv.1")
        self.level_label.setFont(QFont("", 13, QFont.Weight.Bold))
        self.level_label.setStyleSheet("color: #B3886B; background: transparent;")
        bar_layout.addWidget(self.level_label)

        bar_layout.addSpacing(30)

        # 活力值
        vitality_title = QLabel("活力值")
        vitality_title.setStyleSheet("color: #666; font-size: 12px; background: transparent;")
        bar_layout.addWidget(vitality_title)

        self.vitality_bar = QProgressBar()
        self.vitality_bar.setFixedWidth(200)
        self.vitality_bar.setFixedHeight(18)
        self.vitality_bar.setTextVisible(True)
        self.vitality_bar.setRange(0, 100)
        self.vitality_bar.setValue(50)
        self.vitality_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #E8E8E8;
                border-radius: 9px;
                background-color: #F5F5F5;
                text-align: center;
                font-size: 11px;
                color: #008A73;
            }
            QProgressBar::chunk {
                background-color: #008A73;
                border-radius: 9px;
            }
        """)
        bar_layout.addWidget(self.vitality_bar)

        bar_layout.addSpacing(30)

        # 积分
        self.points_label = QLabel("⭐ 500 积分")
        self.points_label.setFont(QFont("", 13, QFont.Weight.Bold))
        self.points_label.setStyleSheet("color: #F28D40; background: transparent;")
        bar_layout.addWidget(self.points_label)

        bar_layout.addStretch()

    def _create_content_area(self):
        self.content_area = QWidget()
        content_layout = QHBoxLayout(self.content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(20)

        # 左侧 —— 宠物展示（固定宽度卡片）
        pet_container = QFrame()
        pet_container.setFixedWidth(320)
        pet_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #F0E0D0;
                border-radius: 15px;
            }
        """)
        pet_layout = QVBoxLayout(pet_container)
        pet_layout.setContentsMargins(15, 15, 15, 15)

        self.pet_widget = PetWidget(self.user_id)
        pet_layout.addWidget(self.pet_widget)
        content_layout.addWidget(pet_container)

        # 右侧 —— 宠物服务
        service_container = QFrame()
        service_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #F0E0D0;
                border-radius: 15px;
            }
        """)
        service_inner = QVBoxLayout(service_container)
        service_inner.setContentsMargins(15, 15, 15, 15)

        service_title = QLabel("宠物服务")
        service_title.setFont(QFont("", 14, QFont.Weight.Bold))
        service_title.setStyleSheet("color: #333; background: transparent; margin-bottom: 5px;")
        service_inner.addWidget(service_title)

        self.service_widget = PetServiceWidget(self.user_id)
        self.service_widget.service_applied.connect(self._on_service_applied)
        service_inner.addWidget(self.service_widget, stretch=1)

        content_layout.addWidget(service_container, stretch=1)

    # ---- 事件回调 ----

    def _on_service_applied(self, result: dict):
        """服务使用成功 → 刷新状态栏"""
        self.vitality_bar.setValue(result.get("new_vitality", 50))
        self.points_label.setText(f"⭐ {result.get('new_points', 500)} 积分")


# ============================================================
#  PetSkinPage  ──  Slot 2 : 皮肤卡片网格
# ============================================================

class PetSkinPage(QWidget):
    """
    宠物皮肤页

    ┌──────────────────────────────────────────────────┐
    │  🐾 宠物皮肤                                      │
    ├──────────────────────────────────────────────────┤
    │  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
    │  │  [GIF]   │  │  [GIF]   │  │  [GIF]   │       │
    │  │ 默认狗狗  │  │ 金色狗狗  │  │ 蓝色狗狗  │       │
    │  │ 初始皮肤  │  │ 金色毛发  │  │ 蓝色毛发  │       │
    │  │[当前皮肤] │  │[设为当前] │  │[设为当前] │       │
    │  └──────────┘  └──────────┘  └──────────┘       │
    └──────────────────────────────────────────────────┘

    Signals:
        skin_changed(int): 皮肤切换成功后触发
    """

    skin_changed = Signal(int)

    def __init__(self, user_id: int = 1, parent=None):
        super().__init__(parent)
        self.user_id = user_id

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # ========== 创建子组件 ==========
        self._create_title()
        self._create_skin_grid()

        # ========== 按顺序添加到布局 ==========
        main_layout.addWidget(self.title_label)
        main_layout.addWidget(self.scroll_area, stretch=1)

    # ---- 创建子组件 ----

    def _create_title(self):
        self.title_label = QLabel("🐾 宠物皮肤")
        self.title_label.setFont(QFont("", 18, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #B3886B; background: transparent;")

    def _create_skin_grid(self):
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                width: 8px;
                background: transparent;
            }
            QScrollBar::handle:vertical {
                background: #D0C0B0;
                border-radius: 4px;
            }
        """)

        scroll_widget = QWidget()
        self.grid_layout = QGridLayout(scroll_widget)
        self.grid_layout.setSpacing(15)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        self.scroll_area.setWidget(scroll_widget)

        # 加载皮肤卡片
        self.cards = []
        self._load_skins()

    def _load_skins(self):
        skins = get_user_skins(self.user_id)
        col_count = 3

        for i, skin in enumerate(skins):
            card = PetSkinCard(skin, self.user_id, on_skin_change=self._on_skin_changed)
            # 居中对齐
            self.grid_layout.addWidget(card, i // col_count, i % col_count,
                                       Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
            self.cards.append(card)

    # ---- 事件回调 ----

    def _on_skin_changed(self, skin_id: int):
        """皮肤切换 → 刷新所有卡片状态"""
        for card in self.cards:
            if card.skin_data["skin_id"] != skin_id:
                card.skin_data["current"] = False
                card.setStyleSheet(card._get_style())
                card._update_button()
        self.skin_changed.emit(skin_id)


# ============================================================
#  测试入口
# ============================================================

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget

    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle("Pet Pages 测试")
    window.resize(900, 650)
    window.setStyleSheet("background-color: #FFF6EA;")

    tabs = QTabWidget()
    tabs.addTab(PetHomePage(user_id=1), "PetHome (Slot 1)")
    tabs.addTab(PetSkinPage(user_id=1), "PetSkin (Slot 2)")
    window.setCentralWidget(tabs)

    window.show()
    sys.exit(app.exec())
