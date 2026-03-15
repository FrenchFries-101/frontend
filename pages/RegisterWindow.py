from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Signal

class RegisterWindow(QWidget):

    register_success = Signal()  # 注册成功信号
    go_login = Signal()          # 点击“已有账号？登录”信号

    def __init__(self):
        super().__init__()

        loader = QUiLoader()
        ui_file = QFile("ui/register.ui")
        ui_file.open(QFile.ReadOnly)

        self.ui = loader.load(ui_file)
        ui_file.close()

        layout = QVBoxLayout()
        layout.addWidget(self.ui)
        self.setLayout(layout)

        # 点击注册按钮
        self.ui.pushButton.clicked.connect(self.register)

        # 点击“已有账号？登录”按钮
        if hasattr(self.ui, "pushButton_2"):  # 你可以给 login 按钮命名 pushButton_login
            self.ui.pushButton_2.clicked.connect(lambda: self.go_login.emit())

    def register(self):
        print("register success")
        self.register_success.emit()