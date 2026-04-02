# components/pet_service_widget.py
# 宠物服务组件：分类按钮栏 + 服务列表（含冷却倒计时）
#最新

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame
)
from PySide6.QtCore import Qt, QTimer, Signal

from service.api_pet_service import (
    get_service_categories,
    get_services_by_category,
    apply_service,
    get_remaining_cooldown,
)

DEFAULT_USER_ID = 1


class PetServiceWidget(QWidget):
    """
    宠物服务组件

    结构：
    ┌─────────────────────────────┐
    │  [食物]  [清洁]  [陪玩]      │  ← 分类按钮栏
    ├─────────────────────────────┤
    │  ┌───────────────────────┐  │
    │  │ 投喂水      -1 积分    │  │  ← 服务按钮列表
    │  └───────────────────────┘  │
    │  ┌───────────────────────┐  │
    │  │ 投喂萝卜    -2 积分    │  │
    │  └───────────────────────┘  │
    │  ...                        │
    └─────────────────────────────┘

    Signals:
        service_applied(dict): 服务使用成功后触发，传递接口返回数据
    """

    service_applied = Signal(dict)

    def __init__(self, user_id: int = DEFAULT_USER_ID, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # 当前选中的分类
        self._current_category_id = None
        # 服务按钮列表 {service_id: QPushButton}
        self._service_buttons = {}
        # 冷却计时器
        self._cooldown_timer = QTimer()
        self._cooldown_timer.timeout.connect(self._refresh_cooldowns)
        self._cooldown_timer.start(1000)  # 每秒刷新一次冷却

        # ========== 创建子组件 ==========
        self._create_category_bar()
        self._create_service_list()

        # ========== 按顺序添加到布局 ==========
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self.category_bar)
        layout.addWidget(self.service_list, stretch=1)

        # 加载分类
        self._load_categories()

    # ============ 创建子组件 ============

    def _create_category_bar(self):
        """创建一级分类按钮栏"""
        self.category_bar = QWidget()
        self.category_bar.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.category_bar_layout = QHBoxLayout(self.category_bar)
        self.category_bar_layout.setContentsMargins(0, 0, 0, 0)
        self.category_bar_layout.setSpacing(8)
        self._cat_buttons = []

    def _create_service_list(self):
        """创建服务按钮列表容器"""
        self.service_list = QWidget()
        self.service_list.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.service_list_layout = QVBoxLayout(self.service_list)
        self.service_list_layout.setContentsMargins(0, 0, 0, 0)
        self.service_list_layout.setSpacing(8)
        self.service_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    # ============ 加载数据 ============

    def _load_categories(self):
        """加载分类按钮"""
        # 清空旧按钮
        for btn in self._cat_buttons:
            self.category_bar_layout.removeWidget(btn)
            btn.deleteLater()
        self._cat_buttons.clear()

        categories = get_service_categories()
        for cat in categories:
            btn = QPushButton(cat["name"])
            btn.setFixedHeight(36)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setProperty("category_id", cat["category_id"])
            btn.setStyleSheet(self._cat_btn_style(active=False))
            btn.clicked.connect(lambda checked, c=cat: self._on_category_clicked(c["category_id"]))
            self.category_bar_layout.addWidget(btn)
            self._cat_buttons.append(btn)

        # 默认选中第一个
        if categories:
            self._on_category_clicked(categories[0]["category_id"])

    def _on_category_clicked(self, category_id: int):
        """切换分类"""
        self._current_category_id = category_id

        # 更新分类按钮样式
        for btn in self._cat_buttons:
            is_active = btn.property("category_id") == category_id
            btn.setStyleSheet(self._cat_btn_style(active=is_active))

        # 加载该分类下的服务
        self._load_services(category_id)

    def _load_services(self, category_id: int):
        """加载某分类下的服务卡片列表"""
        # 清空旧卡片
        for sid, card in self._service_buttons.items():
            self.service_list_layout.removeWidget(card)
            card.deleteLater()
        self._service_buttons.clear()

        services = get_services_by_category(category_id)
        for svc in services:
            card = self._create_service_button(svc)
            self.service_list_layout.addWidget(card)
            self._service_buttons[svc["service_id"]] = card

        # 立即刷新冷却状态
        self._refresh_cooldowns()

    def _create_service_button(self, svc: dict) -> QFrame:
        """创建单个服务卡片，左侧名称+活力值，右侧积分消耗"""
        card = QFrame()
        card.setFixedHeight(52)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setProperty("service_id", svc["service_id"])
        card.setProperty("cooldown_seconds", svc["cooldown_seconds"])
        card.setStyleSheet(self._svc_card_style(active=True))
        card.setObjectName("serviceCard")

        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(14, 8, 14, 8)
        card_layout.setSpacing(0)

        # 左侧：服务名 + 活力值提升提示
        left_layout = QVBoxLayout()
        left_layout.setSpacing(2)

        name_label = QLabel(svc["name"])
        name_label.setStyleSheet("color: #333333; font-size: 14px; font-weight: bold; background: transparent;")
        left_layout.addWidget(name_label)

        effect_label = QLabel(f"+{svc['vitality_effect']} Vitality")
        effect_label.setStyleSheet("color: #008A73; font-size: 11px; background: transparent;")
        left_layout.addWidget(effect_label)
        card_layout.addLayout(left_layout)

        card_layout.addStretch()

        # 右侧：积分消耗
        cost_label = QLabel(f"-{svc['points_cost']} Points")
        cost_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        cost_label.setStyleSheet("color: #F28D40; font-size: 15px; font-weight: bold; background: transparent;")
        card_layout.addWidget(cost_label)

        # 点击事件
        card.mousePressEvent = lambda event, s=svc: self._on_service_clicked(s["service_id"]) if event.button() == Qt.MouseButton.LeftButton else None

        return card

    # ============ 服务点击 ============

    def _on_service_clicked(self, service_id: int):
        """点击服务卡片"""
        card = self._service_buttons.get(service_id)
        if not card:
            return
        remaining = get_remaining_cooldown(self.user_id, service_id)
        if remaining > 0:
            return  # 冷却中不响应
        result = apply_service(self.user_id, service_id)
        if result["success"]:
            self.service_applied.emit(result)
            self._refresh_cooldowns()
        else:
            self._show_error_on_card(card, result.get("message", "操作失败"))

    def _show_error_on_card(self, card: QFrame, message: str):
        """在卡片上临时显示错误提示，2 秒后自动恢复"""
        effect_label = card.layout().itemAt(0).layout().itemAt(1).widget()
        effect_label.setText(message)
        effect_label.setStyleSheet("color: #E76F51; font-size: 11px; background: transparent;")
        card.setStyleSheet(self._svc_card_style(active=True, cooldown=False, error=True))
        # 2 秒后恢复
        QTimer.singleShot(2000, lambda: self._restore_card_from_error(card))

    # ============ 冷却倒计时 ============

    def _refresh_cooldowns(self):
        """每秒刷新所有服务卡片的冷却状态"""
        for sid, card in self._service_buttons.items():
            remaining = get_remaining_cooldown(self.user_id, sid)
            cooldown_total = card.property("cooldown_seconds")

            if remaining > 0:
                card.setEnabled(False)
                card.setCursor(Qt.CursorShape.ForbiddenCursor)
                card.setStyleSheet(self._svc_card_style(active=False, cooldown=True))
                # 更新卡片文本：隐藏活力值，显示冷却
                self._set_card_cooldown(card, remaining)
            else:
                card.setEnabled(True)
                card.setCursor(Qt.CursorShape.PointingHandCursor)
                card.setStyleSheet(self._svc_card_style(active=True, cooldown=False))
                self._restore_card_text(card, sid)

    # ============ 按钮文本 ============

    def _set_card_cooldown(self, card: QFrame, remaining: int):
        """将卡片内容切换为冷却提示"""
        # 卡片有两个子 label：name_label(索引0) 和 effect_label(索引1)
        # 右侧 cost_label(索引2)
        layout = card.layout()
        name_label = layout.itemAt(0).layout().itemAt(0).widget()
        effect_label = layout.itemAt(0).layout().itemAt(1).widget()
        cost_label = layout.itemAt(2).widget()

        name_label.setText("Cooldown...")
        name_label.setStyleSheet("color: #AAAAAA; font-size: 14px; font-weight: bold; background: transparent;")
        effect_label.setText(f"{remaining}s remaining")
        effect_label.setStyleSheet("color: #CCCCCC; font-size: 11px; background: transparent;")
        cost_label.setText("")

    def _restore_card_text(self, card: QFrame, service_id: int):
        """恢复卡片原始内容"""
        svc_name, points_cost, vitality_effect = self._get_service_info(service_id)
        if not svc_name:
            return
        layout = card.layout()
        name_label = layout.itemAt(0).layout().itemAt(0).widget()
        effect_label = layout.itemAt(0).layout().itemAt(1).widget()
        cost_label = layout.itemAt(2).widget()

        name_label.setText(svc_name)
        name_label.setStyleSheet("color: #333333; font-size: 14px; font-weight: bold; background: transparent;")
        effect_label.setText(f"+{vitality_effect} Vitality")
        effect_label.setStyleSheet("color: #008A73; font-size: 11px; background: transparent;")
        cost_label.setText(f"-{points_cost} Points")
        cost_label.setStyleSheet("color: #FFB347; font-size: 15px; font-weight: bold; background: transparent;")

    def _restore_card_from_error(self, card: QFrame):
        """从错误提示状态恢复卡片原始内容"""
        sid = card.property("service_id")
        if not sid:
            return
        remaining = get_remaining_cooldown(self.user_id, sid)
        if remaining > 0:
            self._refresh_cooldowns()
        else:
            svc_name, points_cost, vitality_effect = self._get_service_info(sid)
            if svc_name:
                effect_label = card.layout().itemAt(0).layout().itemAt(1).widget()
                effect_label.setText(f"+{vitality_effect} 活力值")
                effect_label.setStyleSheet("color: #008A73; font-size: 11px; background: transparent;")
                card.setStyleSheet(self._svc_card_style(active=True, cooldown=False))

    def _get_service_info(self, service_id: int):
        """根据 service_id 查找服务信息"""
        from service.api_pet_service import _services_cache
        s = _services_cache.get(service_id)
        if s:
            return s["name"], s["points_cost"], s["vitality_effect"]
        return None, None, None

    # ============ 样式 ============

    def _cat_btn_style(self, active: bool) -> str:
        """分类按钮样式"""
        if active:
            return """
                QPushButton {
                    background-color: #B3886B; color: white; border: none;
                    border-radius: 8px; padding: 0px 20px; margin: 0px;
                    font-size: 14px; font-weight: bold;
                    text-align: center;
                }
            """
        return """
            QPushButton {
                background-color: #FFF6EA; color: #B3886B; border: 1px solid #B3886B;
                border-radius: 8px; padding: 0px 20px; margin: 0px;
                font-size: 14px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #F5E6D3;
            }
        """

    def _svc_card_style(self, active: bool = True, cooldown: bool = False, error: bool = False) -> str:
        """服务卡片样式"""
        if error:
            return """
                QFrame#serviceCard {
                    background-color: #FFF5F0;
                    border: 1px solid #E76F51;
                    border-radius: 10px;
                }
            """
        if cooldown:
            return """
                QFrame#serviceCard {
                    background-color: #F5F5F5;
                    border: 1px solid #E8E8E8;
                    border-radius: 10px;
                }
            """
        if not active:
            return """
                QFrame#serviceCard {
                    background-color: #F5F5F5;
                    border: 1px solid #E8E8E8;
                    border-radius: 10px;
                }
            """
        return """
            QFrame#serviceCard {
                background-color: white;
                border: 1px solid #F0E0D0;
                border-radius: 10px;
            }
            QFrame#serviceCard:hover {
                background-color: #FFFAF5;
                border: 1px solid #B3886B;
            }
        """

    # ============ 公共方法 ============

    def refresh(self):
        """刷新整个组件数据"""
        self._load_categories()

    def stop_cooldown_timer(self):
        """停止冷却计时器（组件销毁时调用）"""
        self._cooldown_timer.stop()


# ============ 测试入口 ============

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QMainWindow
    app = QApplication(sys.argv)

    window = QMainWindow()
    window.setWindowTitle("宠物服务组件 测试")
    window.resize(350, 500)
    window.setStyleSheet("background-color: #FFF6EA;")

    widget = PetServiceWidget(user_id=1)
    window.setCentralWidget(widget)
    window.show()

    sys.exit(app.exec())
