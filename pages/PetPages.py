from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QGridLayout, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from components.pet_current_widget import PetWidget
from components.pet_service_widget import PetServiceWidget
from components.pet_skin_card import PetSkinCard
from components.pet_skin_detail import PetSkinDetailPage
from components.pet_status_widget import PetStatusWidget
from service.api_pet import get_user_skins


# ============================================================
#  PetHomePage  ──  Slot 1 : 状态 + 宠物展示 + 服务
# ============================================================

class PetHomePage(QWidget):
    """
    宠物主页

    ┌──────────────────────────────────────────────────┐
    │  🐾 宠物主页                                      │
    ├──────────────┬───────────────────────────────────┤
    │  [Status]    │                                   │
    │  等级/经验/活力│  [食物]  [清洁]  [陪玩]             │
    ├──────────────┤  ┌───────────────────────────┐    │
    │              │  │ 投喂水       -1 积分       │    │
    │   [Pet GIF]  │  └───────────────────────────┘    │
    │  DOGName ✏   │  ...                             │
    │ "今天背单词了"│                                   │
    └──────────────┴───────────────────────────────────┘

    Signals:
        skin_changed(int): 当前皮肤被切换时触发（与 PetSkinPage 联动）
    """

    skin_changed = Signal(int)

    def __init__(self, user_id: int = 1, parent=None):
        super().__init__(parent)
        self.user_id = user_id

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ========== 滚动区域 ==========
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: #FFF6EA; }
            QScrollBar:vertical {
                width: 8px; background: transparent;
            }
            QScrollBar::handle:vertical {
                background: #D0C0B0; border-radius: 4px; min-height: 30px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: #FFF6EA;")
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        # ========== 创建子组件 ==========
        self._create_title()
        self._create_content_area()

        # ========== 按顺序添加到布局 ==========
        content_layout.addWidget(self.title_label)
        content_layout.addWidget(self.content_area)
        content_layout.addStretch()

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

    # ---- 创建子组件 ----

    def _create_title(self):
        self.title_label = QLabel("🐾 Pet Home")
        self.title_label.setFont(QFont("", 18, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #B3886B; background: transparent;")

    def _create_content_area(self):
        self.content_area = QWidget()
        content_layout = QHBoxLayout(self.content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(20)

        # ====== 左侧：状态 + 宠物展示 ======
        left_panel = QWidget()
        left_panel.setFixedWidth(380)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(15)

        # 左上 —— 状态面板
        status_container = QFrame()
        status_container.setObjectName("statusContainer")
        status_container.setStyleSheet("""
            QFrame#statusContainer {
                background-color: white;
                border: 1px solid #F0E0D0;
                border-radius: 15px;
            }
        """)
        status_layout = QVBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)

        self.status_widget = PetStatusWidget(self.user_id)
        status_layout.addWidget(self.status_widget)
        left_layout.addWidget(status_container)

        # 左下 —— 宠物展示
        pet_container = QFrame()
        pet_container.setObjectName("petContainer")
        pet_container.setStyleSheet("""
            QFrame#petContainer {
                background-color: white;
                border: 1px solid #F0E0D0;
                border-radius: 15px;
            }
        """)
        pet_layout = QVBoxLayout(pet_container)
        pet_layout.setContentsMargins(15, 15, 15, 15)

        self.pet_widget = PetWidget(self.user_id)
        pet_layout.addWidget(self.pet_widget)
        left_layout.addWidget(pet_container, stretch=1)

        content_layout.addWidget(left_panel)

        # ====== 右侧：宠物服务 ======
        service_container = QFrame()
        service_container.setObjectName("serviceContainer")
        service_container.setStyleSheet("""
            QFrame#serviceContainer {
                background-color: white;
                border: 1px solid #F0E0D0;
                border-radius: 15px;
            }
        """)
        service_inner = QVBoxLayout(service_container)
        service_inner.setContentsMargins(15, 15, 15, 15)

        service_title = QLabel("Pet Services")
        service_title.setFont(QFont("", 14, QFont.Weight.Bold))
        service_title.setStyleSheet("color: #333; background: transparent; margin-bottom: 5px;")
        service_inner.addWidget(service_title)

        self.service_widget = PetServiceWidget(self.user_id)
        self.service_widget.service_applied.connect(self._on_service_applied)
        service_inner.addWidget(self.service_widget, stretch=1)

        content_layout.addWidget(service_container, stretch=1)

    # ---- 事件回调 ----

    def _on_service_applied(self, result: dict):
        """服务使用成功 → 刷新状态组件"""
        self.status_widget.refresh()


# ============================================================
#  PetSkinPage  ──  Slot 2 : 皮肤卡片网格
# ============================================================

class PetSkinPage(QWidget):
    """
    宠物皮肤页 —— 网格列表 + 详情页切换

    Signals:
        skin_changed(int): 皮肤切换成功后触发
    """

    skin_changed = Signal(int)

    def __init__(self, user_id: int = 1, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.detail_page = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ========== 列表层 ==========
        self.list_widget = QWidget()
        self.list_widget.setStyleSheet("background: #FFF6EA;")
        list_layout = QVBoxLayout(self.list_widget)
        list_layout.setContentsMargins(20, 20, 20, 20)
        list_layout.setSpacing(15)

        self.title_label = QLabel("🐾 Pet Skins")
        self.title_label.setFont(QFont("", 18, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #B3886B; background: transparent;")
        list_layout.addWidget(self.title_label)

        self._create_skin_grid(list_layout)

        main_layout.addWidget(self.list_widget)

    def _create_skin_grid(self, parent_layout):
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: #FFF6EA;
            }
            QScrollArea > QWidget > QWidget {
                background: #FFF6EA;
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
        scroll_widget.setStyleSheet("background: #FFF6EA;")
        self.grid_layout = QGridLayout(scroll_widget)
        self.grid_layout.setSpacing(15)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        self.scroll_area.setWidget(scroll_widget)

        self.cards = []
        self._load_skins()

        parent_layout.addWidget(self.scroll_area, stretch=1)

    def _load_skins(self):
        skins = get_user_skins(self.user_id)
        col_count = 3

        for i, skin in enumerate(skins):
            card = PetSkinCard(
                skin, self.user_id,
                on_skin_change=self._on_skin_changed,
                on_view_detail=self._show_detail
            )
            self.grid_layout.addWidget(card, i // col_count, i % col_count,
                                       Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
            self.cards.append(card)

    # ---- 页面切换 ----

    def _show_detail(self, skin_data: dict):
        """显示皮肤详情页"""
        self.list_widget.hide()

        if self.detail_page is not None:
            self.detail_page.deleteLater()

        self.detail_page = PetSkinDetailPage(self.user_id, skin_data)
        self.detail_page.back_btn.clicked.connect(self._back_to_list)
        self.layout().addWidget(self.detail_page)

    def _back_to_list(self):
        """返回列表"""
        if self.detail_page:
            self.detail_page.deleteLater()
            self.detail_page = None
        self.list_widget.show()
        self._refresh_cards()

    def _refresh_cards(self):
        """刷新所有卡片状态"""
        for card in self.cards:
            card.setStyleSheet(card._get_style())
            card._update_action_button()

    # ---- 事件回调 ----

    def _on_skin_changed(self, skin_id: int):
        """皮肤切换 → 刷新所有卡片状态"""
        for card in self.cards:
            if card.skin_data["skin_id"] != skin_id:
                card.skin_data["current"] = False
                card.setStyleSheet(card._get_style())
                card._update_action_button()
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
