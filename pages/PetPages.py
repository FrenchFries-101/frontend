from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QGridLayout, QSizePolicy, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from components.pet_current_widget import PetWidget
from components.pet_service_widget import PetServiceWidget
from components.pet_skin_card import PetSkinCard
from components.pet_skin_detail import PetSkinDetailPage
from components.pet_status_widget import PetStatusWidget, get_pet_status
from components.restaurant_widget import RestaurantWidget
from components.city_card_widget import CityCardWidget
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
    points_changed = Signal(int)

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
        """服务使用成功 → 刷新状态组件 + 通知积分变化"""
        self.status_widget.refresh()
        new_points = result.get("new_points")
        if new_points is not None:
            self.points_changed.emit(int(new_points))


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
    points_changed = Signal(int)

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
#  PetExplorePage  ──  Slot 3 : 探索页（活力值 > 40 解锁）
# ============================================================

C_PRIMARY = "#B3886B"
C_BG     = "#FFF6EA"
C_BORDER = "#F0E0D0"

VITALITY_THRESHOLD = 40


class PetExplorePage(QWidget):
    """
    宠物探索页 —— 美食推荐 + 景点天气卡片
    当宠物活力值 > {VITALITY_THRESHOLD} 时解锁，否则显示锁定提示。

    Signals:
        vitality_changed(float): 活力值变化时触发
    """

    vitality_changed = Signal(float)

    def __init__(self, user_id: int = 1, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self._is_unlocked = False

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

        self._scroll_content = QWidget()
        self._scroll_content.setStyleSheet("background: #FFF6EA;")
        content_layout = QVBoxLayout(self._scroll_content)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(24)

        # ========== 标题 + 小标题 ==========
        self._create_title()
        content_layout.addWidget(self.title_label)
        content_layout.addSpacing(4)
        content_layout.addWidget(self.subtitle_label)
        content_layout.addSpacing(8)

        # ========== 锁定遮罩（初始可见） ==========
        self.lock_overlay = QFrame()
        self.lock_overlay.setObjectName("lockOverlay")
        self.lock_overlay.setFixedHeight(280)
        self.lock_overlay.setStyleSheet("""
            QFrame#lockOverlay {
                background: white;
                border: 1px solid #F0E0D0;
                border-radius: 18px;
            }
        """)
        shadow = QGraphicsDropShadowEffect(self.lock_overlay)
        shadow.setOffset(0, 3)
        shadow.setBlurRadius(16)
        shadow.setColor(Qt.GlobalColor.lightGray)
        self.lock_overlay.setGraphicsEffect(shadow)

        lock_layout = QVBoxLayout(self.lock_overlay)
        lock_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lock_layout.setSpacing(12)

        self._lock_icon = QLabel()
        self._lock_icon.setFixedSize(72, 72)
        self._lock_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lock_icon.setText("\U0001F512")
        self._lock_icon.setFont(QFont("", 40))
        self._lock_icon.setStyleSheet("background: transparent;")
        lock_layout.addWidget(self._lock_icon, alignment=Qt.AlignmentFlag.AlignCenter)

        self._lock_title = QLabel("Vitality Too Low")
        self._lock_title.setFont(QFont("", 16, QFont.Weight.Bold))
        self._lock_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lock_title.setStyleSheet(f"color: {C_PRIMARY}; background: transparent;")
        lock_layout.addWidget(self._lock_title)

        self._lock_desc = QLabel(f"Your pet needs vitality > {VITALITY_THRESHOLD} to explore.\nFeed your pet to restore vitality!")
        self._lock_desc.setFont(QFont("", 11))
        self._lock_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lock_desc.setWordWrap(True)
        self._lock_desc.setStyleSheet("color: #999; background: transparent;")
        lock_layout.addWidget(self._lock_desc)

        content_layout.addWidget(self.lock_overlay)

        # ========== 内容区域（初始隐藏） ==========
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background: transparent;")
        content_inner = QVBoxLayout(self.content_widget)
        content_inner.setContentsMargins(0, 0, 0, 0)
        content_inner.setSpacing(24)

        # --- 美食推荐卡片 ---
        food_container = QFrame()
        food_container.setObjectName("foodContainer")
        food_container.setStyleSheet("""
            QFrame#foodContainer {
                background-color: white;
                border: none;
                border-radius: 16px;
            }
        """)
        shadow_food = QGraphicsDropShadowEffect(food_container)
        shadow_food.setOffset(0, 2)
        shadow_food.setBlurRadius(14)
        shadow_food.setColor(Qt.GlobalColor.lightGray)
        food_container.setGraphicsEffect(shadow_food)
        food_inner = QVBoxLayout(food_container)
        food_inner.setContentsMargins(0, 0, 0, 0)

        self.restaurant_widget = RestaurantWidget()
        food_inner.addWidget(self.restaurant_widget)
        content_inner.addWidget(food_container)

        # --- 景点/天气卡片 ---
        city_container = QFrame()
        city_container.setObjectName("cityContainer")
        city_container.setStyleSheet("""
            QFrame#cityContainer {
                background-color: white;
                border: none;
                border-radius: 16px;
            }
        """)
        shadow_city = QGraphicsDropShadowEffect(city_container)
        shadow_city.setOffset(0, 2)
        shadow_city.setBlurRadius(14)
        shadow_city.setColor(Qt.GlobalColor.lightGray)
        city_container.setGraphicsEffect(shadow_city)
        city_inner = QVBoxLayout(city_container)
        city_inner.setContentsMargins(0, 0, 0, 0)

        self.city_widget = CityCardWidget()
        self.city_widget.setMinimumHeight(280)
        city_inner.addWidget(self.city_widget)
        content_inner.addWidget(city_container)

        self.content_widget.hide()
        content_layout.addWidget(self.content_widget)
        content_layout.addStretch()

        scroll.setWidget(self._scroll_content)
        main_layout.addWidget(scroll)

        # ========== 初始检查活力值 ==========
        self._check_vitality()

    # ---- 创建标题 ----

    def _create_title(self):
        self.title_label = QLabel("\U0001F332 Pet Explore")
        self.title_label.setFont(QFont("", 18, QFont.Weight.Bold))
        self.title_label.setStyleSheet(f"color: {C_PRIMARY}; background: transparent;")

        self.subtitle_label = QLabel(
            "Discover tasty food and beautiful sights around you"
        )
        self.subtitle_label.setFont(QFont("", 11))
        self.subtitle_label.setStyleSheet("color: #999; background: transparent; margin-bottom: 5px;")

    # ---- 活力值检查 ----

    def _check_vitality(self):
        data = get_pet_status(self.user_id)
        vitality = data.get("vitality", 0)
        self._update_lock_state(vitality)

    def _update_lock_state(self, vitality: float):
        if vitality > VITALITY_THRESHOLD:
            if not self._is_unlocked:
                self._is_unlocked = True
                self.lock_overlay.hide()
                self.content_widget.show()
        else:
            if self._is_unlocked:
                self._is_unlocked = False
                self.lock_overlay.show()
                self.content_widget.hide()
            # 更新锁定描述中的当前活力值
            self._lock_desc.setText(
                f"Current vitality: {int(vitality)} / 100\n"
                f"Your pet needs vitality > {VITALITY_THRESHOLD} to explore.\n"
                f"Feed your pet to restore vitality!"
            )
        self.vitality_changed.emit(vitality)

    def refresh(self):
        """外部调用：刷新活力值状态"""
        self._check_vitality()
        if self._is_unlocked:
            self.restaurant_widget.refresh()
            self.city_widget.refresh()


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
    tabs.addTab(PetExplorePage(user_id=1), "Explore (Slot 3)")
    window.setCentralWidget(tabs)

    window.show()
    sys.exit(app.exec())
