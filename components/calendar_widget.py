from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGridLayout, QTextEdit, QDialog, QDialogButtonBox
from PySide6.QtCore import QDate, Qt
import json
import os

class CalendarWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.load_tasks()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 月份导航
        nav_layout = QHBoxLayout()
        self.prev_btn = QPushButton("<")
        self.next_btn = QPushButton(">")
        self.month_label = QLabel()
        
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.month_label, 1, Qt.AlignCenter)
        nav_layout.addWidget(self.next_btn)
        
        layout.addLayout(nav_layout)
        
        # 星期标题
        week_layout = QHBoxLayout()
        weekdays = ["日", "一", "二", "三", "四", "五", "六"]
        for day in weekdays:
            label = QLabel(day)
            label.setAlignment(Qt.AlignCenter)
            week_layout.addWidget(label)
        
        layout.addLayout(week_layout)
        
        # 日期网格
        self.calendar_grid = QGridLayout()
        layout.addLayout(self.calendar_grid)
        
        # 当前日期
        self.current_date = QDate.currentDate()
        self.update_calendar()
        
        # 信号连接
        self.prev_btn.clicked.connect(self.prev_month)
        self.next_btn.clicked.connect(self.next_month)
        
        self.setLayout(layout)
    
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
                        date_str += f"\n{task[:10]}..." if len(task) > 10 else f"\n{task}"
                    
                    btn = QPushButton(date_str)
                    btn.setMinimumHeight(60)
                    btn.setStyleSheet("text-align: left; padding: 5px;")
                    
                    # 设置今天的样式
                    if date == QDate.currentDate():
                        btn.setStyleSheet("text-align: left; padding: 5px; background-color: #e3f2fd;")
                    
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
        return os.path.join(os.path.expanduser("~"), ".calendar_tasks.json")
    
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
        
        layout = QVBoxLayout()
        
        # 日期标签
        date_label = QLabel(self.date.toString("yyyy年MM月dd日"))
        layout.addWidget(date_label)
        
        # 任务编辑框
        self.task_edit = QTextEdit()
        self.task_edit.setPlaceholderText("请输入今日任务...")
        
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