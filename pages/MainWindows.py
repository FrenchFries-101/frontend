from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QFrame,
    QLabel,
    QHBoxLayout,
    QSizePolicy,
    QProgressBar,
    QTreeWidgetItem,
    QStackedWidget,
)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Signal, QSize, Qt, QUrl
from PySide6.QtGui import QPixmap, QIcon, QMovie

from pages.RecitePages import RecitePage
from pages.ForumPages import ForumWindow
from pages.SpeakingPage import SpeakingPanel
from pages.RankPage import RankPage
from pages.PetPages import PetHomePage, PetSkinPage
from pages.GroupPlazaPage import GroupPlazaPage
from pages.GroupChatPage import GroupChatPage
from pages.GroupTaskPage import GroupTaskPage
from pages.WordGamePages import *
from service.api import get_cambridge_list, get_tests, get_sections, get_ted_talks, get_user_rank
from utils.path_utils import resource_path
import session



class MainWindow(QWidget):
    exit_signal = Signal()  # 新增信号
    start_test_signal = Signal(int,int,int,int)
    start_ted_signal = Signal(int, str, str)
    open_desktop_calendar_signal = Signal()  # 打开桌面日历信号
    current_cam=0
    current_test=0
    current_section=0

    def __init__(self):
        super().__init__()

        loader = QUiLoader()
        ui_file = QFile(resource_path("ui/mainPage.ui"))
        ui_file.open(QFile.ReadOnly)

        self.ui = loader.load(ui_file)
        ui_file.close()

        layout = QVBoxLayout()
        layout.addWidget(self.ui)
        self.setLayout(layout)

        #self.load_qss()
        self.load_icons()
        self.init_top_bar()

        self.ui.pushButton_14.clicked.connect(self.start_test)


        self.init_recite_page()
        self.init_forum_page()
        self.init_speaking_page()
        self.init_rank_page()
        self.init_pet_pages()
        self.init_group_chat_page()
        self.init_group_task_page()
        self.init_group_plaza_page()

        if hasattr(self.ui, "pushButton_8"):
            self.ui.pushButton_8.setText("TED Talk")
            self.ui.pushButton_8.clicked.connect(self._show_ted_mode)
        if hasattr(self.ui, "pushButton_7"):
            self.ui.pushButton_7.setText("IELTS Test")
            self.ui.pushButton_7.clicked.connect(self._show_ielts_mode)

        self.setup_sidebar_tree()

        self.ui.navTree.itemClicked.connect(self.on_nav_item_clicked)

        self.game_menu = GameMenuPage(self)
        self.start_page = StartGamePage(self)
        self.join_page = JoinPage(self)
        self.board_page = BoardPage(self)
        self.instruction_page = InstructionPage(self)

        self.ui.stackedWidget.addWidget(self.game_menu)
        self.ui.stackedWidget.addWidget(self.start_page)
        self.ui.stackedWidget.addWidget(self.join_page)
        self.ui.stackedWidget.addWidget(self.board_page)
        self.ui.stackedWidget.addWidget(self.instruction_page)

        # 如果你保留了 Exit_button 就连上；删掉也不会报错
        if hasattr(self.ui, "Exit_button"):
            self.ui.Exit_button.clicked.connect(self.exit_to_login)

        self.set_random_avatar(self.ui.label_4)

    def exit_to_login(self):
        self.exit_signal.emit()
    
    def open_desktop_calendar(self):
        self.open_desktop_calendar_signal.emit()

        # self.ui.btn_listening.clicked.connect(
        #     lambda: self.ui.stackedWidget.setCurrentIndex(3)
        # )

    def go_page(self, key: str):
        route = {
            "word_list": 0,
            "listening": 1,
            "speaking": 2,
            "discussion": 3,
            "rank": 7,
            "group_chat": 4,
            "task_board": 5,
            "group_plaza": 6,
        }
        if key == "desktop_calendar":
            self.open_desktop_calendar()
        elif key == "services" and self.pet_home_page:
            self.ui.stackedWidget.setCurrentWidget(self.pet_home_page)
        elif key == "skin_home" and self.pet_skin_page:
            self.ui.stackedWidget.setCurrentWidget(self.pet_skin_page)
        elif key in route:
            self.ui.stackedWidget.setCurrentIndex(route[key])
            if key == "listening":
                self._show_ielts_mode()
        elif key == "game_menu":
            self.ui.stackedWidget.setCurrentWidget(self.game_menu)

    def setup_sidebar_tree(self):
        tree = self.ui.navTree
        tree.clear()
        tree.setHeaderHidden(True)
        tree.setAnimated(True)
        tree.setExpandsOnDoubleClick(False)

        learning = QTreeWidgetItem(["Learning Task"])
        team = QTreeWidgetItem(["Team Work"])
        pets = QTreeWidgetItem(["Pets Home"])
        rank = QTreeWidgetItem(["Leaderboard"])
        rank.setData(0, Qt.UserRole, "rank")

        wl = QTreeWidgetItem(["Word List"])
        wl.setData(0, Qt.UserRole, "word_list")

        li = QTreeWidgetItem(["Listening"])
        li.setData(0, Qt.UserRole, "listening")

        sp = QTreeWidgetItem(["Speaking"])
        sp.setData(0, Qt.UserRole, "speaking")

        ds = QTreeWidgetItem(["Discussion"])
        ds.setData(0, Qt.UserRole, "discussion")

        dc = QTreeWidgetItem(["Calendar"])
        dc.setData(0, Qt.UserRole, "desktop_calendar")

        rk = QTreeWidgetItem(["Leaderboard"])
        rk.setData(0, Qt.UserRole, "rank")

        game = QTreeWidgetItem(["Game"])
        game.setData(0, Qt.UserRole, "game_menu")

        learning.addChildren([wl, li, sp, ds, dc, rk, game])

        my_group = QTreeWidgetItem(["My Group"])
        group_plaza = QTreeWidgetItem(["Group Plaza"])
        group_plaza.setData(0, Qt.UserRole, "group_plaza")

        gc = QTreeWidgetItem(["Group Chat"])
        gc.setData(0, Qt.UserRole, "group_chat")

        tb = QTreeWidgetItem(["Task Board"])
        tb.setData(0, Qt.UserRole, "task_board")

        my_group.addChildren([gc, tb])
        team.addChildren([my_group, group_plaza])

        p1 = QTreeWidgetItem(["Services"])
        p1.setData(0, Qt.UserRole, "services")

        p2 = QTreeWidgetItem(["Skin Home"])
        p2.setData(0, Qt.UserRole, "skin_home")

        pets.addChildren([p1, p2])

        tree.addTopLevelItems([learning, team, pets, rank])
        learning.setExpanded(True)
        team.setExpanded(True)
        my_group.setExpanded(True)
        pets.setExpanded(True)




    def on_nav_item_clicked(self, item, column):
        if item.childCount() > 0:
            item.setExpanded(not item.isExpanded())
            return

        key = item.data(0, Qt.UserRole)
        self.go_page(key)


    #创建自己背单词界面
    def init_recite_page(self):
        self.recite_page = RecitePage()
        self.ui.stackedWidget.removeWidget(self.ui.Recite_page)
        self.ui.stackedWidget.insertWidget(0, self.recite_page)
        self.recite_page.points_changed.connect(self.update_coin_label)

    def init_forum_page(self):
        self.forum_page = ForumWindow()
        self.ui.stackedWidget.removeWidget(self.ui.discussion_page)
        self.ui.stackedWidget.insertWidget(3, self.forum_page.ui)
    
    def init_speaking_page(self):
        self.speaking_page = SpeakingPanel()
        self.ui.stackedWidget.removeWidget(self.ui.Profile_page)
        self.ui.stackedWidget.insertWidget(2, self.speaking_page)

    def init_rank_page(self):
        self.rank_page = RankPage()
        self.ui.stackedWidget.removeWidget(self.ui.Rank)
        self.ui.stackedWidget.insertWidget(7, self.rank_page)


    def init_group_chat_page(self):
        self.group_chat_page = GroupChatPage()
        self.ui.stackedWidget.removeWidget(self.ui.GroupDiscuss)
        self.ui.stackedWidget.insertWidget(4, self.group_chat_page)

    def init_group_task_page(self):
        self.group_task_page = GroupTaskPage()
        self.ui.stackedWidget.removeWidget(self.ui.GroupTask)
        self.ui.stackedWidget.insertWidget(5, self.group_task_page)

    def init_group_plaza_page(self):
        self.group_plaza_page = GroupPlazaPage()
        self.ui.stackedWidget.removeWidget(self.ui.GroupPlaza)
        self.ui.stackedWidget.insertWidget(6, self.group_plaza_page)


    def init_pet_pages(self):
        self.pet_home_page = None
        self.pet_skin_page = None

    def start_test(self):


        self.start_test_signal.emit()

    #这里要不再加上一个清空原本的卡片界面，直接生成剑20的界面
    def generate_cambridge_buttons(self):
        layout = self.ui.scrollAreaWidgetContents_2.layout()

        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        cambridge_list = get_cambridge_list()

        for cam in cambridge_list:
            cam_id = cam["cambridge_id"]
            button = QPushButton(f"Cambridge {cam_id}")
            button.setMinimumHeight(40)
            print("cam",cam_id)
            button.clicked.connect(
                lambda checked=False, c=cam: self.show_tests(c)
            )

            layout.addWidget(button)

        layout.addStretch()

        print(cambridge_list)
        # 默认加载第一个
        if cambridge_list:
            self.show_tests(cambridge_list[4])

    def show_tests(self, cam):

        layout = self.ui.scrollAreaWidgetContents_3.layout()

        # 清空旧内容
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        user_id = session.user["id"]
        cam_id = cam["cambridge_id"]

        print("user_id:", user_id)
        print("cam_id:", cam_id)

        tests = get_tests(cam_id, user_id)

        for t in tests:
            print(t, type(t))
            test_no = t["test_no"]
            test_id=t["test_id"]
            total_sections = t["total_sections"]
            completed = t["completed_sections"]

            card = QFrame()
            card.setObjectName("test_card")
            card.setMinimumHeight(80)

            card_layout = QHBoxLayout(card)

            left_layout = QVBoxLayout()
            left_layout.setSpacing(6)

            title = QLabel(f"Cambridge {cam_id} Test {test_no}")

            progress = QProgressBar()
            progress.setMaximum(total_sections)
            progress.setValue(completed)
            progress.setTextVisible(False)
            progress.setFixedWidth(150)

            left_layout.addWidget(title)
            left_layout.addWidget(progress)

            enter_btn = QPushButton("Open")

            enter_btn.clicked.connect(
                lambda checked=False, c=cam_id, t=test_id: self.show_sections(c, t)
            )

            card_layout.addLayout(left_layout)
            card_layout.addStretch()
            card_layout.addWidget(enter_btn)

            layout.addWidget(card)

        layout.addStretch()

    def show_sections(self, cam, test):

        layout = self.ui.scrollAreaWidgetContents_3.layout()

        # 清空原来的 Section 列表
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        import session
        user_id=session.user["id"]

        # 这里改了
        sections = get_sections(test, user_id)

        for sec in sections:
            print(sec)

            section_number = sec["section_no"]
            section_name = sec["section_name"]
            section_id = sec["section_id"]
            correct_num = sec["correct_num"]
            is_completed = sec["is_completed"]

            card = QFrame()
            card.setObjectName("section_card")
            card.setMinimumHeight(110)
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

            card_layout = QHBoxLayout(card)
            left_layout = QVBoxLayout()

            title = QLabel(f"Section {section_number}")
            title.setObjectName("section_title")

            name_label = QLabel(section_name)
            name_label.setObjectName("section_name")

            # 新增：成绩 / 状态
            if is_completed:
                score_label = QLabel(f"Score: {correct_num}/10  ✔")
            else:
                score_label = QLabel("Not completed")

            start_btn = QPushButton("Begin Training")
            score_label.setObjectName("section_score")

            left_layout.addWidget(title)
            left_layout.addWidget(name_label)
            left_layout.addWidget(score_label)  # 新增这一行

            start_btn.clicked.connect(
                lambda _, c=cam, t=test, s=section_id, ss=section_number:
                self.start_section(c, t, s, ss)
            )

            card_layout.addLayout(left_layout)
            card_layout.addStretch()
            card_layout.addWidget(start_btn)

            layout.addWidget(card)

        layout.addStretch()

    def start_section(self, cam, test, section, section_number):

        self.current_cam = cam
        self.current_test = test
        self.current_section = section
        self.current_sectionNumber=section_number

        print(cam, test, section)
        print(type(cam), type(test), type(section))
        self.start_test_signal.emit(cam,int(test),int(section),int(section_number))

    def set_random_avatar(self, label):
        import random

        index = random.randint(1, 7)
        path = resource_path(f"resources/icons/teenager{index}.png")

        pixmap = QPixmap(path)

        # ✅ QLabel 比图片大
        label.setFixedSize(100, 100)

        # ✅ 图片缩小一点（关键！）
        pixmap = pixmap.scaled(
            70, 70,  # 比 label 小
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        label.setPixmap(pixmap)

        # ✅ 居中
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def load_icons(self):
        self.ui.Exit_button.setIcon(QIcon(resource_path("resources/icons/exit.png")))
        # 设置图标大小
        self.ui.Exit_button.setIconSize(QSize(20, 20))

        logo_path = resource_path("resources/icons/arctic-fox.png")
        logo_url = QUrl.fromLocalFile(logo_path).toString()

        self.ui.label.setText(
            f'<span>'
            f'<img src="{logo_url}" width="30" height="30" '
            f'style="vertical-align:middle; margin-right:8px;">'
            f'<span style="vertical-align:middle;">DIIFOX</span>'
            f'</span>'
        )
        self.ui.label.setAlignment(Qt.AlignCenter)

    def load_data(self):
        print("开始加载Cambridge数据...")

        # 加载数据
        self.generate_cambridge_buttons()

    def set_user(self, user):
        self.user = user
        self.user_name = user['username']
        self.ui.label_13.setText(self.user_name)
        try:
            rank_data = get_user_rank(user['id'])
            self.update_coin_label(rank_data.get("points", 0))
        except Exception:
            pass
        # 更新排行榜页面的用户信息
        if hasattr(self, 'rank_page') and hasattr(self.rank_page, 'set_user'):
            print("MainWindow set_user called, updating rank page")
            self.rank_page.set_user(user)
        # 初始化 pet 页面（需要 user_id）
        if self.pet_home_page is None:
            user_id = user.get("id", 0)
            print(f"[PetPages] Initializing pet pages for user_id={user_id}")
            self.pet_home_page = PetHomePage(user_id)
            self.pet_skin_page = PetSkinPage(user_id)
            self.ui.stackedWidget.addWidget(self.pet_home_page)
            self.ui.stackedWidget.addWidget(self.pet_skin_page)

    def update_coin_label(self, points: int):
        self.ui.coinValueLabel.setText(str(points))

    def clear_data(self):
        # 清空用户名
        self.ui.label_13.setText("")

        # 清空 Cambridge 列表
        layout = self.ui.scrollAreaWidgetContents_2.layout()
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 清空 Test/Section 列表
        layout2 = self.ui.scrollAreaWidgetContents_3.layout()
        while layout2.count():
            item = layout2.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def init_top_bar(self):
    # 连续学习文案
        self.ui.streakLabel.setText("Learning 2 days")

    # 金币 GIF
        self.coin_movie = QMovie(resource_path("resources/icons/Coin.gif"))
        self.ui.coinGifLabel.setMovie(self.coin_movie)
        self.ui.coinGifLabel.setFixedSize(50, 50)
        self.ui.coinGifLabel.setScaledContents(True)
        self.coin_movie.start()

    # 金币数量
        self.ui.coinValueLabel.setText("200")


    def _show_ielts_mode(self):
        self.ui.book_scroll.show()
        self.generate_cambridge_buttons()

    def _show_ted_mode(self):
        self.ui.book_scroll.hide()
        self._load_ted_talks()

    def _load_ted_talks(self):
        layout = self.ui.scrollAreaWidgetContents_3.layout()
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        talks = get_ted_talks()
        for talk in talks:
            card = self._make_ted_card(talk)
            layout.addWidget(card)
        layout.addStretch()

    def _make_ted_card(self, talk):
        _TALK_SUBTITLES = {
            1: "Why coding education should be accessible to every student",
            2: "Unpacking the basics of quantum computing in everyday language",
            3: "How building useless things sparks creativity and joy",
            4: "The critical mistakes engineers must avoid to prevent failure",
            5: "Rethinking how we design and build our physical world",
            6: "How thoughtful city planning shapes sustainable urban futures",
            7: "Engineering solutions for more eco-friendly road infrastructure",
            8: "How autonomous vehicles and smart systems will transform travel",
            9: "The simple traffic technique that reduces congestion and saves time",
            10: "Creator-produced content on modern challenges and opportunities",
        }

        talk_id = int(talk.get("talk_id") or talk.get("id") or 0)
        title = talk.get("title") or f"TED Talk {talk_id}"
        audio_path = talk.get("audio_path") or ""
        subtitle = _TALK_SUBTITLES.get(talk_id, "")

        card = QFrame()
        card.setObjectName("test_card")
        card.setMinimumHeight(90)

        card_layout = QHBoxLayout(card)

        left_layout = QVBoxLayout()
        left_layout.setSpacing(6)

        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setObjectName("label_7")
            subtitle_label.setWordWrap(True)
            left_layout.addWidget(subtitle_label)


        title_label = QLabel(title)
        title_label.setObjectName("label_8")
        left_layout.addWidget(title_label)

        open_btn = QPushButton("Open")
        open_btn.clicked.connect(
            lambda _, tid=talk_id, t=title, a=audio_path: self.start_ted_signal.emit(tid, t, a)
        )

        card_layout.addLayout(left_layout)
        card_layout.addStretch()
        card_layout.addWidget(open_btn)

        return card

    def goto(self, page):
        if page == "game_menu":
            self.ui.stackedWidget.setCurrentWidget(self.game_menu)
        elif page == "start":
            self.ui.stackedWidget.setCurrentWidget(self.start_page)
        elif page == "join":
            self.ui.stackedWidget.setCurrentWidget(self.join_page)
        elif page == "board":
            self.ui.stackedWidget.setCurrentWidget(self.board_page)
        elif page == "instruction":
            self.ui.stackedWidget.setCurrentWidget(self.instruction_page)
