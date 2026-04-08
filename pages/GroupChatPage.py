import base64
import os

import requests
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidgetItem,
    QFrame,
    QFileDialog,
    QMessageBox,
)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Qt, QSize
from PySide6.QtGui import QPixmap, QIcon

import session
from service.api import BASE_URL, get_user_groups, get_group_messages, send_group_message

from utils.path_utils import resource_path


class GroupChatPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        loader = QUiLoader()
        ui_file = QFile(resource_path("ui/group_chat_page.ui"))
        ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(ui_file)
        ui_file.close()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self.ui)

        self._all_groups = []
        self._messages = []
        self._current_group = None
        self._oldest_timestamp = None
        self._selected_image_path = None
        self._last_user_id = None

        self._apply_style()
        self._init_texts()
        self._bind_events()
        self._clear_image_preview()
        self._sync_user_context(force_refresh=True)


    def _apply_style(self):
        self.ui.setStyleSheet(
            """
            QWidget#Form { background: #fff7ef; color: #202020; }
            QFrame { border: none; border-radius: 0px; }
            QFrame#frame { background: #fff7ef; }
            QFrame#frame_2, QFrame#frame_4, QFrame#frame_6 { background: #ffffff; }
            QFrame#frame_3 { background: #ffffff; border: 1px solid #e8d8b4; }


            QLabel#label { font-size: 15px; font-weight: 600; color: #2a2a2a; }
            QLabel#label_2 { font-size: 16px; font-weight: 700; color: #1f1f1f; }
            QLabel#label_3 { font-size: 12px; color: #8c8c8c; }

            QLineEdit#lineEdit {
                background: #ffffff;
                border: none;
                border-radius: 14px;
                padding: 7px 12px;
                color: #333333;
            }
            QLineEdit#lineEdit_2 {
                background: #ffffff;
                border: 1px solid #e8d8b4;
                border-radius: 8px;
                padding: 6px 10px;
                color: #202020;
            }

            QListWidget#listWidget {
                background: #fff7ef;
                border: none;
                border-radius: 0px;
                padding: 0px;
                outline: none;
            }
            QListWidget#listWidget::item {
                border: none;
                border-radius: 0px;
                padding: 10px 8px;
            }
            QListWidget#listWidget::item:hover { background: #f3eadf; }
            QListWidget#listWidget::item:selected { background: #eadfce; color: #1f1f1f; }

            QPushButton#pushButton, QPushButton#pushButton_2, QPushButton#pushButton_4, QPushButton#pushButton_5, QPushButton#pushButton_3 {
                border: none;
                border-radius: 0px;
                background: transparent;
                color: #5a5a5a;
                padding: 6px 8px;
                font-weight: 500;
            }
            QPushButton#pushButton_5 {
                background: #f28d40;
                color: #ffffff;
                font-weight: 700;
            }
            QPushButton#pushButton_5:hover { background: #e37f32; }

            QPushButton:hover { background: #f2f2f2; }

            QScrollArea#scrollArea {
                border: none;
                border-radius: 0px;
                background: #ffffff;
            }
            QWidget#scrollAreaWidgetContents { background: #ffffff; }

            """
        )



    def _init_texts(self):
        self.ui.label.setText("My Groups")
        self.ui.lineEdit.setPlaceholderText("Search groups...")
        self.ui.pushButton.setText("Refresh")
        self.ui.listWidget.setIconSize(QSize(28, 28))
        self.ui.label_2.setText("Select a group")

        self.ui.label_3.setText("No group selected")
        self.ui.pushButton_2.setText("Load Earlier")
        self.ui.pushButton_3.setText("Remove")
        self.ui.pushButton_4.setText("Image")
        self.ui.pushButton_5.setText("Send")
        self.ui.lineEdit_2.setPlaceholderText("Type a message...")

    def _bind_events(self):
        self.ui.pushButton.clicked.connect(self.refresh_groups)
        self.ui.lineEdit.textChanged.connect(self._filter_groups)
        self.ui.listWidget.currentItemChanged.connect(self._on_group_changed)
        self.ui.pushButton_2.clicked.connect(self.load_more_messages)
        self.ui.pushButton_4.clicked.connect(self._pick_image)
        self.ui.pushButton_3.clicked.connect(self._clear_image_preview)
        self.ui.pushButton_5.clicked.connect(self.send_current_message)
        self.ui.lineEdit_2.returnPressed.connect(self.send_current_message)

    def _current_user_id(self):
        u = session.user
        if isinstance(u, dict):
            return u.get("user_id") or u.get("id")
        if hasattr(u, "user_id"):
            return getattr(u, "user_id")
        if hasattr(u, "id"):
            return getattr(u, "id")
        return None

    def showEvent(self, event):
        super().showEvent(event)
        self._sync_user_context(force_refresh=True)

    def _clear_chat_state(self, login_hint=False):
        self._all_groups = []
        self._messages = []
        self._current_group = None
        session.current_group_id = None
        self._oldest_timestamp = None
        self.ui.listWidget.clear()
        self.ui.label_2.setText("Select a group")
        self.ui.label_3.setText("Please log in first" if login_hint else "No group selected")
        self._render_messages()

    def _sync_user_context(self, force_refresh=False):
        user_id = self._current_user_id()
        user_changed = user_id != self._last_user_id

        if user_changed:
            self._clear_chat_state(login_hint=(user_id is None))
            self._clear_image_preview()
            self._last_user_id = user_id

        if user_id is None:
            return

        if force_refresh or user_changed or not self._all_groups:
            self.refresh_groups()

    def refresh_groups(self):
        user_id = self._current_user_id()
        if user_id is None:
            self._clear_chat_state(login_hint=True)
            return


        data = get_user_groups(user_id)
        if not isinstance(data, dict):
            data = {"groups": []}

        groups = data.get("groups", [])
        if not isinstance(groups, list):
            groups = []
        self._all_groups = [g for g in groups if isinstance(g, dict)]

        self._populate_group_list(self._all_groups)

        if not self._all_groups and data.get("detail"):
            self.ui.label_3.setText(f"API Error: {data.get('detail')}")


    def _populate_group_list(self, groups):
        current_group_id = self._current_group.get("group_id") if isinstance(self._current_group, dict) else None
        self.ui.listWidget.clear()

        for g in groups:
            role = g.get("role", "member")
            text = f"{g.get('group_name', 'Unnamed Group')}  ({role})"
            item = QListWidgetItem(text)
            icon = self._group_icon_from_data(g.get("group_icon"))
            if icon is not None:
                item.setIcon(icon)
            item.setData(Qt.UserRole, g)
            self.ui.listWidget.addItem(item)


        if self.ui.listWidget.count() == 0:
            self._current_group = None
            self._messages = []
            self._oldest_timestamp = None
            self.ui.label_2.setText("No groups")
            self.ui.label_3.setText("Join or create a group first")
            self._render_messages()
            return

        target_row = 0
        if current_group_id is not None:
            for i in range(self.ui.listWidget.count()):
                g = self.ui.listWidget.item(i).data(Qt.UserRole) or {}
                if g.get("group_id") == current_group_id:
                    target_row = i
                    break
        self.ui.listWidget.setCurrentRow(target_row)

    def _filter_groups(self):
        keyword = self.ui.lineEdit.text().strip().lower()
        if not keyword:
            self._populate_group_list(self._all_groups)
            return

        filtered = [
            g for g in self._all_groups
            if keyword in str(g.get("group_name", "")).lower()
        ]
        self._populate_group_list(filtered)

    def _on_group_changed(self, current, _previous):
        if current is None:
            return

        self._current_group = current.data(Qt.UserRole) or {}
        session.current_group_id = self._current_group.get("group_id")
        group_name = str(self._current_group.get("group_name", "Group Chat"))
        group_id = self._current_group.get("group_id", "-")

        self.ui.label_2.setText(group_name)
        self.ui.label_3.setText(f"Group ID: {group_id}")

        self._messages = []
        self._oldest_timestamp = None
        self.load_latest_messages()

    def load_latest_messages(self):
        if not self._current_group:
            return

        group_id = self._current_group.get("group_id")
        if group_id is None:
            return

        data = get_group_messages(group_id=group_id, limit=50)
        msgs = data.get("messages", []) if isinstance(data, dict) else []
        self._messages = [m for m in msgs if isinstance(m, dict)]
        self._oldest_timestamp = self._messages[0].get("timestamp") if self._messages else None
        self._render_messages()

    def load_more_messages(self):
        if not self._current_group or not self._oldest_timestamp:
            return

        group_id = self._current_group.get("group_id")
        if group_id is None:
            return

        data = get_group_messages(group_id=group_id, before=self._oldest_timestamp, limit=50)
        older = [m for m in (data.get("messages", []) if isinstance(data, dict) else []) if isinstance(m, dict)]
        if not older:
            return

        existing_ids = {m.get("message_id") for m in self._messages}
        older = [m for m in older if m.get("message_id") not in existing_ids]
        self._messages = older + self._messages
        self._oldest_timestamp = self._messages[0].get("timestamp") if self._messages else None
        self._render_messages()

    def send_current_message(self):
        if not self._current_group:
            QMessageBox.warning(self, "Send Failed", "Please select a group first.")
            return

        user_id = self._current_user_id()
        if user_id is None:
            QMessageBox.warning(self, "Send Failed", "Please log in first.")
            return

        group_id = self._current_group.get("group_id")
        if group_id is None:
            QMessageBox.warning(self, "Send Failed", "Invalid group.")
            return

        text = self.ui.lineEdit_2.text().strip()
        has_image = bool(self._selected_image_path)
        if not text and not has_image:
            return

        if text:
            res = send_group_message(group_id=group_id, sender_id=user_id, content=text, message_type="text")
            if not res.get("success"):
                QMessageBox.warning(self, "Send Failed", str(res.get("message", "Failed to send text.")))
                return

        if has_image:
            image_content = self._encode_image_to_data_uri(self._selected_image_path)
            if not image_content:
                QMessageBox.warning(self, "Send Failed", "Failed to read image.")
                return
            res = send_group_message(group_id=group_id, sender_id=user_id, content=image_content, message_type="image")
            if not res.get("success"):
                QMessageBox.warning(self, "Send Failed", str(res.get("message", "Failed to send image.")))
                return

        self.ui.lineEdit_2.clear()
        self._clear_image_preview()
        self.load_latest_messages()

    def _pick_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image",
            "",
            "Images (*.png *.jpg *.jpeg *.webp *.gif)"
        )
        if not file_path:
            return

        self._selected_image_path = file_path
        pix = QPixmap(file_path)
        if pix.isNull():
            self._clear_image_preview()
            QMessageBox.warning(self, "Invalid Image", "Please select a valid image file.")
            return

        preview = pix.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.ui.label_4.setText("")
        self.ui.label_4.setPixmap(preview)
        self.ui.frame_5.setVisible(True)
        self.ui.pushButton_3.setVisible(True)

    def _clear_image_preview(self):
        self._selected_image_path = None
        self.ui.label_4.setPixmap(QPixmap())
        self.ui.label_4.setText("")
        self.ui.frame_5.setVisible(False)
        self.ui.pushButton_3.setVisible(False)


    def _encode_image_to_data_uri(self, path):
        try:
            ext = os.path.splitext(path)[1].lower().replace(".", "") or "png"
            mime = "jpeg" if ext == "jpg" else ext
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            return f"data:image/{mime};base64,{b64}"
        except Exception:
            return None

    def _clear_message_layout(self):
        layout = self.ui.verticalLayout_3
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _render_messages(self):
        self._clear_message_layout()

        if not self._messages:
            empty = QLabel("No messages yet")
            empty.setStyleSheet("font-size: 12px; color: #8a7348; padding: 8px;")
            self.ui.verticalLayout_3.addWidget(empty)
            self.ui.verticalLayout_3.addStretch()
            return

        my_id = self._current_user_id()
        for m in self._messages:
            self.ui.verticalLayout_3.addWidget(self._build_message_row(m, my_id))
        self.ui.verticalLayout_3.addStretch()

    def _build_message_row(self, message, my_id):
        sender_id = message.get("sender_id")
        sender_name = str(message.get("sender_name") or "Unknown")
        message_type = str(message.get("message_type") or "text").lower()
        content = str(message.get("content") or "")
        timestamp = str(message.get("timestamp") or "")
        is_mine = (my_id is not None and sender_id == my_id)

        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(6, 4, 6, 4)

        bubble = QFrame()
        bubble.setObjectName("bubble")
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(10, 8, 10, 8)
        bubble_layout.setSpacing(4)

        sender_label = QLabel("You" if is_mine else sender_name)
        sender_label.setStyleSheet("font-size: 11px; color: #8a7348; font-weight: 600;")
        bubble_layout.addWidget(sender_label)

        if message_type == "image":
            image_label = QLabel()
            image_label.setAlignment(Qt.AlignCenter)
            pix = self._pixmap_from_image_content(content)
            if pix is not None and not pix.isNull():
                image_label.setPixmap(pix.scaled(220, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                image_label.setText("[Image]")
                image_label.setStyleSheet("font-size: 13px; color: #4a3b1f;")
            bubble_layout.addWidget(image_label)
        else:
            text_label = QLabel(content)
            text_label.setWordWrap(True)
            text_label.setStyleSheet("font-size: 13px; color: #4a3b1f;")
            bubble_layout.addWidget(text_label)

        if timestamp:
            time_label = QLabel(timestamp.replace("T", " ")[:19])
            time_label.setStyleSheet("font-size: 10px; color: #a08b67;")
            bubble_layout.addWidget(time_label)

        if is_mine:
            bubble.setStyleSheet("QFrame#bubble{background:#ffad5f;border:none;border-radius:10px;}")
            row_layout.addStretch()
            row_layout.addWidget(bubble, 0)
        else:
            bubble.setStyleSheet("QFrame#bubble{background:#ffdd8c;border:none;border-radius:10px;}")
            row_layout.addWidget(bubble, 0)
            row_layout.addStretch()


        return row

    def _group_icon_from_data(self, group_icon):
        if not group_icon:
            return None

        icon_value = str(group_icon).strip()
        if not icon_value:
            return None

        pix = self._pixmap_from_image_content(icon_value)
        if (pix is None or pix.isNull()) and not icon_value.startswith("http"):
            candidate = icon_value
            if icon_value.startswith("/"):
                candidate = f"{BASE_URL}{icon_value}"
            else:
                candidate = f"{BASE_URL}/{icon_value}"
            pix = self._pixmap_from_image_content(candidate)

        if pix is None or pix.isNull():
            return None

        return QIcon(pix.scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def _pixmap_from_image_content(self, content):

        if not content:
            return None

        pix = QPixmap()
        if content.startswith("data:image/") and "," in content:
            try:
                b64 = content.split(",", 1)[1]
                raw = base64.b64decode(b64)
                pix.loadFromData(raw)
                return pix if not pix.isNull() else None
            except Exception:
                return None

        if os.path.exists(content):
            pix = QPixmap(content)
            return pix if not pix.isNull() else None

        if content.startswith("http://") or content.startswith("https://"):
            try:
                res = requests.get(content, timeout=5)
                if res.ok and res.content:
                    pix.loadFromData(res.content)
                    return pix if not pix.isNull() else None
            except Exception:
                return None

        return None
