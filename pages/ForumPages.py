import os
import sys
from functools import partial

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout,
    QScrollArea, QLabel, QPushButton, QLineEdit, QTextEdit, QStackedWidget, QSizePolicy
)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Qt

# 导入你的组件
from components.SinglePost import SinglePost
from components.SingleReply import SingleReply
from components.SingleDetailedPost import SingleDetailedPost

# ======================== 假数据（内置） ========================
class MockForumData:
    _posts = [
        {"id": 1, "title": "关于**的瓜", "contents": "这是第一条帖子的详细内容", "author": "用户1", "time": "2026-03-12", "likes": 12},
        {"id": 2, "title": "Python Qt开发经验分享", "contents": "这是第二条帖子的详细内容", "author": "用户2", "time": "2026-03-13", "likes": 28}
    ]
    _replies = {
        1: [
            {"name": "回复用户1", "content": "沙发！前排围观", "time": "2026-03-13 10:00", "likes": 5, "avatar": os.path.join(os.path.dirname(__file__), "resources", "icons", "avatar1.png")},
            {"name": "回复用户2", "content": "支持楼主，期待后续", "time": "2026-03-13 11:00", "likes": 3, "avatar": os.path.join(os.path.dirname(__file__), "resources", "icons", "avatar1.png")}
        ]
    }

    @classmethod
    def get_posts(cls, keyword=""):
        return [p for p in cls._posts if keyword in p["title"]] if keyword else cls._posts
    @classmethod
    def get_post_detail(cls, post_id):
        return next((p for p in cls._posts if p["id"] == post_id), None)
    @classmethod
    def get_replies(cls, post_id):
        return cls._replies.get(post_id, [])
    @classmethod
    def create_post(cls, title, content):
        new_id = max(p["id"] for p in cls._posts) + 1
        cls._posts.append({"id": new_id, "title": title, "content": content, "author": "当前用户", "time": "2026-03-15", "likes": 0})
    @classmethod
    def create_reply(cls, post_id, content):
        if post_id not in cls._replies:
            cls._replies[post_id] = []
        cls._replies[post_id].append({"name": "当前用户", "content": content, "time": "2026-03-15 15:00", "likes": 0, "avatar": os.path.join(os.path.dirname(__file__), "resources", "icons", "avatar1.png")})

