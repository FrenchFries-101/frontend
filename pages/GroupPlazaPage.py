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
)

from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Qt
from PySide6.QtGui import QPixmap
import requests

import session

from service.api import BASE_URL, get_groups, create_group, join_group, get_group_members, upload_group_icon

from utils.path_utils import resource_path



GROUP_PLAZA_STYLE = """
QWidget {
    background: #fff6ea;
    color: #4a3b1f;
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
        self.ui.rightBar.hide()



        if self.ui.scrollAreaWidgetContents.layout() is None:
            self.ui.scrollAreaWidgetContents.setLayout(QVBoxLayout())
        self.ui.scrollAreaWidgetContents.layout().setContentsMargins(0, 0, 0, 0)
        self.ui.scrollAreaWidgetContents.layout().setSpacing(10)

        self.ui.pushButton.clicked.connect(self.refresh_groups)
        self.ui.pushButton_2.clicked.connect(self._reset_search)
        self.ui.pushButton_3.clicked.connect(self._show_create_page)

    def _init_create_ui(self):
        self.create_ui.pushButton.setText("+")
        self.create_ui.pushButton_3.setText("Back")
        self.create_ui.pushButton_2.setText("Create")

        self.create_ui.lineEdit.setPlaceholderText("Enter group name")
        self.create_ui.lineEdit_3.setPlaceholderText("Optional")
        self.create_ui.lineEdit_4.setReadOnly(True)
        self.create_ui.lineEdit_4.setText(self._current_username())


        self.create_ui.label.setStyleSheet("font-size: 22px; font-weight: 700; color: #3b2f18;")
        self.create_ui.label_3.setStyleSheet("font-size: 13px; font-weight: 600; color: #6f5930;")
        self.create_ui.label_5.setStyleSheet("font-size: 13px; font-weight: 600; color: #6f5930;")
        self.create_ui.label_6.setStyleSheet("font-size: 13px; font-weight: 600; color: #6f5930;")

        icon_layout = self.create_ui.horizontalLayout_2

        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setSpacing(8)
        icon_layout.setAlignment(Qt.AlignCenter)

        self.create_ui.label_2.setAlignment(Qt.AlignCenter)
        self.create_ui.label_2.setFixedSize(86, 86)
        self.create_ui.label_2.setStyleSheet(
            "border: 2px solid #cfcfcf; border-radius: 43px; background: #ececec; color: #8c8c8c;"
        )

        self.create_ui.pushButton.setObjectName("btn_add_icon")
        self.create_ui.pushButton.setFixedSize(30, 30)
        self.create_ui.pushButton.setStyleSheet(
            """
            QPushButton#btn_add_icon {
                border: 1px solid #f1d38a;
                border-radius: 15px;
                background: #ffe8a8;
                color: #5b4518;
                font-size: 18px;
                font-weight: 700;
                padding: 0;
            }
            QPushButton#btn_add_icon:hover {
                background: #ffe08e;
                border: 1px solid #dfb75b;
            }
            QPushButton#btn_add_icon:pressed {
                background: #f8d36e;
            }
            """
        )


        self._set_create_icon_preview(None)

        self.create_ui.pushButton.clicked.connect(self._pick_group_icon)
        self.create_ui.pushButton_3.clicked.connect(self._back_to_plaza)
        self.create_ui.pushButton_2.clicked.connect(self._submit_create_group)

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
        frame.setMinimumHeight(90)

        row = QHBoxLayout(frame)
        row.setContentsMargins(12, 10, 12, 10)

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
        name = QLabel(str(group_info.get("group_name", "Unnamed Group")))
        name.setObjectName("group_name")

        cur = int(group_info.get("current_members", 0))
        mx = int(group_info.get("max_members", 0))
        meta = QLabel(f"Members: {cur}/{mx}   ·   ID: {group_info.get('group_id', '-')}")
        meta.setObjectName("group_meta")

        full = cur >= mx
        status = QLabel("Full" if full else "Available")
        status.setObjectName("group_status_full" if full else "group_status_ok")

        text_col.addWidget(name)
        text_col.addWidget(meta)
        text_col.addWidget(status)

        btn_view = QPushButton("View Members")
        btn_join = QPushButton("Join")
        if full:
            btn_join.setEnabled(False)

        btn_view.clicked.connect(lambda: self._open_members_dialog(group_info))
        btn_join.clicked.connect(lambda: self._join_direct(group_info))

        row.addWidget(icon)
        row.addLayout(text_col)
        row.addStretch()
        row.addWidget(btn_view)
        row.addWidget(btn_join)

        return frame

    def _load_group_icon_pixmap(self, icon_url):

        if not icon_url:
            return None

        key = str(icon_url)
        cached = self._group_icon_cache.get(key)
        if cached is not None:
            return cached

        pixmap = QPixmap()
        try:
            url = key
            if key.startswith("/"):
                url = f"{BASE_URL}{key}"

            if url.startswith("http://") or url.startswith("https://"):
                res = requests.get(url, timeout=5)
                if res.ok and res.content:
                    pixmap.loadFromData(res.content)
            else:
                pixmap = QPixmap(url)
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
        self.create_ui.lineEdit_4.setText(self._current_username())
        self._set_create_icon_preview(None)
        self.stack.setCurrentWidget(self.create_ui)

    def _back_to_plaza(self):
        self.stack.setCurrentWidget(self.ui)

    def _pick_group_icon(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Group Icon",
            "",
            "Images (*.png *.jpg *.jpeg *.webp *.gif)"
        )
        if file_path:
            self._set_create_icon_preview(file_path)

    def _set_create_icon_preview(self, file_path):
        self._selected_group_icon_path = file_path
        label = self.create_ui.label_2

        if not file_path:
            label.setPixmap(QPixmap())
            label.setText("+")
            label.setStyleSheet(
                "border: 2px solid #cfcfcf; border-radius: 43px; background: #ececec; color: #8c8c8c; font-size: 24px; font-weight: 700;"
            )
            return

        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            show_themed_message(self, "Invalid Image", "Please choose a valid image file.", level="warning")
            self._set_create_icon_preview(None)
            return


        scaled = pixmap.scaled(82, 82, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        label.setText("")
        label.setPixmap(scaled)
        label.setStyleSheet(
            "border: 2px solid #f1d38a; border-radius: 43px; background: #fffdf7;"
        )


    def _submit_create_group(self):
        group_name = self.create_ui.lineEdit.text().strip()
        password = self.create_ui.lineEdit_3.text().strip() or None

        if not group_name:
            show_themed_message(self, "Missing Information", "Please enter a group name.", level="warning")
            return



        user_id = self._current_user_id()
        result = create_group(
            group_name=group_name,
            max_members=4,
            password=password,
            user_id=user_id,
        )

        if not result.get("success"):
            show_themed_message(self, "Create Failed", f"Failed to create group: {result.get('message', 'Please try again later.')}", level="error")
            return



        group_id = result.get("group_id")
        if self._selected_group_icon_path and group_id is not None:
            upload_res = upload_group_icon(group_id=group_id, image_path=self._selected_group_icon_path)
            if not upload_res.get("success"):
                show_themed_message(self, "Upload Notice", f"Group created, but icon upload failed: {upload_res.get('message', 'Please try again later.')}", level="warning")

        show_themed_message(self, "Created", "Group created successfully.", level="success")


        self.create_ui.lineEdit.clear()
        self.create_ui.lineEdit_3.clear()
        self._set_create_icon_preview(None)
        self.stack.setCurrentWidget(self.ui)
        self.refresh_groups()


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
