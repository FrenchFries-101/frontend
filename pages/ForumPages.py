import os
import session
from utils.path_utils import resource_path
import sys
from PySide6.QtWidgets import QMessageBox
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout,
    QScrollArea, QLabel, QPushButton, QLineEdit, QTextEdit, QStackedWidget, QSizePolicy
)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Qt
from components.SinglePost import SinglePost
from components.SingleReply import SingleReply
from components.SingleDetailedPost import SingleDetailedPost
from service.api_forum import get_posts,get_post_detail,search_posts,get_replies,create_post,reply_post,like_post,like_reply
import session


# ========================假数据========================
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

/* 按钮 like_button*/
QPushButton:not(#like_button){
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


    def load_full_ui(self):
        # 一次性加载整个postPage.ui
        loader = QUiLoader()
        # ui_path = os.path.join(
        #     os.path.dirname(os.path.dirname(__file__)),  # 上一级目录（AgileProject）
        #     "ui",
        #     "postPage.ui"
        # )

        ui_path = resource_path("ui/postPage.ui")
        ui_file = QFile(ui_path)
        if not ui_file.open(QFile.ReadOnly):
            print(f"Can't open ui file(ForumPages): {ui_path}")
            return
        self.ui = loader.load(ui_file, self)
        ui_file.close()


        self.post_scroll = self.ui.findChild(QScrollArea, "post_scrollArea")
        self.post_container = self.ui.findChild(QWidget, "post_contents")

        #获取已有布局，如果没有就创建
        self.post_layout = self.post_container.layout()
        if self.post_layout is None:
            self.post_layout = QVBoxLayout(self.post_container)
        self.post_layout.setAlignment(Qt.AlignTop)


        #取出stackedWidget（三个页面都在里面）
        self.stack = self.ui.findChild(QStackedWidget, "stackedWidget")

        #取出三个子页面
        self.forum_main = self.stack.findChild(QWidget, "forum_main")
        self.forum_create = self.stack.findChild(QWidget, "forum_create")
        self.forum_detail = self.stack.findChild(QWidget, "forum_detail")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.ui)



    def init_scroll_area(self):
        # 获取已有布局，如果没有就创建
        self.post_layout = self.post_container.layout()
        if self.post_layout is None:
            self.post_layout = QVBoxLayout(self.post_container)
        self.post_layout.setAlignment(Qt.AlignTop)




    def init_pages(self):
        # 初始化主页面
        self.init_main_page()
        # 初始化创建页面
        self.init_create_page()
        # 初始化详情页面
        self.init_detail_page()
        # 默认显示主页面
        self.stack.setCurrentIndex(0)



    # ------------------------ 主页面逻辑 ------------------------
    def init_main_page(self):
        # 查找主页面控件
        self.search_input = self.forum_main.findChild(QLineEdit, "search_input")
        self.search_btn = self.forum_main.findChild(QPushButton, "search_button")
        self.to_create_btn = self.forum_main.findChild(QPushButton, "to_create_botton")
        self.post_scroll = self.ui.findChild(QScrollArea, "post_scrollArea")
        self.post_container = self.ui.findChild(QWidget, "post_contents")

        #按钮图片-搜索帖子
        self.search_btn.setIcon(QIcon(self.get_icon("search.png")))
        self.search_btn.setToolTip("Search")

        # 设置滚动区域
        self.post_scroll.setWidgetResizable(True)

        # 获取已有布局，如果没有就创建
        self.post_layout = self.post_container.layout()
        if self.post_layout is None:
            self.post_layout = QVBoxLayout(self.post_container)
        self.post_layout.setAlignment(Qt.AlignTop)

        # 初始化帖子列表
        self.load_posts()

    # def load_posts(self, keyword=""):
    #     # 清空旧内容
    #     while self.post_layout.count():
    #         child = self.post_layout.takeAt(0)
    #         if child.widget():
    #             child.widget().deleteLater()
    #
    #     #替换1: 这里要替换成 get_posts
    #     # posts = MockForumData.get_posts(keyword)
    #     posts = get_posts()
    #     print(posts)
    #
    #     for post in posts:
    #         post_widget = SinglePost(post)
    #         post_widget.clicked.connect(lambda p=post: self.go_to_detail(p["id"]))
    #         self.post_layout.addWidget(post_widget)
    #
    #     print("posts loaded:", [p["title"] for p in posts])

    def load_posts(self, keyword=""):

        # 清空旧内容
        while self.post_layout.count():
            child = self.post_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # 接口1/2：调接口&search 接口合并
        if keyword:
            response = search_posts(keyword)
        else:
            response = get_posts()

        print("RAW:", response)

        #只取posts
        posts = response.get("posts", [])

        #存起来（后面详情页用）
        self.posts_cache = {p["id"]: p for p in posts}

        for post in posts:
            #处理 None（你数据里有）
            fixed_post = {
                "id": post["id"],
                "title": post.get("title", ""),
                "author": post.get("author") or "Unknown",
                "time": post.get("time", ""),
                "likes": post.get("likes", 0)
            }

            post_widget = SinglePost(fixed_post)

            # 直接传 id（改了 Signal）
            post_widget.clicked.connect(
                lambda _, pid=fixed_post["id"]: self.go_to_detail(pid)
            )

            self.post_layout.addWidget(post_widget)

        print("loaded:", len(posts))


    # ------------------------ 创建页面逻辑 ------------------------
    def init_create_page(self):
        # 查找创建页面控件
        self.clear_btn = self.forum_create.findChild(QPushButton, "clear_button")
        self.return_btn = self.forum_create.findChild(QPushButton, "return_button")
        self.create_btn = self.forum_create.findChild(QPushButton, "create_button")
        self.title_input = self.forum_create.findChild(QLineEdit, "title_input")
        self.content_input = self.forum_create.findChild(QTextEdit, "content_input")

        # 按钮图片-发布
        self.create_btn.setIcon(QIcon(self.get_icon("plane.png")))
        self.create_btn.setToolTip("Publish your post")

        # 按钮图片-清空
        self.clear_btn.setIcon(QIcon(self.get_icon("broom.png")))
        self.clear_btn.setToolTip("Clear the input content")

        # 按钮图片-返回
        self.return_btn.setIcon(QIcon(self.get_icon("bank.png")))
        self.return_btn.setToolTip("Return to the forum homepage")

        # 设置标题
        title_label = self.forum_create.findChild(QLabel, "create_title_label")
        if title_label:
            title_label.setText("Release a new post")

    def clear_inputs(self):
        self.title_input.clear()
        self.content_input.clear()

    #替换5:创建帖子
    def create_post(self):
        title = self.title_input.text().strip()
        content = self.content_input.toPlainText().strip()
        if not title or not content:
            print("title and contents cannot be vacant")
            QMessageBox.warning(self, "Failed", " Unable to submit blank content")
            return


        # MockForumData.create_post(title, content)
        #创建create的接口！
