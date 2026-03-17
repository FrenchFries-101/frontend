from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile,Signal
#自己创的单词界面
from pages.RecitePages import RecitePage
from pages.ForumPages import ForumWindow
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QFrame, QLabel, QHBoxLayout
from PySide6.QtWidgets import QProgressBar


class MainWindow(QWidget):
    exit_signal = Signal()  # 新增信号
    start_test_signal = Signal()

    def __init__(self):
        super().__init__()

        loader = QUiLoader()
        ui_file = QFile("ui/mainPage.ui")
        ui_file.open(QFile.ReadOnly)

        self.ui = loader.load(ui_file)
        ui_file.close()

        layout = QVBoxLayout()
        layout.addWidget(self.ui)
        self.setLayout(layout)

        self.ui.pushButton_14.clicked.connect(self.start_test)

        self.init_recite_page()
        self.init_forum_page()

        self.ui.Recite_button.clicked.connect(
            lambda: self.ui.stackedWidget.setCurrentIndex(0)
        )

        self.ui.Favourite_button.clicked.connect(
            lambda: self.ui.stackedWidget.setCurrentIndex(1)
        )

        self.ui.Profile_button.clicked.connect(
            lambda: self.ui.stackedWidget.setCurrentIndex(2)
        )

        self.ui.Discussion_button.clicked.connect(
            lambda: self.ui.stackedWidget.setCurrentIndex(3)
        )

        # Exit按钮逻辑
        self.ui.Exit_button.clicked.connect(self.exit_to_login)
        self.generate_cambridge_buttons()

    def exit_to_login(self):
        self.exit_signal.emit()

        # self.ui.btn_listening.clicked.connect(
        #     lambda: self.ui.stackedWidget.setCurrentIndex(3)
        # )

    #创建自己背单词界面
    def init_recite_page(self):
        self.recite_page = RecitePage()
        self.ui.stackedWidget.removeWidget(self.ui.Recite_page)
        self.ui.stackedWidget.insertWidget(0, self.recite_page)

    def init_forum_page(self):
        self.forum_page = ForumWindow()
        self.ui.stackedWidget.removeWidget(self.ui.discussion_page)
        self.ui.stackedWidget.insertWidget(3, self.forum_page.ui)

    def start_test(self):
        self.start_test_signal.emit()

    #这里要不再加上一个清空原本的卡片界面，直接生成剑20的界面
    def generate_cambridge_buttons(self):
        layout = self.ui.scrollAreaWidgetContents_2.layout()

        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i in range(5, 21):
            button = QPushButton(f"Cambridge {i}")

            button.setMinimumHeight(40)

            button.clicked.connect(
                lambda checked=False, cam=i: self.show_tests(cam)
            )

            layout.addWidget(button)
        layout.addStretch()
        self.show_tests(5)

    def show_tests(self, cam):

        layout = self.ui.scrollAreaWidgetContents_3.layout()

        # 清空旧内容
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for test in range(1, 5):
            card = QFrame()
            card.setObjectName("test_card")
            card.setMinimumHeight(80)

            card_layout = QHBoxLayout(card)

            # 左侧布局（标题 + 进度条）
            left_layout = QVBoxLayout()

            title = QLabel(f"Cambridge {cam} Test {test}")

            progress = QProgressBar()
            progress.setMaximum(4)
            progress.setValue(1)  # 示例进度（后面可以改成数据库读取）
            progress.setTextVisible(False)
            progress.setFixedWidth(150)

            left_layout.addWidget(title)
            left_layout.addWidget(progress)

            # 右侧按钮
            enter_btn = QPushButton("Open")

            enter_btn.clicked.connect(
                lambda checked=False, c=cam, t=test: self.show_sections(c, t)
            )

            # 添加到卡片
            card_layout.addLayout(left_layout)
            card_layout.addStretch()
            card_layout.addWidget(enter_btn)

            layout.addWidget(card)

        layout.addStretch()

    def show_sections(self, cam, test):

        layout = self.ui.scrollAreaWidgetContents_3.layout()

        # 清空原来的 Test 列表
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 示例 Section 名称
        section_names = [
            "Multiple Choice",
            "Matching Information",
            "True / False / Not Given",
            "Sentence Completion"
        ]

        # 生成 Section
        for section in range(1, 5):
            card = QFrame()
            card.setObjectName("section_card")
            card.setMinimumHeight(80)

            card_layout = QHBoxLayout(card)

            # 左侧（标题 + section name）
            left_layout = QVBoxLayout()

            title = QLabel(f"Section {section}")
            section_name = QLabel(section_names[section - 1])

            left_layout.addWidget(title)
            left_layout.addWidget(section_name)

            # 右侧按钮
            start_btn = QPushButton("Begin Training")

            start_btn.clicked.connect(
                lambda _, c=cam, t=test, s=section:
                self.start_section(c, t, s)
            )

            card_layout.addLayout(left_layout)
            card_layout.addStretch()
            card_layout.addWidget(start_btn)

            layout.addWidget(card)

        layout.addStretch()

    def start_section(self, cam, test, section):

        print(cam, test, section)

        self.start_test_signal.emit()