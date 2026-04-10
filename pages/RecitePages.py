from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QHBoxLayout,
    QSizePolicy, QSpacerItem, QScrollArea
)
from utils.path_utils import resource_path
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QPixmap, QIcon, QColor
from service.api_word import get_categories, get_subcategories, get_words
from service.api import submit_group_activity

from PySide6.QtGui import QMovie
from pages.SpellDialog import SpellDialog
from datetime import datetime
import session


class RecitePage(QWidget):
    points_changed = Signal(int)   # 兼容旧逻辑，当前不再用于背词加金币
    group_activity_submitted = Signal()

    def __init__(self):
        super().__init__()
        print("开始加载背单词界面")
        self.ICON_RETURN = resource_path("resources/icons/return_black.png")
        self.ICON_CHINESE_OFF = resource_path("resources/icons/book.png")
        self.ICON_CHINESE_ON = resource_path("resources/icons/bookopen.png")
        self.english = resource_path("resources/icons/graduate.gif")
        self.science = resource_path("resources/icons/science.gif")

        # Global Chinese display toggle
        self.show_chinese_global = False

        # Spelling feature: track completed words (english -> timestamp) across loads
        self.completed_words = {}    # english -> timestamp string
        self.word_item_refs = {}     # english -> ts_label widget (rebuilt per load_words)

        self.init_ui()
        # self.init_data()
        self.show_categories()

    def init_ui(self):
        self.setStyleSheet("""
        QWidget{
            background:white;
            font-family:"Microsoft YaHei";
            color:#333;
        }
        

        QLabel#title{
            font-size:20px;
            background:transparent;
            font-weight:600;
            margin:0;
            padding:20px 0;
        }
        QPushButton#title_chinese_btn {
            min-width: 24px !important;  /* 强制按钮至少占24px宽度，不能被压缩 */
            margin-right: 5px !important; /* 按钮右边留5px空隙，不贴到窗口边缘 */
            padding: 0 !important; /* 把按钮的内边距清零，只显示图标 */
        }
        /* 标题栏返回按钮样式 */
        QPushButton#title_back_btn {
            background:transparent;
            border:none;
            margin:0;
            padding:0;
        }

        QPushButton#title_back_btn:hover {
            opacity: 0.8;
        }


QPushButton.category {
    background-color: white;
    border-radius: 12px;
    border: 1px solid #f0f0f0;

    padding: 6px 5px;
    font-size: 13px;
    color: #333;

    min-width: 80px;   /* ? 防止太窄 */
}

/* hover */
QPushButton.category:hover {
    background-color: #fff7f9;
    border: 1px solid #ff8fa3;
}

/* 选中 */
QPushButton.category:checked {
    background-color: #ffe4e8;
    border: 1px solid #ff6b81;
    color: #ff6b81;
}

        QListWidget{
            border:none;
            background:white;
            border-radius:10px;
            padding:6px;
            outline:none;
            margin:20px;
        }

        QListWidget::item{
            padding:0px;
            border-bottom:1px solid #eee;
            height:50px;
        }

        QListWidget::item:selected{
            background:#f3f4f6;
            color:#333;
            outline:none;
        }

        QLabel#word_en {
            font-size:16px;
            color:#333;
            padding-left:12px;
        }

        QLabel#word_cn {
            font-size:16px;
            color:#666;
            padding-right:12px;
        }
        
        QWidget#CategoryCard {
    background-color: white;
    border-radius: 18px;
    border: 1px solid #f0f0f0;
}

/* hover */
QWidget#CategoryCard:hover {
    border: 1px solid #ff8fa3;
}

/* 文字 */
QLabel#cat_text {
    font-size: 16px;
    font-weight: 600;
    color: #333;
}

/* hover 文字变粉 */
QWidget#CategoryCard:hover QLabel#cat_text {
    color: #ff6b81;
}

        """)

        main = QVBoxLayout(self)
        main.setSpacing(0)
        main.setContentsMargins(20, 0, 30, 0)

        # ---------------- 标题栏（返回按钮 + 标题 + 中文开关） ----------------
        title_bar_layout = QHBoxLayout()
        title_bar_layout.setSpacing(10)
        title_bar_layout.setContentsMargins(0, 0, 0, 0)

        # 1. 返回按钮
        self.title_back_btn = QPushButton()
        self.title_back_btn.setObjectName("title_back_btn")
        self.title_back_btn.setFixedSize(24, 24)
        self.title_back_btn.setVisible(False)

        # 加载返回图标  self.ICON_CHINESE_ON  self.ICON_RETURN
        try:
            pixmap = QPixmap(self.ICON_RETURN)
            scaled_pixmap = pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.title_back_btn.setIcon(QIcon(scaled_pixmap))
            self.title_back_btn.setIconSize(QSize(24, 24))


        except:
            self.title_back_btn.setText("←")
            self.title_back_btn.setStyleSheet("font-size:20px; font-weight:bold;")

        self.title_back_btn.clicked.connect(self.on_title_back_clicked)

        # 2. 左侧弹性空间
        spacer_left = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)


        # 原来的标题样式
        self.title = QLabel("Word Expansion")
        self.title.setObjectName("title")
        self.title.setAlignment(Qt.AlignCenter)

        # 新样式
        self.title.setStyleSheet("""
            font: 700 17pt "Terminal";   /* 加粗 17pt Terminal */
            color: #ff6b81;              /* 粉色 */
            background: transparent;
            margin:0;
            padding:20px 0;
        """)

        # 右侧弹性空间
        spacer_right = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)

        # 中文显示开关容器
        self.switch_widget = QWidget()
        self.switch_widget.setVisible(True)
        switch_container = QHBoxLayout(self.switch_widget)
        switch_container.setSpacing(5)
        switch_container.setContentsMargins(0, 0, 0, 0)
        switch_container.setAlignment(Qt.AlignVCenter)

        # 中文按钮
        self.chinese_btn = QPushButton()
        self.chinese_btn.setObjectName("title_chinese_btn")
        self.chinese_btn.setFixedSize(30, 30)
        self.chinese_btn.setStyleSheet("border:none;background:transparent;")


        # 加载两张图片，和返回按钮同款
        pixmap_off = QPixmap(self.ICON_CHINESE_OFF)  # 记载为土
        if pixmap_off.isNull():
            print("pixmap_off 加载失败")
        else:
            print("pixmap_off 加载成功")
        if not pixmap_off.isNull():
            scaled_off = pixmap_off.scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.icon_chinese_off = QIcon(scaled_off)
            print("ICON_CHINESE_OFF成功！！")
            if self.icon_chinese_off.isNull():
                print("self.icon_chinese_off 创建失败")
            else:
                print("self.icon_chinese_off 创建成功")
        else:
            print("ICON_CHINESE_OFF记载失败")
            self.icon_chinese_off = QIcon()  # 失败就空

        pixmap_on = QPixmap(self.ICON_CHINESE_ON)
        if pixmap_on.isNull():
            print("pixmap_on 加载失败")
        else:
            print("pixmap_on 加载成功")
        if not pixmap_on.isNull():
            scaled_on = pixmap_on.scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.icon_chinese_on = QIcon(scaled_on)
            print("ICON_CHINESE_ON记载成功！")
            if self.icon_chinese_on.isNull():
                print("self.icon_chinese_on创建失败")
            else:
                print("self.icon_chinese_on创建成功")
        else:
            print("ICON_CHINESE_ON加载失败")
            self.icon_chinese_on = QIcon()

        # 默认状态
        try:
            self.chinese_btn.setIcon(self.icon_chinese_off)
            self.chinese_btn.setIconSize(QSize(30, 30))
            self.chinese_btn.setFixedSize(30, 30)
            print(self.chinese_btn.icon().isNull())
        except:
            self.chinese_btn.setText("--")
            self.chinese_btn.setStyleSheet("font-size:20px; font-weight:bold;")

        # 点击事件
        self.chinese_btn.clicked.connect(self.toggle_chinese)
        switch_container.addWidget(self.chinese_btn)


        # 组装标题栏
        title_bar_layout.addWidget(self.title_back_btn, alignment=Qt.AlignVCenter)
        title_bar_layout.addItem(spacer_left)
        title_bar_layout.addWidget(self.title, alignment=Qt.AlignVCenter)
        title_bar_layout.addItem(spacer_right)
        # title_bar_layout.addWidget(self.chinese_btn, alignment=Qt.AlignVCenter)
        title_bar_layout.addWidget(self.switch_widget, alignment=Qt.AlignVCenter)
        self.chinese_btn.setVisible(True)
        self.switch_widget.setVisible(True)
        print(self.chinese_btn.icon().isNull())
        print(self.chinese_btn.isVisible())
        print(self.switch_widget.isVisible())

        main.addLayout(title_bar_layout)

        # 内容容器
        self.container = QVBoxLayout()
        main.addLayout(self.container)

        # 页面状态
        self.current_category = ""
        self.current_sub = ""
        self.page_state = "category"
        self.word_list = None


    # ---------------- 单词点击单独切换（可选保留） ----------------
    def toggle_word_meaning(self, item):
        """单个单词的中文显示切换（受全局开关限制）"""
        if not self.show_chinese_global:
            return  # 全局开关关闭时，禁止单独切换

        cn_label = item.data(Qt.UserRole)
        if cn_label:
            cn_label.setVisible(not cn_label.isVisible())

    # ---------------- api接口-获取第一季分类----------------
    def get_categories(self):
        return get_categories()

    # 示例返回值

    # ---------------- api接口-获取第二级分类----------------
    def get_subcategories(self, category):
        return get_subcategories(category)


    def get_words(self, subcategory_id):
        return get_words(subcategory_id)

    # ---------------- 工具方法 ----------------
    def clear_container(self):
        """清空内容容器"""
        while self.container.count():
            item = self.container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                sub_layout = item.layout()
                while sub_layout.count():
                    sub_item = sub_layout.takeAt(0)
                    if sub_item.widget():
                        sub_item.widget().deleteLater()
                sub_layout.deleteLater()

    # ---------------- 页面切换 ----------------
    def on_title_back_clicked(self):
        """返回按钮点击事件"""
        if self.page_state == "subcategory":
            self.show_categories()

    def show_categories(self):
        self.clear_container()
        self.word_list = None   # prevent stale reference to deleted widget
        self.page_state = "category"
        self.title_back_btn.setVisible(False)
        self.switch_widget.setVisible(False)

        # ⭐ 外层垂直居中容器
        wrapper = QVBoxLayout()
        wrapper.setContentsMargins(0, 40, 0, 40)
        wrapper.setSpacing(30)
        # wrapper.setAlignment(Qt.AlignCenter)

        self.container.addLayout(wrapper)

        for c in self.get_categories():

            # ===== 卡片 =====
            card = QWidget()
            card.setObjectName("CategoryCard")
            card.setFixedWidth(500)
            card.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

            layout = QVBoxLayout(card)
            layout.setAlignment(Qt.AlignCenter)
            layout.setSpacing(12)

            # ===== GIF =====
            img_label = QLabel()
            img_label.setAlignment(Qt.AlignCenter)

            if c["category_name"] == "Academic Disciplines":
                gif_path = self.science
            else:
                gif_path = self.english

            movie = QMovie(gif_path)
            movie.setScaledSize(QSize(140, 140))  # ⭐ 图也放大
            img_label.setMovie(movie)
            movie.start()

            # ===== 文字 =====
            text_label = QLabel(c["category_name"])
            text_label.setObjectName("cat_text")
            text_label.setAlignment(Qt.AlignCenter)

            # ===== 组装 =====
            layout.addWidget(img_label)
            layout.addWidget(text_label)

            # ⭐ 鼠标手型（体验+1）
            card.setCursor(Qt.PointingHandCursor)

            # ===== 点击 =====
            card.mousePressEvent = lambda e, cid=c["category_id"]: self.show_subcategories(cid)

            wrapper.addWidget(card, alignment=Qt.AlignCenter)



    def show_subcategories(self, category_id):
        self.current_category = category_id
        self.page_state = "subcategory"
        self.title_back_btn.setVisible(True)
        self.switch_widget.setVisible(True)  # 显示开关容器
        self.clear_container()


        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)  # 保证可以横向滑动
        scroll.setFixedHeight(55)  # 控制高度
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 不要纵向滚动
        scroll.setStyleSheet("border:none; background:white;")



        tab_container = QWidget()
        self.tab_layout = QHBoxLayout(tab_container)
        self.tab_layout.setSpacing(6)
        self.tab_layout.setContentsMargins(0, 0, 0, 0)  # 外边距不要挡按钮

        scroll.setWidget(tab_container)
        self.container.addWidget(scroll)


        sub_list = self.get_subcategories(category_id)

        # 默认选第一个 subcategory_id
        self.current_sub = sub_list[0]["subcategory_id"] if sub_list else None

        for sub in sub_list:
            btn = QPushButton(sub["subcategory_name"])
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.setProperty("class", "category")

            # ⭐ 给二级标题按钮加边框
            btn.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    border: 1px solid #f0f0f0;   /* 默认边框颜色 */
                    border-radius: 10px;          /* 圆角 */
                    padding: 1px 1px;            /* 内边距 */
                    font-size: 14px;
                    color: #333;
                }
                QPushButton:hover {
                    border: 2px solid #ff6b81;
                    background-color: #fff0f3;
                    color: #ff6b81;
                }
                QPushButton:checked {
                    border: 2px solid #ff6b81;
                    background-color: #ffe4e8;
                    color: #ff6b81;
                }
            """)

            # ⭐ 横向自动伸展，高度固定
            # ⭐ 横向固定，纵向高度固定
            # 字体
            font = btn.font()
            font.setPointSize(14)
            btn.setFont(font)

            # ⭐ 动态计算最小宽度，保证文字全部显示
            fm = btn.fontMetrics()  # 获取字体度量
            text_width = fm.horizontalAdvance(sub["subcategory_name"])
            btn.setMinimumWidth(text_width + 20)  # +20px 内边距

            btn.setFixedHeight(36)  # 固定高度
            btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

            btn.clicked.connect(lambda _, sid=sub["subcategory_id"]: self.switch_subcategory(sid))
            self.tab_layout.addWidget(btn)
        self.tab_layout.addStretch()
        self.tab_layout.addSpacing(10)

        # 单词列表
        self.word_list = QListWidget()
        self.word_list.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.word_list.itemDoubleClicked.connect(self._on_word_double_click)
        self.container.addWidget(self.word_list)
        self.load_words()



    def switch_subcategory(self, sub_id):
        self.current_sub = sub_id
        self.load_words()

    # 切换函数
    def toggle_chinese(self):
        self.show_chinese_global = not self.show_chinese_global

        if self.show_chinese_global:
            self.chinese_btn.setIcon(self.icon_chinese_on)
        else:
            self.chinese_btn.setIcon(self.icon_chinese_off)

        # Toggle cn_label visibility in-place — no HTTP request, no widget recreation
        if not self.word_list:
            return
        for i in range(self.word_list.count()):
            item = self.word_list.item(i)
            widget = self.word_list.itemWidget(item)
            if widget:
                cn = widget.findChild(QLabel, "cn_label")
                if cn:
                    cn.setVisible(self.show_chinese_global)
                    item.setSizeHint(widget.sizeHint())

    # ---------------- 加载单词列表 ----------------
    def load_words(self):
        if not self.word_list or not self.current_category or not self.current_sub:
            return

        self.word_list.clear()
        self.word_item_refs = {}
        words = self.get_words(self.current_sub)

        for w in words:
            word_widget = QWidget()
            word_widget.setObjectName("WordCard")

            word_widget.setStyleSheet("""
                QWidget {
                    background: white;
                    border-radius: 10px;
                    padding: 8px;
                }
                /* ================= 单词卡片 ================= */

