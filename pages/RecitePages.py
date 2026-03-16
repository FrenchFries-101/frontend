from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QHBoxLayout,
    QSizePolicy, QSpacerItem
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QIcon, QColor
import os


class RecitePage(QWidget):
    def __init__(self):
        super().__init__()
        # 获取当前脚本所在目录
        self.BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 上一级 project_root
        self.ICON_RETURN = os.path.join(self.BASE_DIR, "resources", "icons", "return_black.png")
        self.ICON_CHINESE_OFF = os.path.join(self.BASE_DIR, "resources", "icons", "chinese.png")
        self.ICON_CHINESE_ON = os.path.join(self.BASE_DIR, "resources", "icons", "chinese1.png")
        # 全局中文显示开关状态
        self.show_chinese_global = False

        self.init_ui()
        self.init_data()
        self.show_categories()


    def init_ui(self):
        self.setStyleSheet("""
        QWidget{
            background:#f8f9fb;
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


        QPushButton.category{
            background:white;
            border:1px solid #e5e7eb;
            padding:14px;
            border-radius:8px;
            font-size:16px;
        }
        
        QPushButton.category:hover{
            background:#f7d6d0;
        }
        
        QPushButton.category:pressed{
            background:#ffb6c1;   /* 按下瞬间 */
        }
        
        QPushButton.category:checked{
            background:#f4c8c2;   /* 点击后保持选中 */
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

            # pixmap = QPixmap(self.ICON_CHINESE_ON)
            # scaled_pixmap = pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            # self.title_back_btn.setIcon(QIcon(scaled_pixmap))
            # # self.title_back_btn.setIconSize(QSize(24, 24))
        except:
            self.title_back_btn.setText("←")
            self.title_back_btn.setStyleSheet("font-size:20px; font-weight:bold;")

        self.title_back_btn.clicked.connect(self.on_title_back_clicked)

        # 2. 左侧弹性空间
        spacer_left = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)

        # 3. 标题
        self.title = QLabel("Word Expansion")
        self.title.setObjectName("title")
        self.title.setAlignment(Qt.AlignCenter)

        #右侧弹性空间
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
        # self.chinese_btn.setFixedSize(30, 30)
        self.chinese_btn.setObjectName("title_chinese_btn")
        self.chinese_btn.setFixedSize(24, 24)
        # self.chinese_btn.setVisible(False)
        self.chinese_btn.setStyleSheet("border:none;background:transparent;")

        # 加载两张图片，和返回按钮同款
        pixmap_off = QPixmap(self.ICON_CHINESE_OFF)#记载为土
        if pixmap_off.isNull():
            print("pixmap_off 加载失败")
        else:
            print("pixmap_off 加载成功")
        if not pixmap_off.isNull():
            scaled_off = pixmap_off.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.icon_chinese_off = QIcon(scaled_off)
            # self.chinese_btn.setIcon(QIcon(scaled_off))
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
            scaled_on = pixmap_on.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
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
            self.chinese_btn.setIconSize(QSize(24, 24))
            self.chinese_btn.setFixedSize(30,30)
            print(self.chinese_btn.icon().isNull())
        except:
            self.chinese_btn.setText("--")
            self.chinese_btn.setStyleSheet("font-size:20px; font-weight:bold;")

        # 点击事件
        self.chinese_btn.clicked.connect(self.toggle_chinese)

        # switch_container.addWidget(self.switch_label)
        switch_container.addWidget(self.chinese_btn)
        # switch_container.addWidget(QLabel("Test"))
        # switch_container.addWidget(self.title_back_btn1)

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

    def init_data(self):
        # 单词数据
        self.word_data = {
            ("学科单词", "数学"): [
                {"english": "derivative", "chinese": "导数"},
                {"english": "matrix", "chinese": "矩阵"},
                {"english": "integral", "chinese": "积分"},
            ],
            ("学科单词", "计算机"): [
                {"english": "algorithm", "chinese": "算法"},
                {"english": "recursion", "chinese": "递归"},
                {"english": "compiler", "chinese": "编译器"},
            ],
            ("学术英语", "演讲用语"): [
                {"english": "hello", "chinese": "打招呼"},
            ],
            ("学术英语", "学术写作"): [
                {"english": "Next", "chinese": "下一个"},
            ],
            ("学术英语", "小组讨论用语"): [
                {"english": "In my opinion", "chinese": "我认为"},
                {"english": "I agree with you", "chinese": "我同意你的观点"},
            ],
            ("学术英语", "邮件用语"): [
                {"english": "In my opinion", "chinese": "我认为"},
                {"english": "I agree with you", "chinese": "我同意你的观点"},
            ]
        }

    # ---------------- 单词点击单独切换（可选保留） ----------------
    def toggle_word_meaning(self, item):
        """单个单词的中文显示切换（受全局开关限制）"""
        if not self.show_chinese_global:
            return  # 全局开关关闭时，禁止单独切换

        cn_label = item.data(Qt.UserRole)
        if cn_label:
            cn_label.setVisible(not cn_label.isVisible())

    # ---------------- 数据获取方法 ----------------
    def get_categories(self):
        return ["学科单词", "学术英语"]

    def get_subcategories(self, category):
        data = {
            "学科单词": ["数学", "计算机", "土木", "机械"],
            "学术英语": ["小组讨论用语", "演讲用语", "学术写作", "邮件用语"]
        }
        return data.get(category, [])

    def get_words(self, category, sub):
        return self.word_data.get((category, sub), [])

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
        """显示一级分类页面：隐藏返回按钮和开关"""
        self.clear_container()
        self.page_state = "category"
        self.title_back_btn.setVisible(False)
        self.switch_widget.setVisible(False)  # 隐藏开关容器

        # 显示一级分类按钮
        for c in self.get_categories():
            btn = QPushButton(c)
            btn.setProperty("class", "category")
            btn.clicked.connect(lambda _, x=c: self.show_subcategories(x))
            self.container.addWidget(btn)
        self.container.addStretch()

    def show_subcategories(self, category):
        """显示二级分类页面：显示返回按钮和开关"""
        self.current_category = category
        self.page_state = "subcategory"
        self.title_back_btn.setVisible(True)
        self.switch_widget.setVisible(True)  # 显示开关容器
        self.clear_container()

        # 二级分类横向布局
        self.tab_layout = QHBoxLayout()
        self.tab_layout.setSpacing(10)
        self.container.addLayout(self.tab_layout)

        # 二级分类按钮
        sub_list = self.get_subcategories(category)
        self.current_sub = sub_list[0] if sub_list else ""
        for sub in sub_list:
            btn = QPushButton(sub)
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.setProperty("class", "category")
            btn.clicked.connect(lambda _, s=sub: self.switch_subcategory(s))
            self.tab_layout.addWidget(btn)

        # 单词列表
        self.word_list = QListWidget()
        self.word_list.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        # self.word_list.itemClicked.connect(self.toggle_word_meaning)
        self.container.addWidget(self.word_list)

        self.load_words()

    def switch_subcategory(self, sub):
        """切换二级分类"""
        self.current_sub = sub
        self.load_words()

    #切换函数
    def toggle_chinese(self):

        self.show_chinese_global = not self.show_chinese_global

        if self.show_chinese_global:
            self.chinese_btn.setIcon(self.icon_chinese_on)
        else:
            self.chinese_btn.setIcon(self.icon_chinese_off)

        # 重新加载单词
        self.load_words()


    # ---------------- 加载单词列表 ----------------
    def load_words(self):
        """加载并显示单词列表"""
        if not self.word_list or not self.current_category or not self.current_sub:
            return

        self.word_list.clear()
        words = self.get_words(self.current_category, self.current_sub)

        for w in words:
            # 单词卡片Widget
            word_widget = QWidget()
            word_layout = QHBoxLayout(word_widget)
            word_layout.setContentsMargins(0, 0, 0, 0)
            word_layout.setSpacing(0)

            # 英文标签
            en_label = QLabel(w["english"])
            en_label.setObjectName("word_en")
            en_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

            # 弹性空间
            spacer = QWidget()
            spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

            # 中文标签（根据全局开关决定显示状态）
            cn_label = QLabel(w["chinese"])
            cn_label.setObjectName("word_cn")
            cn_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

            # 组装布局
            word_layout.addWidget(en_label)
            word_layout.addWidget(spacer)
            word_layout.addWidget(cn_label)

            #它本身是一个新的窗口，先绑定到整体窗口再setVisible就不会单独创建一个新的窗口了
            cn_label.setVisible(self.show_chinese_global)

            # 列表项
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 50))

            # 存储中文标签引用
            cn_label.setProperty("cn_label", True)
            item.setData(Qt.UserRole, cn_label)

            self.word_list.addItem(item)
            self.word_list.setItemWidget(item, word_widget)


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = RecitePage()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())