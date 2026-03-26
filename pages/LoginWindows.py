from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Signal
from service.api import register,login,get_current_user
from PySide6.QtWidgets import QMessageBox
import session
from utils.path_utils import resource_path
from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QPixmap


class LoginWindow(QWidget):

    login_success = Signal()

    def __init__(self):
        super().__init__()

        loader = QUiLoader()
        ui_file = QFile(resource_path("ui/login.ui"))
        ui_file.open(QFile.ReadOnly)

        self.ui = loader.load(ui_file)
        ui_file.close()

        # ===== 背景图 QLabel =====
        self.bg_label = QLabel(self)
        pixmap = QPixmap(resource_path("resources/images/login-picture2.jpg"))
        self.bg_label.setPixmap(pixmap)
        self.bg_label.setScaledContents(True)
        self.bg_label.lower()  # 放到最底层

        layout = QVBoxLayout()
        layout.addWidget(self.ui)
        self.setLayout(layout)

        self.ui.pushButton.clicked.connect(self.login)

    def login(self):
        # 1️⃣ 获取输入
        username = self.ui.lineEdit.text().strip()
        password = self.ui.lineEdit_2.text().strip()

        self.ui.label_5.setText("")

        # 2️⃣ 判空
        if not username or not password:
            self.ui.label_5.setStyleSheet("color: red;")
            self.ui.label_5.setText("username or password cannot be empty")
            return

        try:
            # 3️⃣ 调用后端 API
            res = login(username, password)

            # 4️⃣ 获取 token
            token = res["access_token"]

            print("Login success, token:", token)

            # 👉 可以存起来（后面用）
            session.token=token

            # （可选）立刻获取用户信息
            user = get_current_user(token)
            session.user=user
            print("Current user:", user)

            # 5️⃣ 发信号（跳转主界面）
            self.login_success.emit()

        except Exception as e:
            self.ui.label_5.setStyleSheet("color: red;")
            self.ui.label_5.setText(str(e))

    def load_qss(self):
        bg_path = resource_path("resources/images/login-picture2.jpg").replace("\\", "/")
        import os
        print("背景图片路径:", bg_path)
        print("文件存在吗?", os.path.exists(bg_path))

        qss = f"""
        QWidget#Form {{
            border-image: url("{bg_path}");
        }}
        """

        self.setStyleSheet(qss)

    def resizeEvent(self, event):
        self.bg_label.setGeometry(self.rect())
        super().resizeEvent(event)