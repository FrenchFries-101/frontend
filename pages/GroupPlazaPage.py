from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFrame,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QDialog,
    QTableWidgetItem,
    QInputDialog,
    QLineEdit,
    QStackedWidget,
    QFileDialog,
    QGridLayout,
    QScrollArea,
    QComboBox,
    QSpinBox,
    QTextEdit,
    QRadioButton,
    QButtonGroup,
    QSizePolicy,
)

from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Qt, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtGui import QPixmap, QIcon

import base64
import mimetypes

import requests


import session

from service.api import BASE_URL, get_groups, create_group, join_group, get_group_members, upload_group_icon, upload_group_images


from utils.path_utils import resource_path



GROUP_PLAZA_STYLE = """
QWidget {
    background: #fff6ea;
    color: #4a3b1f;
}

QLabel {
    background: transparent;
}


QWidget#searchBar, QWidget#bottomBar {
    background: #fff9f0;
    border: 1px solid #ffe08e;
    border-radius: 12px;
}

QLineEdit {
    background: #fffdf7;
    border: 1px solid #f1d38a;
    border-radius: 8px;
    padding: 8px 10px;
    font-size: 13px;
}

QLineEdit:focus {
    border: 1px solid #e0b84f;
}

QPushButton {
    border: 1px solid #f1d38a;
    border-radius: 8px;
    padding: 8px 12px;
    background: #ffe8a8;
    color: #5b4518;
}

QPushButton:hover {
    background: #ffe08e;
    border: 1px solid #dfb75b;
}

QPushButton:pressed {
    background: #f8d36e;
}

QFrame#group_card {
    background: #fffaf0;
    border: 1px solid #ffe08e;
    border-radius: 12px;
    padding: 8px;
}

QFrame#group_card:hover {
    border: 1px solid #dfb75b;
    background: #fff3d4;
}

QLabel#group_name {
    font-size: 15px;
    font-weight: 700;
    color: #3b2f18;
}

QLabel#group_meta {
    font-size: 12px;
    color: #7a6640;
}

QLabel#group_status_ok {
    color: #2e9b52;
    font-size: 12px;
    font-weight: 600;
}

QLabel#group_status_full {
    color: #c0392b;
    font-size: 12px;
    font-weight: 600;
}

QLabel#group_type_tag {
    background: #fff1cf;
    color: #8a5a00;
    border: 1px solid #f1d38a;
    border-radius: 8px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
}

QWidget#introPanel {
    background: #fffdf7;
    border: 1px solid #f1d38a;
    border-radius: 12px;
}

QLabel#intro_panel_title {
    font-size: 16px;
    font-weight: 700;
    color: #3b2f18;
}

QLabel#intro_group_title {
    font-size: 15px;
    font-weight: 700;
    color: #3b2f18;
    padding: 2px 0;
}


QLabel#intro_desc {
    font-size: 13px;
    color: #5b4518;
    line-height: 1.6;
}
"""



