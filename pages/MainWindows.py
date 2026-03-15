from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile,Signal
#自己创的单词界面
from pages.RecitePages import RecitePage
from pages.ForumPages import ForumWindow


class MainWindow(QWidget):
    exit_signal = Signal()  # 新增信号

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