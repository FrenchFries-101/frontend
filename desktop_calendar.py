import sys
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                                QPushButton, QLabel, QGridLayout, QTextEdit, 
                                QDialog, QDialogButtonBox, QFrame)
from PySide6.QtCore import QDate, Qt, QPoint
from PySide6.QtGui import QColor, QFont, QPainter, QBrush, QPen
import json
import os

class DesktopCalendar(QWidget):
    def __init__(self):
        super().__init__()
        self.load_tasks()
        self.init_ui()
        self.setup_drag()
    
    def init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(400, 500)
        
        # 主容器
        self.main_frame = QFrame()
        self.main_frame.setStyleSheet("""
            QFrame {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 15px;
                border: 2px solid rgba(255, 255, 255, 0.3);
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.main_frame)
        self.setLayout(layout)
        
        # 内部布局
        inner_layout = QVBoxLayout()
        inner_layout.setContentsMargins(15, 15, 15, 15)
        inner_layout.setSpacing(10)
        
        # 标题栏
        title_layout = QHBoxLayout()
        
        self.title_label = QLabel("📅 每日便签")
        self.title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: bold;
                font-family: 'Microsoft YaHei', sans-serif;
            }
        """)
        
        # 关闭按钮
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.2);
                border: none;
                border-radius: 15px;
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.4);
            }
        """)
        self.close_btn.clicked.connect(self.close)
        
        title_layout.addWidget(self.title_label, 1)
        title_layout.addWidget(self.close_btn)
        
        inner_layout.addLayout(title_layout)
        
        # 月份导航
        nav_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("◀")
        self.prev_btn.setFixedSize(40, 30)
        self.prev_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.2);
                border: none;
                border-radius: 15px;
                color: white;
                font-size: 14px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.4);
            }
        """)
        
        self.next_btn = QPushButton("▶")
        self.next_btn.setFixedSize(40, 30)
        self.next_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.2);
                border: none;
                border-radius: 15px;
                color: white;
                font-size: 14px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.4);
            }
        """)
        
        self.month_label = QLabel()
        self.month_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Microsoft YaHei', sans-serif;
            }
        """)
        self.month_label.setAlignment(Qt.AlignCenter)
        
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.month_label, 1)
        nav_layout.addWidget(self.next_btn)
        
        inner_layout.addLayout(nav_layout)
        
        # 星期标题
        week_layout = QHBoxLayout()
        weekdays = ["日", "一", "二", "三", "四", "五", "六"]
        for day in weekdays:
            label = QLabel(day)
            label.setStyleSheet("""
                QLabel {
                    color: rgba(255, 255, 255, 0.8);
                    font-size: 12px;
                    font-weight: bold;
                }
            """)
            label.setAlignment(Qt.AlignCenter)
            week_layout.addWidget(label)
        
        inner_layout.addLayout(week_layout)
        
        # 日期网格
        self.calendar_grid = QGridLayout()
        self.calendar_grid.setSpacing(5)
        inner_layout.addLayout(self.calendar_grid)
        
        # 当前日期
        self.current_date = QDate.currentDate()
        self.update_calendar()
        
        # 信号连接
        self.prev_btn.clicked.connect(self.prev_month)
        self.next_btn.clicked.connect(self.next_month)
        
        self.main_frame.setLayout(inner_layout)
    
    def setup_drag(self):
        self.drag_position = None
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_position:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        self.drag_position = None
    
    def update_calendar(self):
        # 清空网格
        while self.calendar_grid.count() > 0:
            item = self.calendar_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 更新月份标签
        month_name = self.current_date.toString("yyyy年MM月")
        self.month_label.setText(month_name)
        
        # 获取当月第一天
        first_day = QDate(self.current_date.year(), self.current_date.month(), 1)
        # 获取当月第一天是星期几
        first_day_of_week = first_day.dayOfWeek() % 7  # 0-6，0是星期日
        # 获取当月天数
        days_in_month = self.current_date.daysInMonth()
        
        # 填充日期按钮
        day = 1
        for row in range(6):
            for col in range(7):
                if (row == 0 and col < first_day_of_week) or day > days_in_month:
                    # 空白单元格
                    label = QLabel()
                    self.calendar_grid.addWidget(label, row, col)
                else:
                    # 日期按钮
                    date = QDate(self.current_date.year(), self.current_date.month(), day)
                    date_str = str(day)
                    
                    # 检查是否有任务
                    task = self.get_task(date)
                    if task:
                        date_str += f"\n{task[:8]}..." if len(task) > 8 else f"\n{task}"
                    
                    btn = QPushButton(date_str)
                    btn.setMinimumSize(45, 45)
                    
                    # 设置今天的样式
                    if date == QDate.currentDate():
                        btn.setStyleSheet("""
                            QPushButton {
                                background: rgba(255, 255, 255, 0.9);
                                border: none;
                                border-radius: 10px;
                                color: #667eea;
                                font-size: 14px;
                                font-weight: bold;
                                text-align: center;
                            }
                            QPushButton:hover {
                                background: white;
                            }
                        """)
                    else:
                        btn.setStyleSheet("""
                            QPushButton {
                                background: rgba(255, 255, 255, 0.2);
                                border: none;
                                border-radius: 10px;
                                color: white;
                                font-size: 14px;
                                text-align: center;
                            }
                            QPushButton:hover {
                                background: rgba(255, 255, 255, 0.4);
                            }
                        """)
                    
                    # 连接点击信号
                    btn.clicked.connect(lambda checked, d=date: self.on_date_clicked(d))
                    
                    self.calendar_grid.addWidget(btn, row, col)
                    day += 1
    
    def prev_month(self):
        self.current_date = self.current_date.addMonths(-1)
        self.update_calendar()
    
    def next_month(self):
        self.current_date = self.current_date.addMonths(1)
        self.update_calendar()
    
    def on_date_clicked(self, date):
        # 显示任务编辑对话框
        dialog = TaskEditDialog(self, date)
        if dialog.exec() == QDialog.Accepted:
            task = dialog.get_task()
            self.save_task(date, task)
            self.update_calendar()
    
    def get_task_file_path(self):
        # 获取任务文件路径
        return os.path.join(os.path.expanduser("~"), ".desktop_calendar_tasks.json")
    
    def load_tasks(self):
        # 加载任务
        try:
            with open(self.get_task_file_path(), "r", encoding="utf-8") as f:
                self.tasks = json.load(f)
        except:
            self.tasks = {}
    
    def save_tasks(self):
        # 保存任务
        with open(self.get_task_file_path(), "w", encoding="utf-8") as f:
            json.dump(self.tasks, f, ensure_ascii=False, indent=2)
    
    def get_task(self, date):
        # 获取指定日期的任务
        date_str = date.toString("yyyy-MM-dd")
        return self.tasks.get(date_str, "")
    
    def save_task(self, date, task):
        # 保存指定日期的任务
        date_str = date.toString("yyyy-MM-dd")
        if task:
            self.tasks[date_str] = task
        else:
            if date_str in self.tasks:
                del self.tasks[date_str]
        self.save_tasks()