class ThemedMessageDialog(QDialog):
    def __init__(self, title, message, level="info", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(360)

        tone = {
            "success": {"accent": "#2e9b52", "bg": "#f0fff5", "border": "#b9e7c8"},
            "error": {"accent": "#c0392b", "bg": "#fff4f2", "border": "#f0c2bd"},
            "warning": {"accent": "#b7791f", "bg": "#fff8eb", "border": "#f1d38a"},
            "info": {"accent": "#5b4518", "bg": "#fff8eb", "border": "#f1d38a"},
        }.get(level, {"accent": "#5b4518", "bg": "#fff8eb", "border": "#f1d38a"})

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(10)

        title_label = QLabel(title)
        title_label.setObjectName("titleLabel")

        msg_label = QLabel(str(message))
        msg_label.setWordWrap(True)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        ok_btn = QPushButton("OK")

        ok_btn.clicked.connect(self.accept)
        btn_row.addWidget(ok_btn)

        root.addWidget(title_label)
        root.addWidget(msg_label)
        root.addLayout(btn_row)

        self.setStyleSheet(
            f"""
            QDialog {{
                background: #fff6ea;
                border: 1px solid {tone['border']};
                border-radius: 12px;
            }}
            QLabel {{
                color: #4a3b1f;
                font-size: 13px;
            }}
            QLabel#titleLabel {{
                color: {tone['accent']};
                font-size: 15px;
                font-weight: 700;
                background: {tone['bg']};
                border: 1px solid {tone['border']};
                border-radius: 8px;
                padding: 6px 10px;
            }}
            QPushButton {{
                min-width: 82px;
                border: 1px solid #f1d38a;
                border-radius: 8px;
                padding: 7px 12px;
                background: #ffe8a8;
                color: #5b4518;
            }}
            QPushButton:hover {{
                background: #ffe08e;
                border: 1px solid #dfb75b;
            }}
            """
        )


def show_themed_message(parent, title, message, level="info"):
    dlg = ThemedMessageDialog(title, message, level=level, parent=parent)
    dlg.exec()


class GroupMembersDialog(QDialog):

    def __init__(self, group_info, parent=None):
        super().__init__(parent)
        self.group_info = group_info

        loader = QUiLoader()
        ui_file = QFile(resource_path("ui/group_members_dialog.ui"))
        ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(ui_file)
        ui_file.close()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.ui)

        self.setWindowTitle("Group Members")
        self.resize(660, 500)

        group_name = group_info.get("group_name", "Unnamed Group")
        cur = group_info.get("current_members", 0)
        mx = group_info.get("max_members", 0)

        self.ui.pushButton.setText("Join Group")
        self.ui.pushButton_2.setText("Close")
        self.ui.pushButton_2.clicked.connect(self.reject)

        self.ui.label.setText(f"{group_name}")
        self.ui.label_2.setText(f"Members: {cur}/{mx}")
        self.ui.label_3.setText("Member List")

        self.ui.tableWidget.setColumnCount(3)
        self.ui.tableWidget.setHorizontalHeaderLabels(["Username", "Role", "Join Time"])

        self.ui.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.ui.tableWidget.verticalHeader().setVisible(False)
        self.ui.tableWidget.setAlternatingRowColors(True)

        self.ui.setStyleSheet(
            """
            QWidget { background: #fff6ea; color: #4a3b1f; }
            QLabel#label {
                font-size: 20px;
                font-weight: 700;
                color: #3b2f18;
                padding: 8px 12px;
                background: #fff3d4;
                border: 1px solid #ffe08e;
                border-radius: 10px;
            }
            QLabel#label_2 {
                font-size: 13px;
                font-weight: 600;
                color: #7a6640;
                padding: 12px 0 0 8px;
            }
            QLabel#label_3 {
                font-size: 13px;
                font-weight: 700;
                color: #5b4518;
                padding: 12px 0 0 8px;
            }
            QTableWidget {
                background: #fffdf7;
                alternate-background-color: #fff7e4;
                border: 1px solid #f1d38a;
                border-radius: 10px;
                gridline-color: #f3dfb2;
                color: #4a3b1f;
                font-size: 12px;
            }
            QHeaderView::section {
                background: #ffe8a8;
                color: #5b4518;
                border: none;
                border-bottom: 1px solid #dfb75b;
                padding: 8px;
                font-weight: 700;
            }
            QPushButton {
                border: 1px solid #f1d38a;
                border-radius: 8px;
                padding: 8px 12px;
                background: #ffe8a8;
                color: #5b4518;
            }
            QPushButton:hover {
                background: #ffe08e;
                border: 1px solid #dfb75b;
            }
            """
        )

        self.ui.pushButton.clicked.connect(self._join_group)
        self._load_members()


    def _load_members(self):
        data = get_group_members(self.group_info.get("group_id"))
        raw_members = data.get("members", []) if isinstance(data, dict) else []
        members = raw_members if isinstance(raw_members, list) else []

        self.ui.tableWidget.setRowCount(len(members))
        for i, m in enumerate(members):
            if not isinstance(m, dict):
                continue
            self.ui.tableWidget.setItem(i, 0, QTableWidgetItem(str(m.get("username", ""))))
            self.ui.tableWidget.setItem(i, 1, QTableWidgetItem(str(m.get("role", "member"))))
            self.ui.tableWidget.setItem(i, 2, QTableWidgetItem(str(m.get("join_time", ""))))

    def _join_group(self):
        group_id = self.group_info.get("group_id")
        user_id = None
        u = session.user
        if isinstance(u, dict):
            user_id = u.get("user_id") or u.get("id")
        elif hasattr(u, "user_id"):
            user_id = getattr(u, "user_id")
        elif hasattr(u, "id"):
            user_id = getattr(u, "id")

        if user_id is None:
            show_themed_message(self, "Action Failed", "Please log in before joining a group.", level="error")
            return


        password = self._ask_group_password_if_needed(self.group_info)
        if password is False:
            return

        result = join_group(group_id, password=password, user_id=user_id)
        if result.get("success"):
            show_themed_message(self, "Joined", "You have successfully joined this group.", level="success")
            self.accept()
            return



        message = str(result.get("message", "Failed to join group"))
        if (not password) and ("password" in message.lower()):

            retry_password = self._ask_group_password_force()
            if retry_password is False:
                return
            retry = join_group(group_id, password=retry_password, user_id=user_id)
            if retry.get("success"):
                show_themed_message(self, "Joined", "You have successfully joined this group.", level="success")
                self.accept()
                return

            message = retry.get("message", "Failed to join group")

        show_themed_message(self, "Join Failed", f"Failed to join group: {message}", level="error")



    def _ask_group_password_if_needed(self, group_info):
        need_password = bool(group_info.get("has_password"))
        if not need_password:
            need_password = bool(group_info.get("password") is False)
        if not need_password:
            return None
        return self._ask_group_password_force()


    def _ask_group_password_force(self):
        dlg = QInputDialog(self)
        dlg.setWindowTitle("Join Group")
        dlg.setLabelText("Password:")
        dlg.setTextEchoMode(QLineEdit.Password)
        dlg.setOkButtonText("Join")
        dlg.setCancelButtonText("Cancel")
        dlg.setStyleSheet(
            """
            QInputDialog { background: #fff6ea; color: #4a3b1f; }
            QLabel { color: #4a3b1f; font-size: 13px; }
            QLineEdit {
                background: #fffdf7;
                border: 1px solid #f1d38a;
                border-radius: 8px;
                padding: 6px 10px;
                color: #4a3b1f;
            }
            QPushButton {
                border: 1px solid #f1d38a;
                border-radius: 8px;
                padding: 6px 12px;
                background: #ffe8a8;
                color: #5b4518;
            }
            QPushButton:hover {
                background: #ffe08e;
                border: 1px solid #dfb75b;
            }
            """
        )
        if dlg.exec() != QDialog.Accepted:
            return False
        return dlg.textValue().strip()