<<<<<<< HEAD
        create_post(title, content, session.user["id"])#记得改用户id
=======
        create_post(title, content, session.user)#记得改 用户id
>>>>>>> 0accfe7bf6d48f4e7c49ff6708047d67f56f3769
        QMessageBox.information(self, "Success", "Release successful!")
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

        #按钮图片-回复
        self.reply_btn.setIcon(QIcon(self.get_icon("pen.png")))
        self.reply_btn.setToolTip("Post a reply")
        #按钮图片-返回键
        self.return_btn2.setIcon(QIcon(self.get_icon("bank.png")))
        self.return_btn2.setToolTip("Return to the forum homepage")
        #按钮图片-刷新
        self.up_btn.setIcon(QIcon(self.get_icon("refresh.png")))
        self.up_btn.setToolTip("Refresh this page")

        self.detail_layout = self.detail_container.layout()
        if self.detail_layout is None:
            self.detail_layout = QVBoxLayout(self.detail_container)
        self.detail_layout.setAlignment(Qt.AlignTop)

        # 设置滚动区域布局
        self.detail_layout.setSpacing(15)
        self.current_post_id = None



    #显示帖子内容
    def load_post_detail(self, post_id):
        self.current_post_id = post_id
        print(f"post_id{post_id}")

        #清空旧内容
        while self.detail_layout.count():
            child = self.detail_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # 加载帖子详情
        #替换3: get_post_detail(post_id)
        # post = MockForumData.get_post_detail(post_id)
        post = get_post_detail(post_id)
        if not post:
            print("post do not exsit")
            return
        print(f"post raw detail information：{post}")

        #字段匹配清洗
        fixed_post = {
            "id": post.get("id"),
            "title": post.get("title", ""),
            "author": post.get("author") or "Unknown",
            "time": post.get("time", ""),
            "content": post.get("content", ""),
            "likes": post.get("likes", 0)
        }


        self.detail_title.setText(f"Post Details")

        # 添加帖子组件
        post_widget = SingleDetailedPost(fixed_post)
        self.detail_layout.addWidget(post_widget)
        #连接点赞逻辑？
        post_widget.liked.connect(self.handle_like_post)

        # style: 添加分割线
        line = QLabel()
        line.setStyleSheet("background-color: #E0E0E0; height: 1px;")
        self.detail_layout.addWidget(line)
        # style: 添加回复标题
        reply_title = QLabel("Comments")
        reply_title.setStyleSheet("""
            color: #888888;                 
            font-size: 14px;
            font-weight: bold;
            font-family: Consolas, "Courier New", monospace;  
            margin: 10px 0 10px 20px;       
        """)
        self.detail_layout.addWidget(reply_title)

        # 替换4：get_replies(post_id)
        # replies = MockForumData.get_replies(post_id)
        replies = get_replies(fixed_post['id'])
        print(replies)

        for reply in replies:
            #测试
            print(reply)
            reply_widget = SingleReply(reply)
            #点赞信号！！连接？
            reply_widget.liked.connect(self.handle_like_reply)
            self.detail_layout.addWidget(reply_widget)


    #创建回复
    def create_reply(self):
        if not self.current_post_id:
            return
        content = self.reply_input.toPlainText().strip()
        if not content:
            print("容不能为空")
            return

        #替换6: def reply_post(post_id, content, user_id)
        # MockForumData.create_reply(self.current_post_id, content)\