QWidget#WordCard {
    background-color: white;
    border-radius: 12px;
    border: 1px solid #f0f0f0;
    padding: 10px;
}

/* hover 效果 */
QWidget#WordCard:hover {
    background-color: #fff7f9;
    border: 1px solid #ff8fa3;
}


/* ================= 英文 ================= */
QWidget#WordCard QLabel#en {
    font-size: 16px;
    font-weight: 600;
    color: #222;
}

/* hover 英文变粉 */
QWidget#WordCard:hover QLabel#en {
    color: #ff6b81;
}


/* ================= 中文 ================= */
QWidget#WordCard QLabel#cn {
    font-size: 14px;
    color: #666;
}


/* 子组件透明 */
QWidget#WordCard * {
    background: transparent;
}
            """)

            word_layout = QVBoxLayout(word_widget)
            word_layout.setContentsMargins(10, 8, 10, 8)
            word_layout.setSpacing(6)

            # ---------------- Top row: English word + timestamp ----------------
            top_row = QHBoxLayout()
            top_row.setSpacing(8)

            en_label = QLabel(w["english"])
            en_label.setStyleSheet("""
                font-size:16px;
                font-weight:600;
                color:#222;
            """)
            en_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

            ts_label = QLabel()
            ts_label.setStyleSheet("font-size:11px; color:#ff6b81;")
            ts_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

            # Restore timestamp if word was previously completed
            english_key = w["english"]
            if english_key in self.completed_words:
                ts_label.setText(f'finished at {self.completed_words[english_key]}')
                ts_label.setVisible(True)
            else:
                ts_label.setVisible(False)

            self.word_item_refs[english_key] = ts_label

            top_row.addWidget(en_label)
            top_row.addStretch()
            top_row.addWidget(ts_label)

            # ---------------- Chinese definition ----------------
            cn_label = QLabel(w["chinese"])
            cn_label.setObjectName("cn_label")
            cn_label.setStyleSheet("""
                font-size:14px;
                color:#666;
            """)
            cn_label.setWordWrap(True)
            cn_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            cn_label.setVisible(self.show_chinese_global)

            # ---------------- Assemble ----------------
            word_layout.addLayout(top_row)
            word_layout.addWidget(cn_label)

            # ---------------- ListItem ----------------
            item = QListWidgetItem()
            item.setData(Qt.UserRole, w)
            item.setSizeHint(word_widget.sizeHint())

            self.word_list.addItem(item)
            self.word_list.setItemWidget(item, word_widget)


    def _on_word_double_click(self, item):
        """Open spell dialog on double-click; mark word finished and award points if correct."""
        word_data = item.data(Qt.UserRole)
        if not word_data:
            return

        dlg = SpellDialog(word_data, self)
        if dlg.exec() == SpellDialog.Accepted:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M")
            english_key = word_data["english"]
            is_new = english_key not in self.completed_words

            self.completed_words[english_key] = ts

            ts_label = self.word_item_refs.get(english_key)
            if ts_label:
                ts_label.setText(f"finished at {ts}")
                ts_label.setVisible(True)


            if is_new:
                user_id = session.user["id"] if session.user else None
                group_id = getattr(session, "current_group_id", None)
                if user_id and group_id:
                    result = submit_group_activity(
                        group_id=group_id,
                        user_id=user_id,
                        activity_type="word",
                        amount=1,
                    )
                    if isinstance(result, dict) and result.get("success"):
                        self.group_activity_submitted.emit()
                    else:
                        print("背词 activity 登记失败:", result)



if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = RecitePage()
    window.resize(800, 600)
    window.sh