class GroupPlazaPage(QWidget):



    def __init__(self, parent=None):
        super().__init__(parent)

        loader = QUiLoader()

        plaza_file = QFile(resource_path("ui/group_plaza_page.ui"))
        plaza_file.open(QFile.ReadOnly)
        self.ui = loader.load(plaza_file)
        plaza_file.close()

        create_file = QFile(resource_path("ui/create_group_page.ui"))
        create_file.open(QFile.ReadOnly)
        self.create_ui = loader.load(create_file)
        create_file.close()

        self.stack = QStackedWidget()
        self.stack.addWidget(self.ui)
        self.stack.addWidget(self.create_ui)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self.stack)

        self.setStyleSheet(GROUP_PLAZA_STYLE)
        self._selected_group_icon_path = None
        self._group_icon_cache = {}

        self._init_plaza_ui()
        self._init_intro_panel()

        self._init_create_ui()
        self.refresh_groups()


    def _init_plaza_ui(self):
        self.ui.pushButton.setText("Search")
        self.ui.pushButton_2.setText("Reset")
        self.ui.pushButton_3.setText("+ Create Group")
        self.ui.checkBox.setText("Only show available groups")
        self.ui.lineEdit.setPlaceholderText("Search groups by name...")
        self.ui.label.setText("Total 0 groups")
        self.ui.label.setStyleSheet("color: #7a6640; font-size: 12px; font-weight: 500; padding-left: 4px;")

        if self.ui.scrollAreaWidgetContents.layout() is None:

            self.ui.scrollAreaWidgetContents.setLayout(QVBoxLayout())
        self.ui.scrollAreaWidgetContents.layout().setContentsMargins(0, 0, 0, 0)
        self.ui.scrollAreaWidgetContents.layout().setSpacing(10)
        self.ui.leftBar.setMinimumWidth(0)
        self.ui.scrollAreaWidgetContents.setMinimumWidth(0)
        self.ui.scrollAreaWidgetContents.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.ui.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.ui.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.ui.horizontalLayout_2.setStretch(0, 1)
        self.ui.horizontalLayout_2.setStretch(1, 0)


        self.ui.pushButton.clicked.connect(self.refresh_groups)

        self.ui.pushButton_2.clicked.connect(self._reset_search)
        self.ui.pushButton_3.clicked.connect(self._show_create_page)

    def _init_intro_panel(self):
        self.ui.rightBar.setObjectName("introPanel")
        self.ui.rightBar.setMinimumWidth(0)
        self.ui.rightBar.setMaximumWidth(0)

        root = QVBoxLayout(self.ui.rightBar)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel("Group Introduction")
        title.setObjectName("intro_panel_title")
        close_btn = QPushButton("✕")
        close_btn.setFixedWidth(28)
        close_btn.clicked.connect(self._hide_intro_panel)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(close_btn)

        self._intro_title = QLabel("No Group Selected")
        self._intro_title.setObjectName("intro_group_title")
        self._intro_title.setWordWrap(True)

        self._intro_meta = QLabel("")
        self._intro_meta.setObjectName("group_meta")
        self._intro_meta.setWordWrap(True)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._intro_scroll = scroll


        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(10)

        images_wrap = QWidget()
        images_layout = QGridLayout(images_wrap)
        images_layout.setContentsMargins(0, 0, 0, 0)
        images_layout.setHorizontalSpacing(8)
        images_layout.setVerticalSpacing(8)
        self._intro_images_layout = images_layout

        self._intro_desc = QLabel("No introduction yet.")
        self._intro_desc.setObjectName("intro_desc")
        self._intro_desc.setWordWrap(True)
        self._intro_desc.setAlignment(Qt.AlignTop)

        content_layout.addWidget(images_wrap)
        content_layout.addWidget(self._intro_desc)
        content_layout.addStretch()

        scroll.setWidget(content)

        root.addLayout(header)
        root.addWidget(self._intro_title)
        root.addWidget(self._intro_meta)
        root.addWidget(scroll)

        self._intro_anim = QPropertyAnimation(self.ui.rightBar, b"maximumWidth", self)
        self._intro_anim.setDuration(220)
        self._intro_anim.setEasingCurve(QEasingCurve.OutCubic)

    def _toggle_intro_panel(self, show_panel):
        if show_panel:
            target = max(420, int(self.width() * 0.40))
            self.ui.horizontalLayout_2.setStretch(0, 3)
            self.ui.horizontalLayout_2.setStretch(1, 2)
            self.ui.rightBar.show()
            self.ui.rightBar.setMinimumWidth(target)
            self.ui.rightBar.setMaximumWidth(target)
            self.ui.scrollAreaWidgetContents.setMinimumWidth(0)

        else:
            self.ui.horizontalLayout_2.setStretch(0, 1)
            self.ui.horizontalLayout_2.setStretch(1, 0)
            self.ui.rightBar.setMinimumWidth(0)
            self.ui.rightBar.setMaximumWidth(0)
            self.ui.rightBar.hide()


    def _hide_intro_panel(self):
        self._toggle_intro_panel(False)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.ui.rightBar.isVisible() and self.ui.rightBar.maximumWidth() > 0:
            target = max(420, int(self.width() * 0.40))
            self.ui.rightBar.setMinimumWidth(target)
            self.ui.rightBar.setMaximumWidth(target)

    def _init_create_ui(self):

        self._create_step = 1
        self._selected_group_icon_path = None
        self._selected_intro_image_paths = []

        self.create_ui.setMinimumWidth(1020)
        self.create_ui.label.setStyleSheet("font-size: 22px; font-weight: 700; color: #3b2f18;")
        self.create_ui.label_3.setStyleSheet("font-size: 13px; font-weight: 600; color: #6f5930;")
        self.create_ui.label_5.setStyleSheet("font-size: 13px; font-weight: 600; color: #6f5930;")
        self.create_ui.label_6.setStyleSheet("font-size: 13px; font-weight: 600; color: #6f5930;")

        self.create_ui.lineEdit.setPlaceholderText("Enter group name")
        self.create_ui.lineEdit_3.setPlaceholderText("Enter password for private group")
        self.create_ui.lineEdit_4.setReadOnly(True)
        self.create_ui.lineEdit_4.setText(self._current_username())

        self.create_ui.pushButton.hide()
        self.create_ui.label_2.hide()

        icon_layout = self.create_ui.horizontalLayout_2
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setSpacing(8)
        icon_layout.setAlignment(Qt.AlignCenter)

        self._group_icon_button = QPushButton("+")
        self._group_icon_button.setObjectName("group_icon_button")
        self._group_icon_button.setFixedSize(92, 92)
        self._group_icon_button.setStyleSheet(
            """
            QPushButton#group_icon_button {
                border: 2px dashed #d5c28e;
                border-radius: 46px;
                background: #fffdf7;
                color: #9b834b;
                font-size: 30px;
                font-weight: 700;
            }
            QPushButton#group_icon_button:hover {
                border: 2px solid #dfb75b;
                background: #fff3d4;
            }
            """
        )
        icon_layout.insertWidget(0, self._group_icon_button, alignment=Qt.AlignCenter)

        grid = self.create_ui.gridLayout

        self._group_type_combo = QComboBox()
        self._group_type_combo.addItem("Study", "study")
        self._group_type_combo.addItem("Social", "social")

        self._study_types_edit = QLineEdit()
        self._study_types_edit.setPlaceholderText("e.g. IELTS, speaking, grammar")

        self._max_members_spin = QSpinBox()
        self._max_members_spin.setRange(2, 20)
        self._max_members_spin.setValue(8)

        self._public_radio = QRadioButton("Public")
        self._private_radio = QRadioButton("Private")
        self._public_radio.setChecked(True)
        self._privacy_group = QButtonGroup(self)
        self._privacy_group.addButton(self._public_radio)
        self._privacy_group.addButton(self._private_radio)

        privacy_wrap = QWidget()
        privacy_row = QHBoxLayout(privacy_wrap)
        privacy_row.setContentsMargins(0, 0, 0, 0)
        privacy_row.setSpacing(16)
        privacy_row.addWidget(self._public_radio)
        privacy_row.addWidget(self._private_radio)
        privacy_row.addStretch()

        label_group_type = QLabel("Group Type")
        label_group_type.setStyleSheet("font-size: 13px; font-weight: 600; color: #6f5930;")
        label_study_types = QLabel("Study Types")
        label_study_types.setStyleSheet("font-size: 13px; font-weight: 600; color: #6f5930;")
        label_max_members = QLabel("Max Members")
        label_max_members.setStyleSheet("font-size: 13px; font-weight: 600; color: #6f5930;")
        label_visibility = QLabel("Visibility")
        label_visibility.setStyleSheet("font-size: 13px; font-weight: 600; color: #6f5930;")

        grid.addWidget(label_group_type, 3, 0)
        grid.addWidget(self._group_type_combo, 3, 1)
        grid.addWidget(label_study_types, 4, 0)
        grid.addWidget(self._study_types_edit, 4, 1)
        grid.addWidget(label_max_members, 5, 0)
        grid.addWidget(self._max_members_spin, 5, 1)
        grid.addWidget(label_visibility, 6, 0)
        grid.addWidget(privacy_wrap, 6, 1)

        self._intro_page = QWidget()
        self._intro_page.setMinimumWidth(900)
        intro_root = QVBoxLayout(self._intro_page)
        intro_root.setContentsMargins(8, 8, 8, 8)
        intro_root.setSpacing(10)

        self._intro_title_edit = QLineEdit()
        self._intro_title_edit.setPlaceholderText("Write a title...")
        self._intro_title_edit.setMinimumHeight(48)
        self._intro_title_edit.setStyleSheet(
            """
            QLineEdit {
                font-size: 28px;
                font-weight: 700;
                color: #3b2f18;
                border: none;
                border-bottom: 2px solid #e2c06f;
                border-radius: 0;
                padding: 6px 4px;
                background: #fffdf7;
            }
            QLineEdit:focus {
                border-bottom: 2px solid #c9952f;
            }
            """
        )

        image_toolbar = QHBoxLayout()
        image_toolbar.setSpacing(8)
        self._intro_picture_button = QPushButton("+ Add Pictures")
        self._intro_picture_button.setMinimumHeight(36)
        self._clear_intro_images_btn = QPushButton("Clear")
        self._clear_intro_images_btn.setMinimumHeight(36)
        self._intro_images_count = QLabel("0 images")
        self._intro_images_count.setObjectName("group_meta")
        image_toolbar.addWidget(self._intro_picture_button)
        image_toolbar.addWidget(self._clear_intro_images_btn)
        image_toolbar.addStretch()
        image_toolbar.addWidget(self._intro_images_count)

        self._intro_images_wrap = QWidget()
        self._intro_images_grid = QGridLayout(self._intro_images_wrap)
        self._intro_images_grid.setContentsMargins(0, 0, 0, 0)
        self._intro_images_grid.setHorizontalSpacing(8)
        self._intro_images_grid.setVerticalSpacing(8)

        self._intro_desc_edit = QTextEdit()
        self._intro_desc_edit.setPlaceholderText("Write your group introduction...")
        self._intro_desc_edit.setMinimumHeight(300)
        self._intro_desc_edit.setStyleSheet(
            """
            QTextEdit {
                background: #fffdf7;
                border: 1px solid #f1d38a;
                border-radius: 12px;
                padding: 12px;
                color: #4a3b1f;
                font-size: 15px;
                line-height: 1.7;
            }
            """
        )

        intro_root.addWidget(self._intro_title_edit)
        intro_root.addLayout(image_toolbar)
        intro_root.addWidget(self._intro_images_wrap)
        intro_root.addWidget(self._intro_desc_edit)

        self.create_ui.verticalLayout.insertWidget(3, self._intro_page)

        self.create_ui.pushButton_3.clicked.connect(self._handle_create_back)
        self.create_ui.pushButton_2.clicked.connect(self._handle_create_next_or_submit)
        self._group_icon_button.clicked.connect(self._pick_group_icon)
        self._intro_picture_button.clicked.connect(self._pick_intro_images)
        self._clear_intro_images_btn.clicked.connect(self._clear_intro_images)
        self._public_radio.toggled.connect(self._on_privacy_changed)
        self._private_radio.toggled.connect(self._on_privacy_changed)

        self._set_create_image_button_preview(self._group_icon_button, None, "+")
        self._refresh_intro_images_preview()
        self._switch_create_step(1)



    def _clear_group_list(self):

        layout = self.ui.scrollAreaWidgetContents.layout()
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def refresh_groups(self):
        search = self.ui.lineEdit.text().strip()
        data = get_groups(search=search if search else None, page=1, page_size=50)
        raw_groups = data.get("groups", []) if isinstance(data, dict) else []
        groups = raw_groups if isinstance(raw_groups, list) else []
        groups = [g for g in groups if isinstance(g, dict)]

        if self.ui.checkBox.isChecked():
            groups = [
                g for g in groups
                if int(g.get("current_members", 0)) < int(g.get("max_members", 0))
            ]

        self._clear_group_list()
        layout = self.ui.scrollAreaWidgetContents.layout()

        for g in groups:
            layout.addWidget(self._build_group_card(g))

        layout.addStretch()
        self.ui.label.setText(f"Total {len(groups)} groups")



    def _build_group_card(self, group_info):
        frame = QFrame()
        frame.setObjectName("group_card")
        frame.setMinimumHeight(96)

        row = QHBoxLayout(frame)
        row.setContentsMargins(12, 10, 12, 10)
        row.setSpacing(10)

        icon = QLabel()
        icon.setFixedSize(44, 44)
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("border-radius: 22px; background: #f0f0f0; color: #888;")

        icon_pixmap = self._load_group_icon_pixmap(group_info.get("group_icon"))
        if icon_pixmap is not None:
            icon.setPixmap(icon_pixmap.scaled(44, 44, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
            icon.setText("")
        else:
            icon.setText("👥")

        text_col = QVBoxLayout()
        text_col.setSpacing(4)

        name_row = QHBoxLayout()
        name_row.setSpacing(8)

        name = QLabel(str(group_info.get("group_name", "Unnamed Group")))
        name.setObjectName("group_name")

        type_tag = QLabel(self._format_group_type_tag(group_info))
        type_tag.setObjectName("group_type_tag")

        name_row.addWidget(name)
        name_row.addWidget(type_tag)
        name_row.addStretch()

        cur = int(group_info.get("current_members", 0))
        mx = int(group_info.get("max_members", 0))
        meta = QLabel(f"Members: {cur}/{mx}   ·   ID: {group_info.get('group_id', '-')}")
        meta.setObjectName("group_meta")

        full = cur >= mx
        status = QLabel("Full" if full else "Available")
        status.setObjectName("group_status_full" if full else "group_status_ok")

        text_col.addLayout(name_row)
        text_col.addWidget(meta)
        text_col.addWidget(status)

        btn_view = QPushButton("Member")
        btn_intro = QPushButton("Intro")
        btn_join = QPushButton("Join")

        for btn, w in ((btn_view, 70), (btn_intro, 62), (btn_join, 56)):
            btn.setMinimumWidth(w)
            btn.setMaximumWidth(w)
            btn.setStyleSheet("padding: 4px 6px; font-size: 11px;")


        if full:
            btn_join.setEnabled(False)

        btn_view.clicked.connect(lambda: self._open_members_dialog(group_info))
        btn_intro.clicked.connect(lambda: self._open_group_intro(group_info))
        btn_join.clicked.connect(lambda: self._join_direct(group_info))

        row.addWidget(icon)
        row.addLayout(text_col, 1)
        row.addWidget(btn_view)
        row.addWidget(btn_intro)
        row.addWidget(btn_join)


        return frame

    def _format_group_type_tag(self, group_info):
        group_type = str(group_info.get("group_type") or "study").strip().lower()
        study_types = str(group_info.get("study_types") or "").strip()

        if group_type == "social":
            return "Social"

        if study_types:
            labels = [x.strip().capitalize() for x in study_types.split(",") if x.strip()]
            if labels:
                return "Study · " + "/".join(labels[:2])

        return "Study"

    def _parse_intro_images(self, group_info):
        images = []

        for key in ("images", "group_images", "image_urls"):
            raw = group_info.get(key)
            if isinstance(raw, list):
                images.extend([str(x).strip() for x in raw if str(x).strip()])

        cover = str(group_info.get("cover_image") or "").strip()
        if cover:
            if "," in cover:
                images.extend([x.strip() for x in cover.split(",") if x.strip()])
            else:
                images.append(cover)

        dedup = []
        seen = set()
        for item in images:
            if item and item not in seen:
                seen.add(item)
                dedup.append(item)

        return dedup[:6]

    def _open_group_intro(self, group_info):
        title = str(group_info.get("title") or group_info.get("group_name") or "Group Introduction")
        desc = str(group_info.get("description") or "This group has not added an introduction yet.")
        type_text = self._format_group_type_tag(group_info)

        self._intro_title.setText(title)
        self._intro_meta.setText(f"{type_text}   ·   Group ID: {group_info.get('group_id', '-')}")
        self._intro_desc.setText(desc)

        images = self._parse_intro_images(group_info)
        self._fill_intro_images(images)
        self._toggle_intro_panel(True)

    def _fill_intro_images(self, image_urls):
        layout = self._intro_images_layout
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if not image_urls:
            placeholder = QLabel("No images")
            placeholder.setObjectName("group_meta")
            layout.addWidget(placeholder, 0, 0)
            return

        sizes = [(260, 200), (126, 96), (126, 96), (126, 96), (126, 96), (126, 96)]
        positions = [(0, 0, 2, 2), (0, 2, 1, 1), (1, 2, 1, 1), (2, 0, 1, 1), (2, 1, 1, 1), (2, 2, 1, 1)]

        for idx, img in enumerate(image_urls[:6]):
            label = QLabel()
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("border-radius: 8px; background: #f3f3f3; color: #999;")

            pix = self._load_group_icon_pixmap(img)
            w, h = sizes[min(idx, len(sizes) - 1)]
            if pix is not None and not pix.isNull():
                label.setPixmap(pix.scaled(w, h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
                label.setFixedSize(w, h)
            else:
                label.setText("Image")
                label.setFixedSize(w, h)

            r, c, rs, cs = positions[min(idx, len(positions) - 1)]
            layout.addWidget(label, r, c, rs, cs)

    def _load_group_icon_pixmap(self, icon_url):

        if not icon_url:
            return None

        key = str(icon_url).strip()
        if not key:
            return None

        if key in self._group_icon_cache:
            return self._group_icon_cache[key]

        pixmap = QPixmap()
        try:
            normalized = key.strip("\"'")
            base = BASE_URL.rstrip("/")
            candidates = []

            if normalized.startswith("http://") or normalized.startswith("https://"):
                candidates.append(normalized)
            else:
                clean = normalized.lstrip("/")
                candidates.append(f"{base}/{clean}")

                if clean.startswith("head/"):
                    tail = clean[len("head/"):]
                    candidates.extend([
                        f"{base}/static/head/{tail}",
                        f"{base}/uploads/head/{tail}",
                        f"{base}/media/head/{tail}",
                        f"{base}/files/head/{tail}",
                    ])

            seen = set()
            for fetch_url in candidates:
                if fetch_url in seen:
                    continue
                seen.add(fetch_url)

                try:
                    res = requests.get(fetch_url, timeout=5)
                    if res.ok and res.content:
                        pixmap.loadFromData(res.content)
                        if not pixmap.isNull():
                            break
                except Exception:
                    continue

            if pixmap.isNull() and normalized and not normalized.startswith("http"):
                local_pix = QPixmap(normalized)
                if not local_pix.isNull():
                    pixmap = local_pix
        except Exception:
            pixmap = QPixmap()

        if pixmap.isNull():
            self._group_icon_cache[key] = None
            return None

        self._group_icon_cache[key] = pixmap
        return pixmap



    def _open_members_dialog(self, group_info):

        dlg = GroupMembersDialog(group_info, self)
        ok = dlg.exec()
        if ok:
            self.refresh_groups()

    def _join_direct(self, group_info):
        group_id = group_info.get("group_id")
        if group_id is None:
            show_themed_message(self, "Action Failed", "Invalid group ID.", level="error")
            return

        user_id = self._current_user_id()
        if user_id is None:
            show_themed_message(self, "Action Failed", "Please log in before joining a group.", level="error")
            return


        password = self._ask_group_password_if_needed(group_info)
        if password is False:
            return

        result = join_group(group_id, password=password, user_id=user_id)
        if result.get("success"):
            show_themed_message(self, "Joined", "You have successfully joined this group.", level="success")
            self.refresh_groups()
            return


        message = str(result.get("message", "Failed to join group"))
        if (not password) and ("password" in message.lower()):

            retry_password = self._ask_group_password_force()
            if retry_password is False:
                return
            retry = join_group(group_id, password=retry_password, user_id=user_id)
            if retry.get("success"):
                show_themed_message(self, "Joined", "You have successfully joined this group.", level="success")
                self.refresh_groups()
                return

            message = retry.get("message", "Failed to join group")

        show_themed_message(self, "Join Failed", f"Failed to join group: {message}", level="error")



    def _ask_group_password_if_needed(self, group_info):
        need_password = bool(group_info.get("has_password"))
        if not need_password:
            need_password = bool(group_info.get("password") is False)
        if not need_password:
            return None
        return self._ask_group_password_force()


    def _ask_group_password_force(self):
        dlg = QInputDialog(self)
        dlg.setWindowTitle("Join Group")
        dlg.setLabelText("Password:")
        dlg.setTextEchoMode(QLineEdit.Password)
        dlg.setOkButtonText("Join")
        dlg.setCancelButtonText("Cancel")
        dlg.setStyleSheet(
            """
            QInputDialog { background: #fff6ea; color: #4a3b1f; }
            QLabel { color: #4a3b1f; font-size: 13px; }
            QLineEdit {
                background: #fffdf7;
                border: 1px solid #f1d38a;
                border-radius: 8px;
                padding: 6px 10px;
                color: #4a3b1f;
            }
            QPushButton {
                border: 1px solid #f1d38a;
                border-radius: 8px;
                padding: 6px 12px;
                background: #ffe8a8;
                color: #5b4518;
            }
            QPushButton:hover {
                background: #ffe08e;
                border: 1px solid #dfb75b;
            }
            """
        )
        if dlg.exec() != QDialog.Accepted:
            return False
        return dlg.textValue().strip()

    def _reset_search(self):



        self.ui.lineEdit.clear()
        self.ui.checkBox.setChecked(False)
        self.refresh_groups()

    def _show_create_page(self):
        self._reset_create_form()
        self.create_ui.lineEdit_4.setText(self._current_username())
        self.stack.setCurrentWidget(self.create_ui)

    def _back_to_plaza(self):
        self.stack.setCurrentWidget(self.ui)

    def _handle_create_back(self):
        if self._create_step == 2:
            self._switch_create_step(1)
            return
        self._back_to_plaza()

    def _handle_create_next_or_submit(self):
        if self._create_step == 1:
            group_name = self.create_ui.lineEdit.text().strip()
            if not group_name:
                show_themed_message(self, "Missing Information", "Please enter a group name.", level="warning")
                return

            if self._private_radio.isChecked() and not self.create_ui.lineEdit_3.text().strip():
                show_themed_message(self, "Missing Information", "Private group needs a password.", level="warning")
                return

            self._switch_create_step(2)
            return

        self._submit_create_group()

    def _switch_create_step(self, step):
        self._create_step = step
        is_page_one = step == 1

        self.create_ui.widget_3.setVisible(is_page_one)
        self.create_ui.widget_2.setVisible(is_page_one)
        self._intro_page.setVisible(not is_page_one)

        if is_page_one:
            self.create_ui.label.setText("Create A New Group · Basic Info")
            self.create_ui.pushButton_3.setText("Back")
            self.create_ui.pushButton_2.setText("Next")
        else:
            self.create_ui.label.setText("Create A New Group · Introduction")
            self.create_ui.pushButton_3.setText("Previous")
            self.create_ui.pushButton_2.setText("Create")

        self._on_privacy_changed()

    def _on_privacy_changed(self):
        private_mode = self._private_radio.isChecked()
        self.create_ui.label_5.setVisible(private_mode)
        self.create_ui.lineEdit_3.setVisible(private_mode)
        if not private_mode:
            self.create_ui.lineEdit_3.clear()

    def _pick_group_icon(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Group Icon",
            "",
            "Images (*.png *.jpg *.jpeg *.webp *.gif)"
        )
        if file_path:
            self._selected_group_icon_path = file_path
            self._set_create_image_button_preview(self._group_icon_button, file_path, "+")

    def _pick_intro_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Introduction Pictures",
            "",
            "Images (*.png *.jpg *.jpeg *.webp *.gif)"
        )
        if not files:
            return

        for path in files:
            if path and path not in self._selected_intro_image_paths:
                self._selected_intro_image_paths.append(path)

        self._refresh_intro_images_preview()

    def _clear_intro_images(self):
        self._selected_intro_image_paths = []
        self._refresh_intro_images_preview()

    def _refresh_intro_images_preview(self):
        while self._intro_images_grid.count():
            item = self._intro_images_grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if not self._selected_intro_image_paths:
            placeholder = QLabel("No images selected")
            placeholder.setObjectName("group_meta")
            self._intro_images_grid.addWidget(placeholder, 0, 0)
            self._intro_images_count.setText("0 images")
            return

        for idx, path in enumerate(self._selected_intro_image_paths[:9]):
            pix = QPixmap(path)
            preview = QLabel()
            preview.setFixedSize(140, 92)
            preview.setAlignment(Qt.AlignCenter)
            preview.setStyleSheet("border: 1px solid #f1d38a; border-radius: 8px; background: #fff9f0;")
            if not pix.isNull():
                preview.setPixmap(pix.scaled(140, 92, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
            else:
                preview.setText("Invalid")
            self._intro_images_grid.addWidget(preview, idx // 3, idx % 3)

        extra_count = max(0, len(self._selected_intro_image_paths) - 9)
        if extra_count:
            more = QLabel(f"+{extra_count} more")
            more.setObjectName("group_meta")
            self._intro_images_grid.addWidget(more, 3, 2)

        self._intro_images_count.setText(f"{len(self._selected_intro_image_paths)} images")

    def _set_create_image_button_preview(self, button, file_path, placeholder_text):
        if not file_path:
            button.setIcon(QIcon())
            button.setText(placeholder_text)
            return

        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            show_themed_message(self, "Invalid Image", "Please choose a valid image file.", level="warning")
            button.setIcon(QIcon())
            button.setText(placeholder_text)
            return

        scaled = pixmap.scaled(84, 84, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        button.setIcon(QIcon(scaled))
        button.setIconSize(QSize(84, 84))
        button.setText("")


    def _submit_create_group(self):
        group_name = self.create_ui.lineEdit.text().strip()
        if not group_name:
            show_themed_message(self, "Missing Information", "Please enter a group name.", level="warning")
            return

        intro_title = self._intro_title_edit.text().strip()
        intro_desc = self._intro_desc_edit.toPlainText().strip()
        if not intro_title or not intro_desc:
            show_themed_message(self, "Missing Information", "Please fill introduction title and text.", level="warning")
            return

        group_type = self._group_type_combo.currentData()
        study_types = self._study_types_edit.text().strip() or None
        if group_type == "study" and not study_types:
            show_themed_message(self, "Missing Information", "Study group needs Study Types.", level="warning")
            return

        private_mode = self._private_radio.isChecked()
        password = self.create_ui.lineEdit_3.text().strip() if private_mode else None
        if private_mode and not password:
            show_themed_message(self, "Missing Information", "Private group needs a password.", level="warning")
            return

        uploaded_image_urls = []
        if self._selected_intro_image_paths:
            image_base64_list = []
            for path in self._selected_intro_image_paths:
                encoded = self._encode_image_to_data_url(path)
                if not encoded:
                    show_themed_message(self, "Image Error", f"Failed to read image: {path}", level="error")
                    return
                image_base64_list.append(encoded)

            upload_result = upload_group_images(image_base64_list)
            if not upload_result.get("success"):
                show_themed_message(self, "Upload Failed", f"Failed to upload images: {upload_result.get('message', 'Please try again later.')}", level="error")
                return

            raw_urls = upload_result.get("images", [])
            if not isinstance(raw_urls, list):
                show_themed_message(self, "Upload Failed", "Image upload response is invalid.", level="error")
                return

            uploaded_image_urls = [str(x).strip() for x in raw_urls if str(x).strip()]
            if not uploaded_image_urls:
                show_themed_message(self, "Upload Failed", "Image upload returned empty URLs.", level="error")
                return


        user_id = self._current_user_id()
        create_payload = {
            "group_name": group_name,
            "max_members": int(self._max_members_spin.value()),
            "group_type": group_type,
            "study_types": study_types,
            "password": password,
            "user_id": user_id,
            "title": intro_title,
            "description": intro_desc,
            "cover_image": uploaded_image_urls[0] if uploaded_image_urls else None,
            "images": uploaded_image_urls,
            "is_private": private_mode,
            "visibility": ("private" if private_mode else "public"),
        }
        result = create_group(**create_payload)

        if not result.get("success"):
            show_themed_message(self, "Create Failed", f"Failed to create group: {result.get('message', 'Please try again later.')}", level="error")
            return

        group_id = result.get("group_id")
        if self._selected_group_icon_path and group_id is not None:
            upload_res = upload_group_icon(group_id=group_id, image_path=self._selected_group_icon_path)
            if not upload_res.get("success"):
                show_themed_message(self, "Upload Notice", f"Group created, but icon upload failed: {upload_res.get('message', 'Please try again later.')}", level="warning")

        show_themed_message(self, "Created", "Group created successfully.", level="success")

        self._reset_create_form()
        self.stack.setCurrentWidget(self.ui)
        self.refresh_groups()

    def _encode_image_to_data_url(self, file_path):
        try:
            with open(file_path, "rb") as f:
                raw = f.read()
            encoded = base64.b64encode(raw).decode("utf-8")
            mime, _ = mimetypes.guess_type(file_path)
            mime = mime or "image/png"
            return f"data:{mime};base64,{encoded}"
        except Exception:
            return None

    def _reset_create_form(self):
        self.create_ui.lineEdit.clear()
        self.create_ui.lineEdit_3.clear()
        self.create_ui.lineEdit_4.setText(self._current_username())
        self._group_type_combo.setCurrentIndex(0)
        self._study_types_edit.clear()
        self._max_members_spin.setValue(8)
        self._public_radio.setChecked(True)
        self._intro_title_edit.clear()
        self._intro_desc_edit.clear()

        self._selected_group_icon_path = None
        self._selected_intro_image_paths = []
        self._set_create_image_button_preview(self._group_icon_button, None, "+")
        self._refresh_intro_images_preview()
        self._switch_create_step(1)




    def _current_username(self):
        u = session.user
        if isinstance(u, dict):
            return str(u.get("username") or u.get("name") or "Current User")
        if hasattr(u, "username") and getattr(u, "username"):
            return str(getattr(u, "username"))
        if hasattr(u, "name") and getattr(u, "name"):
            return str(getattr(u, "name"))
        return "Current User"

    def _current_user_id(self):
        u = session.user
        if isinstance(u, dict):
            return u.get("user_id") or u.get("id")
        if hasattr(u, "user_id"):
            return getattr(u, "user_id")
        if hasattr(u, "id"):
            return getattr(u, "id")
        return None
