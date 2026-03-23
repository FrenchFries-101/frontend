from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Signal
from service.api import register as register_api
from utils.path_utils import resource_path

class RegisterWindow(QWidget):

    register_success = Signal()  # 注册成功信号
    go_login = Signal()          # 点击“已有账号？登录”信号

    def __init__(self):
        super().__init__()

        loader = QUiLoader()
        ui_file = QFile(resource_path("ui/register.ui"))
        ui_file.open(QFile.ReadOnly)

        self.ui = loader.load(ui_file)
        ui_file.close()

        layout = QVBoxLayout()
        layout.addWidget(self.ui)
        self.setLayout(layout)

        self.load_qss()

        # 点击注册按钮
        self.ui.pushButton.clicked.connect(self.register)

        # 点击“已有账号？登录”按钮
        if hasattr(self.ui, "pushButton_2"):  # 你可以给 login 按钮命名 pushButton_login
            self.ui.pushButton_2.clicked.connect(lambda: self.go_login.emit())

    def register(self):
        # 1️⃣ 获取输入
        email = self.ui.lineEdit.text().strip()
        password = self.ui.lineEdit_2.text().strip()
        confirm_password = self.ui.lineEdit_3.text().strip()
        username = self.ui.lineEdit_4.text().strip()

        # 2️⃣ 清空提示
        self.ui.label_7.setText("")
        self.ui.label_7.setStyleSheet("color: red;")

        # 3️⃣ 判空
        if not email or not password or not confirm_password or not username:
            self.ui.label_7.setText("All fields are required")
            return

        # 4️⃣ 判断两次密码是否一致
        if password != confirm_password:
            self.ui.label_7.setText("Passwords do not match")
            return

        # 5️⃣ 密码长度（建议和后端一致）
        if len(password) < 6:
            self.ui.label_7.setText("Password must be at least 6 characters")
            return

        # （可选）简单邮箱格式校验
        if "@" not in email:
            self.ui.label_7.setText("Invalid email format")
            return

        try:
            # 6️⃣ 调用后端接口
            res = register_api(username, email, password)

            # 7️⃣ 成功提示
            self.ui.label_7.setStyleSheet("color: green;")
            self.ui.label_7.setText("Register success!")

            print("Register success:", res)

            # 8️⃣ 发信号（可以跳登录页）
            #self.register_success.emit()

        except Exception as e:
            # 9️⃣ 后端错误提示（比如用户名重复）
            self.ui.label_7.setStyleSheet("color: red;")
            self.ui.label_7.setText(str(e))

    def load_qss(self):
        bg_path = resource_path("resources/images/login-picture2.jpg").replace("\\", "/")

        qss = f"""
        QWidget#Form {{
            border-image: url({bg_path});
        }}
        """

        self.setStyleSheet(qss)