<<<<<<< HEAD
        reply_post(self.current_post_id, content, session.user["id"])#记得改用户id
=======
        reply_post(self.current_post_id, content, session.user)#记得改 用户id
>>>>>>> 0accfe7bf6d48f4e7c49ff6708047d67f56f3769
        QMessageBox.information(self, "Success", "Release successful!")
        self.reply_input.clear()
        self.load_post_detail(self.current_post_id)


    #button们 和 their events
    def bind_all_events(self):

        #替换2 改成search_posts(keyword, page=1, page_size=20):
        self.search_btn.clicked.connect(lambda: self.load_posts(self.search_input.text()))
        self.to_create_btn.clicked.connect(lambda: self.stack.setCurrentIndex(2))

        # 创建页面事件
        self.clear_btn.clicked.connect(self.clear_inputs)
        self.return_btn.clicked.connect(self.back_to_main)
        self.create_btn.clicked.connect(self.create_post)
        # 详情页面事件
        self.return_btn2.clicked.connect(self.back_to_main)
        self.up_btn.clicked.connect(self.scroll_to_top)
        self.reply_btn.clicked.connect(self.create_reply)

    # 新增方法
    def back_to_main(self):
        self.stack.setCurrentIndex(0)  # 切回主页
        self.load_posts()  # 重新加载帖子

    #inner function change pages
    def go_to_detail(self, post_id):
        self.load_post_detail(post_id)
        self.stack.setCurrentIndex(1)

    #inner function: get icon images
    # def get_icon(self, name):
    #     base_dir = os.path.dirname(__file__)
    #     return os.path.join(base_dir, "..","resources", "icons", name)

    def get_icon(self, name):
        return resource_path(f"resources/icons/{name}")

    #inner function
    def scroll_to_top(self):
        self.detail_scroll.verticalScrollBar().setValue(0)
        self.load_post_detail(self.current_post_id)

    #点赞帖子
    # def handle_like_post(self, post_id):
    #     res = like_post(post_id, 1)
    #
    #     if res:
    #         QMessageBox.information(self, "Success", "点赞成功")
    #         self.load_post_detail(post_id)  # 或局部更新
    #     else:
    #         QMessageBox.warning(self, "Error", "点赞失败")


    # 点赞帖子
    # def handle_like_post(self, post_id):
    #     res = like_post(post_id, 1)
    #
    #     if res.get("status") == "ok":
    #
    #         widget = self.detail_container.findChild(SingleDetailedPost)
    #
    #         if widget:
    #             # ✅ 用后端 action 决定状态
    #             if res["action"] == "liked":
    #                 widget.liked_by_user = True
    #             else:
    #                 widget.liked_by_user = False
    #
    #             # ✅ 更新 UI（统一走组件方法）
    #             widget.update_like_ui()
    #
    #
    #             # ✅ 更新点赞数
    #             widget.likes_label.setText(str(res["likes"]))
    #
    #             # ✅ 恢复按钮
    #             widget.like_btn.setEnabled(True)
    #
    #     else:
    #         QMessageBox.warning(self, "Error", "点赞失败")
    #

    def handle_like_post(self, post_id):
        res = like_post(post_id, session.user) #记得改 用户id

        if res.get("status") == "ok":
            widget = self.detail_container.findChild(SingleDetailedPost)

            if widget:
                # ⭐ 直接反转状态
                widget.liked_by_user = not widget.liked_by_user

                widget.update_like_ui()

                # 更新点赞数（后端给的是对的）
                widget.likes_label.setText(str(res["likes"]))

                widget.like_btn.setEnabled(True)

        else:
            QMessageBox.warning(self, "Error", "点赞失败")


    #点赞评论
    # def handle_like_reply(self, reply_id):
    #     print(f"点赞 reply_id: {reply_id}")
    #
    #     res = like_reply(reply_id, 1)  #记得改user_id
    #     if res:
    #         print("点赞成功:", res)
    #     else:
    #         QMessageBox.warning(self, "Error", "点赞失败")
    #         self.load_post_detail(self.current_post_id)

    def handle_like_reply(self, reply_id):
        res = like_reply(reply_id, session.user) #记得改 用户id

        if res.get("status") == "ok":

            replies = self.detail_container.findChildren(SingleReply)

            for widget in replies:
                if widget.property("reply_id") == reply_id:
                    # ⭐ 只在这里改一次！
                    widget.liked_by_user = not widget.liked_by_user

                    widget.update_like_ui()
                    widget.like_label.setText(str(res["likes"]))
                    widget.like_btn.setEnabled(True)

                    break

# ======================== 运行 ========================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ForumWindow()
    window.setWindowTitle("DIICSU Forum")
    window.resize(900, 700)
    window.show()
    sys.exit(app.exec())