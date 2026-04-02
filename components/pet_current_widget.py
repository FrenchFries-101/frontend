# pet_widget.py
import os
from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QPushButton, QLineEdit, QHBoxLayout
)
from PySide6.QtGui import QMovie, QFont, QPixmap
from PySide6.QtCore import Qt, QTimer, QSize
from service.api_petshow import get_current_skin, modify_pet_name, get_pet_quote


class PetWidget(QWidget):
    """可复用宠物展示组件"""

    def __init__(self, user_id: int, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # 主布局
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(0, 5, 0, 0) #调整上下左右间距

        # ========== 创建子组件 ==========
        self._create_gif_area()
        self._create_name_slot()
        self._create_quote_area()
        self._create_timer()

        # ========== 按顺序添加到布局 ==========
        self.layout.addWidget(self.quote_label)
        self.layout.addWidget(self.gif_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.name_slot)

        # 初始化数据
        self.load_pet_data()

    def _create_gif_area(self):
        """创建宠物图片/GIF区域"""
        self.gif_label = QLabel()
        self.gif_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gif_label.setFixedSize(250, 200)

    def _create_name_slot(self):
        """创建名字展示 + 内联编辑区（固定高度占位，防止编辑时位移）"""
        self.name_slot = QWidget()
        self.name_slot.setFixedHeight(35)
        self.name_slot.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        slot_layout = QVBoxLayout(self.name_slot)
        slot_layout.setContentsMargins(0, 0, 0, 0)
        slot_layout.setSpacing(0)

        # --- 名字展示行 ---
        name_layout = QHBoxLayout()
        name_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_layout.setSpacing(5)

        self.name_label = QLabel()
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setFont(QFont("", 14, QFont.Weight.Bold))
        self.name_label.setStyleSheet("color: #B3886B; background: transparent;")
        name_layout.addWidget(self.name_label)

        #编辑名字的按钮
        self.edit_icon = QPushButton("✏")
        self.edit_icon.setFixedSize(22, 22)
        self.edit_icon.setCursor(Qt.CursorShape.PointingHandCursor)
        self.edit_icon.setStyleSheet("""
            QPushButton {
                background: transparent; border: none;
                padding: 0px; margin: 0px;
                color: #B3886B; font-size: 12px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: rgba(179, 136, 107, 0.15); border-radius: 11px;
            }
        """)
        self.edit_icon.clicked.connect(self._toggle_edit)
        name_layout.addWidget(self.edit_icon)

        # --- 内联编辑行（默认隐藏，始终占位） ---
        edit_layout = QHBoxLayout()
        edit_layout.setContentsMargins(40, 0, 40, 0)

        self.name_input = QLineEdit()
        self.name_input.setMaxLength(20)
        self.name_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_input.setPlaceholderText("Input new name...")
        self.name_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #B3886B; border-radius: 6px;
                padding: 4px 8px; background: white;
            }
            QLineEdit:focus { border: 2px solid #B3886B; }
        """)
        edit_layout.addWidget(self.name_input)
        edit_layout.addSpacing(8)

        confirm_btn = QPushButton("✓")
        confirm_btn.setFixedSize(28, 28)
        confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #B3886B; color: white; border: none;
                border-radius: 14px; font-size: 14px; font-weight: bold;
                padding: 0px; margin: 0px;
                text-align: center;
            }
            QPushButton:hover { background-color: #9A7055; }
        """)
        confirm_btn.clicked.connect(self._submit_name)
        edit_layout.addWidget(confirm_btn)
        edit_layout.addSpacing(4)

        cancel_btn = QPushButton("✕")
        cancel_btn.setFixedSize(28, 28)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #DFE0DF; color: #666; border: none;
                border-radius: 14px; font-size: 14px; font-weight: bold;
                padding: 0px; margin: 0px;
                text-align: center;
            }
            QPushButton:hover { background-color: #C8C8C8; }
        """)
        cancel_btn.clicked.connect(self._cancel_edit)
        edit_layout.addWidget(cancel_btn)

        # 名字展示行和编辑行放入 slot
        self.name_row_widget = QWidget()
        self.name_row_widget.setLayout(name_layout)
        self.name_row_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        slot_layout.addWidget(self.name_row_widget)

        self.edit_row_widget = QWidget()
        self.edit_row_widget.setLayout(edit_layout)
        self.edit_row_widget.setVisible(False)
        self.edit_row_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        slot_layout.addWidget(self.edit_row_widget)

    def _create_quote_area(self):
        """创建语录区域"""
        self.quote_label = QLabel()
        self.quote_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.quote_label.setWordWrap(True)
        self.quote_label.setStyleSheet("color: #666666; background: transparent; padding: 5px;")

    def _create_timer(self):
        """创建定时刷新语录"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_quote)
        self.timer.start(5000)

    def load_pet_data(self):
        """加载宠物数据"""
        data = get_current_skin(self.user_id)
        self.skin_id = data.get("skin_id")
        self.name_label.setText(data.get("name", ""))
        self.gif_url = data.get("gif_url")
        if self.gif_url:
            self.set_gif(self.gif_url)
        self.update_quote()

    def set_gif(self, gif_path: str):
        """加载图片/GIF"""
        if not gif_path or not os.path.isabs(gif_path):
            gif_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), gif_path
            )
        if not os.path.exists(gif_path):
            print(f"[PetWidget] 文件不存在: {gif_path}")
            return

        _, ext = os.path.splitext(gif_path)
        if ext.lower() == ".gif":
            self.movie = QMovie(gif_path)
            self.movie.setCacheMode(QMovie.CacheMode.CacheAll)
            self.movie.setScaledSize(QSize(200, 200))
            self.gif_label.setMovie(self.movie)
            self.movie.start()
        else:
            pixmap = QPixmap(gif_path)
            if not pixmap.isNull():
                self.gif_label.setPixmap(pixmap.scaled(
                    200, 200,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                ))

    # ===== 名字编辑（内联，不弹窗） =====

    def _toggle_edit(self):
        """切换编辑区域显示"""
        if self.edit_row_widget.isVisible():
            self._cancel_edit()
        else:
            self.name_input.setText(self.name_label.text())
            self.name_input.setMaximumWidth(620)
            self.edit_row_widget.setVisible(True)
            self.name_row_widget.setVisible(False)
            self.name_input.setFocus()
            self.name_input.selectAll()

    def _submit_name(self):
        """提交新名字"""
        new_name = self.name_input.text().strip()
        if not new_name:
            return
        result = modify_pet_name(self.user_id, new_name)
        if result["success"]:
            self.name_label.setText(new_name)
        else:
            print("修改失败:", result["message"])
        self._cancel_edit()

    def _cancel_edit(self):
        """取消编辑，恢复名字显示"""
        self.edit_row_widget.setVisible(False)
        self.name_row_widget.setVisible(True)

    def update_quote(self):
        """刷新语录"""
        quote = get_pet_quote(self.user_id)
        self.quote_label.setText(quote.get("content", "")) #改组件


# 测试入口
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QMainWindow
    app = QApplication(sys.argv)

    window = QMainWindow()
    window.setWindowTitle("PetWidget Demo")
    window.resize(400, 600)
    window.setStyleSheet("background-color: #FFF6EA;")  # 测试窗口背景色

    pet_widget = PetWidget(user_id=1)
    window.setCentralWidget(pet_widget)
    window.show()
    sys.exit(app.exec())
