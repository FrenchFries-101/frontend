from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile,Signal
#自己创的单词界面
from pages.RecitePages import RecitePage
from pages.ForumPages import ForumWindow
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QFrame, QLabel, QHBoxLayout
from PySide6.QtWidgets import QProgressBar
from service.api import get_cambridge_list, get_tests, get_sections
import random
from PySide6.QtGui import QPixmap
import session
from PySide6.QtCore import Qt
from utils.path_utils import resource_path


class MainWindow(QWidget):
    exit_signal = Signal()  # 新增信号
    start_test_signal = Signal(int,int,int)
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

        self.load_qss()

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
        self.set_random_avatar(self.ui.label_4)
        self.user_name=session.user['username']
        print(self.user_name)
        self.ui.label_13.setText(f"{self.user_name}")

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

        # 清空原来的 Test 列表
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        sections = get_sections(cam, test)

        for sec in sections:
            print(sec)
            section_number = sec["section_no"]
            section_name = sec["section_name"]
            section_id=sec["section_id"]

            card = QFrame()
            card.setObjectName("section_card")
            card.setMinimumHeight(80)

            card_layout = QHBoxLayout(card)

            left_layout = QVBoxLayout()

            title = QLabel(f"Section {section_number}")
            name_label = QLabel(section_name)

            left_layout.addWidget(title)
            left_layout.addWidget(name_label)

            start_btn = QPushButton("Begin Training")

            start_btn.clicked.connect(
                lambda _, c=cam, t=test, s=section_id:
                self.start_section(c, t, s)
            )

            card_layout.addLayout(left_layout)
            card_layout.addStretch()
            card_layout.addWidget(start_btn)

            layout.addWidget(card)

        layout.addStretch()

    def start_section(self, cam, test, section):

        self.current_cam = cam
        self.current_test = test
        self.current_section = section

        print(cam, test, section)
        print(type(cam), type(test), type(section))
        self.start_test_signal.emit(cam,int(test),int(section))

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

    def load_qss(self):
        # 获取所有图标路径，Windows 路径转换成 /
        book_icon = resource_path("resources/icons/book-alt.png").replace("\\", "/")
        headphones_icon = resource_path("resources/icons/headphones.png").replace("\\", "/")
        user_icon = resource_path("resources/icons/user-speaking.png").replace("\\", "/")
        bank_icon = resource_path("resources/icons/bank.png").replace("\\", "/")
        exit_icon = resource_path("resources/icons/exit.png").replace("\\", "/")

        # 使用 f-string 安全替换
        qss = f"""
        QPushButton#Recite_button {{
            qproperty-icon: url({book_icon});
            qproperty-iconSize: 20px 20px;
        }}

        QPushButton#Favourite_button {{
            qproperty-icon: url({headphones_icon});
            qproperty-iconSize: 20px 20px;
        }}

        QPushButton#Profile_button {{
            qproperty-icon: url({user_icon});
            qproperty-iconSize: 20px 20px;
        }}

        QPushButton#Discussion_button {{
            qproperty-icon: url({bank_icon});
            qproperty-iconSize: 20px 20px;
        }}

        QPushButton#Exit_button {{
            qproperty-icon: url({exit_icon});
            qproperty-iconSize: 20px 20px;
        }}
        """

        self.setStyleSheet(qss)