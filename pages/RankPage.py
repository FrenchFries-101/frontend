from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QHBoxLayout
from PySide6.QtCore import Qt
from service.api import get_rank_list

class RankPage(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_rank_data()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 标题
        title = QLabel("Leaderboard")
        title.setObjectName("rank_title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 排行榜表格
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Rank", "Username", "Points"])
        
        # 设置列宽
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def load_rank_data(self):
        rank_list = get_rank_list()
        self.table.setRowCount(len(rank_list))
        
        for i, user in enumerate(rank_list):
            # 排名
            rank_item = QTableWidgetItem(str(i + 1))
            rank_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 0, rank_item)
            
            # 用户名
            username_item = QTableWidgetItem(user["username"])
            username_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 1, username_item)
            
            # 积分
            points_item = QTableWidgetItem(str(user["points"]))
            points_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 2, points_item)