# ======================== 主窗口：一次性加载整个UI ========================
class ForumWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)




        self.load_full_ui()
        #这个加了才能显示出来
        self.init_pages()
        self.bind_all_events()
        self.ui.setObjectName("ForumPage")
        self.setAttribute(Qt.WA_StyledBackground, True)

        self.ui.setStyleSheet("""

        
 /* 外层保持透明，和 main 融合 */
#ForumPage{
    background:transparent;
}

/* 页面主体 */
QScrollArea{
    border:none;
    background:white;
}

/* 内容区域 */
#post_contents,
#detail_content{
    background:white;
}

/* 输入框 */
QLineEdit,
QTextEdit{
    background:white;
    border:1px solid #ddd;
    border-radius:6px;
}

/* 按钮 */
QPushButton{
    background:white;
    border:1px solid #eee;
    border-radius:8px;
}

QPushButton:hover{
    background:#fff0f3;
}

QPushButton:pressed{
    background:#ffd6e0;
}

QPushButton:checked{
    background:#ffccd5;
}

      
        """)

        # print(self.ui.size())
        # print(self.size())

    def load_full_ui(self):
        # 一次性加载整个postPage.ui
        loader = QUiLoader()
        ui_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),  # 上一级目录（AgileProject）
            "ui",
            "postPage.ui"
        )
        ui_file = QFile(ui_path)
        if not ui_file.open(QFile.ReadOnly):
            print(f"无法打开UI文件: {ui_path}")
            return
        self.ui = loader.load(ui_file, self)
        ui_file.close()


        self.post_scroll = self.ui.findChild(QScrollArea, "post_scrollArea")
        self.post_container = self.ui.findChild(QWidget, "post_contents")

        # 获取已有布局，如果没有就创建
        self.post_layout = self.post_container.layout()
        if self.post_layout is None:
            self.post_layout = QVBoxLayout(self.post_container)
        self.post_layout.setAlignment(Qt.AlignTop)

        # 添加一个按钮，用来动态添加控件
        add_btn = QPushButton("添加新控件")
        add_btn.clicked.connect(self.add_new_label)
        self.post_layout.addWidget(add_btn)

        # 取出stackedWidget（三个页面都在里面）
        self.stack = self.ui.findChild(QStackedWidget, "stackedWidget")

        # 取出三个子页面
        self.forum_main = self.stack.findChild(QWidget, "forum_main")
        self.forum_create = self.stack.findChild(QWidget, "forum_create")
        self.forum_detail = self.stack.findChild(QWidget, "forum_detail")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.ui)

    def init_scroll_area(self):
        # 确保 scroll area 可自适应大小
        # self.post_scroll.setWidgetResizable(True)
        # self.post_scroll.setWidget(self.post_container)

        # 获取已有布局，如果没有就创建
        self.post_layout = self.post_container.layout()
        if self.post_layout is None:
            self.post_layout = QVBoxLayout(self.post_container)
        self.post_layout.setAlignment(Qt.AlignTop)

        # 添加一个按钮，用来动态添加控件
        add_btn = QPushButton("添加新控件")
        add_btn.clicked.connect(self.add_new_label)
        self.post_layout.addWidget(add_btn)

    def init_pages(self):
        # 初始化主页面
        self.init_main_page()
        # 初始化创建页面
        self.init_create_page()
        # 初始化详情页面
        self.init_detail_page()
        # 默认显示主页面
        self.stack.setCurrentIndex(0)

    def add_new_label(self):
        # 每点击一次就添加一个新的 QLabel
        count = self.post_layout.count()
        label = QLabel(f"新控件 {count}")
        label.setStyleSheet("background-color: #C0FFC0; padding: 5px;")
        label.setAlignment(Qt.AlignCenter)
        self.post_layout.addWidget(label)

    # ------------------------ 主页面逻辑 ------------------------
    def init_main_page(self):
        # 查找主页面控件
        self.search_input = self.forum_main.findChild(QLineEdit, "search_input")
        self.search_btn = self.forum_main.findChild(QPushButton, "search_button")
        self.to_create_btn = self.forum_main.findChild(QPushButton, "to_create_botton")
        self.post_scroll = self.ui.findChild(QScrollArea, "post_scrollArea")
        self.post_container = self.ui.findChild(QWidget, "post_contents")


        # 设置滚动区域
        self.post_scroll.setWidgetResizable(True)

        # 获取已有布局，如果没有就创建
        self.post_layout = self.post_container.layout()
        if self.post_layout is None:
            self.post_layout = QVBoxLayout(self.post_container)
        self.post_layout.setAlignment(Qt.AlignTop)


        # 初始化帖子列表
        self.load_posts()

    def load_posts(self, keyword=""):
        # 清空旧内容
        while self.post_layout.count():
            child = self.post_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        posts = MockForumData.get_posts(keyword)

        for post in posts:
            post_widget = SinglePost(post)
            post_widget.clicked.connect(lambda p=post: self.go_to_detail(p["id"]))
            self.post_layout.addWidget(post_widget)

        print("posts loaded:", [p["title"] for p in posts])


    # ------------------------ 创建页面逻辑 ------------------------
    def init_create_page(self):
        # 查找创建页面控件
        self.clear_btn = self.forum_create.findChild(QPushButton, "clear_button")
        self.return_btn = self.forum_create.findChild(QPushButton, "return_button")
        self.create_btn = self.forum_create.findChild(QPushButton, "create_button")
        self.title_input = self.forum_create.findChild(QLineEdit, "title_input")
        self.content_input = self.forum_create.findChild(QTextEdit, "content_input")
        # 设置标题
        title_label = self.forum_create.findChild(QLabel, "create_title_label")
        if title_label:
            title_label.setText("发布新帖子")

    def clear_inputs(self):
        self.title_input.clear()
        self.content_input.clear()

    def create_post(self):
        title = self.title_input.text().strip()
        content = self.content_input.toPlainText().strip()
        if not title or not content:
            print("标题和内容不能为空")
            return

        MockForumData.create_post(title, content)
        self.clear_inputs()
        self.stack.setCurrentIndex(0)
        self.load_posts()  # 刷新主页

    # ------------------------ 详情页面逻辑 ------------------------
    def init_detail_page(self):
        # 查找详情页面控件
        self.return_btn2 = self.forum_detail.findChild(QPushButton, "return_button2")
        self.up_btn = self.forum_detail.findChild(QPushButton, "up_button")
        self.reply_btn = self.forum_detail.findChild(QPushButton, "reply_button")
        self.reply_input = self.forum_detail.findChild(QTextEdit, "reply_input")
        self.detail_title = self.forum_detail.findChild(QLabel, "detail_title")
        self.detail_scroll = self.forum_detail.findChild(QScrollArea, "detail_scrollArea")
        self.detail_container = self.forum_detail.findChild(QWidget, "detail_content")

        self.detail_layout = self.detail_container.layout()
        if self.detail_layout is None:
            self.detail_layout = QVBoxLayout(self.detail_container)
        self.detail_layout.setAlignment(Qt.AlignTop)

        # 设置滚动区域布局
        self.detail_layout.setSpacing(15)
        self.current_post_id = None



    def load_post_detail(self, post_id):
        self.current_post_id = post_id
        print(f"post_id{post_id}")
        # 清空旧内容
        while self.detail_layout.count():
            child = self.detail_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # 加载帖子详情
        post = MockForumData.get_post_detail(post_id)
        if not post:
            print("mei you post")
            return
        print(post)
        self.detail_title.setText(f"帖子详情：{post['title']}")
        # 添加帖子组件
        post_widget = SingleDetailedPost(post)
        self.detail_layout.addWidget(post_widget)
        # 添加分割线
        line = QLabel()
        line.setStyleSheet("background-color: #E0E0E0; height: 1px;")
        self.detail_layout.addWidget(line)
        # 添加回复标题
        reply_title = QLabel("评论区jhh")
        reply_title.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px 0;")
        self.detail_layout.addWidget(reply_title)

        # 添加回复
        replies = MockForumData.get_replies(post_id)
        print(replies)

        for reply in replies:
            print(reply)
            reply_widget = SingleReply(reply)
            self.detail_layout.addWidget(reply_widget)

    def create_reply(self):
        if not self.current_post_id:
            return
        content = self.reply_input.toPlainText().strip()
        if not content:
            print("容不能为空")
            return
        MockForumData.create_reply(self.current_post_id, content)
        self.reply_input.clear()
        self.load_post_detail(self.current_post_id)

    def scroll_to_top(self):
        self.detail_scroll.verticalScrollBar().setValue(0)
        self.load_post_detail(self.current_post_id)

    # ------------------------ 页面切换与事件绑定 ------------------------
    def bind_all_events(self):
        # 主页面事件
        self.search_btn.clicked.connect(lambda: self.load_posts(self.search_input.text()))
        self.to_create_btn.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        # 创建页面事件
        self.clear_btn.clicked.connect(self.clear_inputs)
        self.return_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.create_btn.clicked.connect(self.create_post)
        # 详情页面事件
        self.return_btn2.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.up_btn.clicked.connect(self.scroll_to_top)
        self.reply_btn.clicked.connect(self.create_reply)

    def go_to_detail(self, post_id):
        self.load_post_detail(post_id)
        self.stack.setCurrentIndex(1)

# ======================== 运行 ========================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ForumWindow()
    window.setWindowTitle("DIICSU Forum")
    window.resize(900, 700)
    window.show()
    sys.exit(app.exec())