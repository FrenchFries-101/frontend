from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QCheckBox, QFrame, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, QDate, QPoint
from PySide6.QtGui import QFont, QScreen
import json
import os


class DesktopPlanWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        # 窗口设置
        self.setFixedSize(280, 400)
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        # 透明背景
        self.setAttribute(Qt.WA_TranslucentBackground)
        # 禁用系统背景
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        
        # 设置窗口位置（屏幕右下角）
        self.set_window_position()
        
        # 初始化 UI
        self.init_ui()
        
        # 加载今日计划
        self.load_today_plan()
    
    def set_window_position(self):
        # 获取屏幕尺寸
        screen = QScreen.availableGeometry(self.screen())
        # 设置窗口位置在屏幕右下角，留出一些边距
        x = screen.width() - self.width() - 100
        y = screen.height() - self.height() - 100
        self.move(x, y)
    
    def init_ui(self):
        # 主容器
        self.main_frame = QFrame()
        self.main_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 243, 232, 230);
                border-radius: 15px;
                border: none;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.main_frame)
        
        # 主布局
        main_layout = QVBoxLayout(self.main_frame)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 标题栏（包含标题和关闭按钮）
        title_layout = QHBoxLayout()
        
        # 标题
        title_label = QLabel("Today's Plan")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setStyleSheet("color: #333333; border: none; background: transparent;")
        title_label.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(title_label)
        
        # 关闭按钮
        close_btn = QPushButton("×")
        close_btn.setFixedSize(25, 25)
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(242, 141, 64, 0.3);
                border: none;
                border-radius: 12px;
                color: #333333;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(242, 141, 64, 0.6);
            }
        """)
        close_btn.clicked.connect(self.hide)
        title_layout.addWidget(close_btn)
        
        main_layout.addLayout(title_layout)
        
        # 日期
        date_label = QLabel(QDate.currentDate().toString("yyyy-MM-dd"))
        date_label.setFont(QFont("Arial", 10))
        date_label.setStyleSheet("color: #666666; border: none; background: transparent;")
        date_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(date_label)
        
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background: rgba(242, 141, 64, 0.3); border: none; max-height: 2px;")
        main_layout.addWidget(separator)
        
        # 任务列表容器
        self.tasks_layout = QVBoxLayout()
        self.tasks_layout.setSpacing(8)
        main_layout.addLayout(self.tasks_layout)
        
        main_layout.addStretch()
    
    def get_task_file_path(self):
        # 获取任务文件路径（与日历组件相同）
        return os.path.join(os.path.expanduser("~"), ".desktop_calendar_tasks.json")
    
    def load_today_plan(self):
        # 清除现有的任务
        for i in reversed(range(self.tasks_layout.count())):
            self.tasks_layout.itemAt(i).widget().setParent(None)
        
        # 获取今日日期
        today = QDate.currentDate().toString("yyyy-MM-dd")
        
        # 默认任务
        default_tasks = [
            "Memorize vocabulary",
            "Listen to audio materials",
            "Practice speaking",
            "Read English articles",
            "Review grammar"
        ]
        
        # 读取任务文件（使用与日历相同的文件）
        tasks = {}
        try:
            with open(self.get_task_file_path(), "r", encoding="utf-8") as f:
                tasks = json.load(f)
        except:
            pass
        
        # 获取今日任务
        if today in tasks and tasks[today].strip():
            # 解析任务（假设任务是用换行分隔的）
            task_list = [task.strip() for task in tasks[today].split('\n') if task.strip()]
        else:
            # 使用默认任务
            task_list = default_tasks
        
        # 加载已完成的任务状态
        completed_file = "completed_tasks.json"
        completed_tasks = {}
        if os.path.exists(completed_file):
            try:
                with open(completed_file, "r", encoding="utf-8") as f:
                    all_completed = json.load(f)
                    completed_tasks = all_completed.get(today, {})
            except:
                pass
        
        # 创建任务复选框
        for i, task in enumerate(task_list):
            checkbox = QCheckBox(task)
            checkbox.setFont(QFont("Arial", 11))
            checkbox.setStyleSheet("""
                QCheckBox {
                    color: #333333;
                    border: none;
                    background: transparent;
                    spacing: 8px;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                    border: 2px solid #F28D40;
                    border-radius: 4px;
                    background: white;
                }
                QCheckBox::indicator:checked {
                    background: #F28D40;
                    border: 2px solid #F28D40;
                }
                QCheckBox::indicator:hover {
                    border: 2px solid #D77A35;
                }
            """)
            
            # 设置已完成的任务
            if completed_tasks.get(str(i), False):
                checkbox.setChecked(True)
            
            # 连接状态变化信号
            checkbox.stateChanged.connect(lambda state, idx=i: self.save_completed_state(idx, state))
            
            self.tasks_layout.addWidget(checkbox)
    
    def save_completed_state(self, task_index, state):
        # 获取今日日期
        today = QDate.currentDate().toString("yyyy-MM-dd")
        completed_file = "completed_tasks.json"
        
        # 读取现有的完成状态
        all_completed = {}
        if os.path.exists(completed_file):
            try:
                with open(completed_file, "r", encoding="utf-8") as f:
                    all_completed = json.load(f)
            except:
                pass
        
        # 更新今日的完成状态
        if today not in all_completed:
            all_completed[today] = {}
        
        all_completed[today][str(task_index)] = (state == 2)  # 2 表示选中状态
        
        # 保存到文件
        try:
            with open(completed_file, "w", encoding="utf-8") as f:
                json.dump(all_completed, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def mousePressEvent(self, event):
        # 允许拖动窗口
        if event.button() == Qt.LeftButton:
            self.offset = event.pos()
    
    def mouseMoveEvent(self, event):
        # 拖动窗口
        if event.buttons() == Qt.LeftButton:
            self.move(self.pos() + event.pos() - self.offset)