class TaskEditDialog(QDialog):
    def __init__(self, parent, date):
        super().__init__(parent)
        self.date = date
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle(f"编辑 {self.date.toString('yyyy年MM月dd日')} 的任务")
        self.setMinimumWidth(400)
        self.setStyleSheet("""
            QDialog {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }
            QLabel {
                color: white;
                font-size: 14px;
                font-family: 'Microsoft YaHei', sans-serif;
            }
            QTextEdit {
                background: rgba(255, 255, 255, 0.9);
                border: none;
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
                font-family: 'Microsoft YaHei', sans-serif;
            }
            QPushButton {
                background: rgba(255, 255, 255, 0.2);
                border: none;
                border-radius: 10px;
                color: white;
                font-size: 14px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.4);
            }
            QDialogButtonBox {
                background: transparent;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 日期标签
        date_label = QLabel(f"📝 {self.date.toString('yyyy年MM月dd日')} 的任务")
        date_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
            }
        """)
        layout.addWidget(date_label)
        
        # 任务编辑框
        self.task_edit = QTextEdit()
        self.task_edit.setPlaceholderText("请输入今日任务...")
        self.task_edit.setMinimumHeight(200)
        
        # 加载现有任务
        parent = self.parent()
        if hasattr(parent, "get_task"):
            task = parent.get_task(self.date)
            self.task_edit.setPlainText(task)
        
        layout.addWidget(self.task_edit)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def get_task(self):
        return self.task_edit.toPlainText().strip()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    calendar = DesktopCalendar()
    calendar.show()
    
    sys.exit(app.exec())