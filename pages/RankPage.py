from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QHBoxLayout, QStyle
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from service.api import get_rank_list, get_user_rank
import session

class RankPage(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_rank_data()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title = QLabel("Leaderboard")
        title.setObjectName("rank_title")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 20, QFont.Bold))
        layout.addWidget(title)
        
        # 排行榜表格
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Rank", "Username", "Points"])
        
        # 设置列宽
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        # 设置表格不可点击
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        
        # 设置表格样式
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #f5f5f5;
                border-radius: 8px;
                border: 1px solid #ddd;
            }
            QTableWidget::item {
                padding: 10px;
            }
            QHeaderView::section {
                background-color: #F28D40;
                color: white;
                padding: 8px;
                font-weight: bold;
            }
        """)
        
        layout.addWidget(self.table)
        
        # 个人排名信息
        self.user_info_frame = QFrame()
        self.user_info_frame.setStyleSheet("""
            QFrame {
                background-color: #FFF3E0;
                border-radius: 8px;
                border: 1px solid #F28D40;
                padding: 10px;
            }
        """)
        user_info_layout = QHBoxLayout()
        
        self.user_rank_label = QLabel("Your Rank: --")
        self.user_rank_label.setFont(QFont("Arial", 12, QFont.Bold))
        
        self.user_name_label = QLabel("Username: --")
        self.user_name_label.setFont(QFont("Arial", 12))
        
        self.user_points_label = QLabel("Points: --")
        self.user_points_label.setFont(QFont("Arial", 12))
        
        user_info_layout.addWidget(self.user_rank_label)
        user_info_layout.addWidget(self.user_name_label)
        user_info_layout.addWidget(self.user_points_label)
        user_info_layout.addStretch()
        
        self.user_info_frame.setLayout(user_info_layout)
        layout.addWidget(self.user_info_frame)
        
        self.setLayout(layout)
    
    def load_rank_data(self):
        rank_list = get_rank_list()
        current_user = session.user
        
        print("Rank list data:", rank_list)
        print("Current user:", current_user)
        
        # 只显示前10名
        top_10 = rank_list[:10]
        self.table.setRowCount(len(top_10))
        
        # 查找当前用户的排名
        user_rank = -1
        user_points = 0
        user_name = ""
        
        if current_user:
            user_id = current_user.get("id")
            user_name = current_user.get("username", "")
            print(f"Current user ID: {user_id}, Username: {user_name}")
            
            if user_id:
                # 使用新的API获取用户排名和积分
                user_rank_data = get_user_rank(user_id)
                print(f"User rank data: {user_rank_data}")
                user_rank = user_rank_data.get("rank", -1)
                user_points = user_rank_data.get("points", 0)
                print(f"Fetched user rank: {user_rank}, points: {user_points}")
        
        # 更新个人排名信息
        print(f"Updating user info: rank={user_rank}, points={user_points}, name={user_name}")
        if user_rank > 0:
            self.user_rank_label.setText(f"Your Rank: {user_rank}")
            self.user_name_label.setText(f"Username: {user_name}")
            self.user_points_label.setText(f"Points: {user_points}")
        else:
            self.user_rank_label.setText("Your Rank: Not ranked")
            self.user_name_label.setText(f"Username: {user_name}")
            self.user_points_label.setText(f"Points: {user_points}")
        
        # 填充前10名数据
        for i, user in enumerate(top_10):
            # 排名
            rank_item = QTableWidgetItem(str(i + 1))
            rank_item.setTextAlignment(Qt.AlignCenter)
            
            # 设置前三名的样式
            if i < 3:
                rank_item.setFont(QFont("Arial", 12, QFont.Bold))
                if i == 0:  # 第一名
                    rank_item.setForeground(QColor("#FFD700"))  # 金色
                elif i == 1:  # 第二名
                    rank_item.setForeground(QColor("#C0C0C0"))  # 银色
                else:  # 第三名
                    rank_item.setForeground(QColor("#CD7F32"))  # 铜色
            
            self.table.setItem(i, 0, rank_item)
            
            # 用户名
            username_item = QTableWidgetItem(user["username"])
            username_item.setTextAlignment(Qt.AlignCenter)
            
            # 如果是当前用户，高亮显示
            if current_user and user.get("id") == current_user.get("id"):
                username_item.setFont(QFont("Arial", 11, QFont.Bold))
                username_item.setForeground(QColor("#1976D2"))
            
            self.table.setItem(i, 1, username_item)
            
            # 积分
            points_item = QTableWidgetItem(str(user["points"]))
            points_item.setTextAlignment(Qt.AlignCenter)
            
            # 如果是当前用户，高亮显示
            if current_user and user.get("id") == current_user.get("id"):
                points_item.setFont(QFont("Arial", 11, QFont.Bold))
                points_item.setForeground(QColor("#1976D2"))
            
            self.table.setItem(i, 2, points_item)
    
    def set_user(self, user):
        # 当用户登录成功后，重新加载排行榜数据
        print("RankPage set_user called with user:", user)
        # 确保session.user被更新
        session.user = user
        # 重新加载排行榜数据
        self.load_rank_data()