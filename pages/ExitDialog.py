from PySide6.QtWidgets import (
    QDialog, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout
)
from PySide6.QtCore import Qt


class ExitDialog(QDialog):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Exit Practice")
        self.setFixedSize(360, 200)

        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # 标题
        title = QLabel("Exit Practice")
        title.setAlignment(Qt.AlignCenter)
        title.setObjectName("title")

        # 内容
        message = QLabel(
            "Your answers will not be saved.\nAre you sure you want to exit?"
        )
        message.setAlignment(Qt.AlignCenter)
        message.setObjectName("message")

        # 按钮
        cancel_btn = QPushButton("Cancel")
        exit_btn = QPushButton("Exit")

        cancel_btn.setObjectName("cancel")
        exit_btn.setObjectName("exit")

        cancel_btn.clicked.connect(self.reject)
        exit_btn.clicked.connect(self.accept)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(exit_btn)
        button_layout.addStretch()

        layout = QVBoxLayout()
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(15)

        layout.addWidget(title)
        layout.addWidget(message)
        layout.addStretch()
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # 样式
        self.setStyleSheet("""
        QDialog {
            background: white;
            border-radius: 10px;
        }

        QLabel#title {
            font-size: 18px;
            font-weight: bold;
        }

        QLabel#message {
            font-size: 14px;
            color: #444;
        }

        QPushButton {
            min-width: 90px;
            padding: 8px 0px;
            border-radius: 6px;
            font-size: 13px;
        }

        QPushButton#cancel {
            background: #f3f3f3;
            border: 1px solid #d0d0d0;
        }

        QPushButton#cancel:hover {
            background: #e7e7e7;
        }

        QPushButton#exit {
            background: #e53935;
            color: white;
            border: none;
        }

        QPushButton#exit:hover {
            background: #d32f2f;
        }
        """)