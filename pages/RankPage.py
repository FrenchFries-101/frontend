from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QHBoxLayout, QStyle, QPushButton, QStackedWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis, QBarSeries, QBarSet
from service.api import get_rank_list, get_user_rank
import session

class RankPage(QWidget):
    def __init__(self):
        super().__init__()
        self.current_view = "table"
        self.rank_list = []
        self.init_ui()
        self.load_rank_data()
    
    def init_ui(self):
        self.setStyleSheet("background-color: #FFF3E8;")
        
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("🏆 Leaderboard")
        title.setObjectName("rank_title")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setStyleSheet("color: #333333; padding: 10px;")
        layout.addWidget(title)
        
        # 切换按钮
        button_layout = QHBoxLayout()
        
        self.table_btn = QPushButton("📊 Table")
        self.table_btn.setStyleSheet("""
            QPushButton {
                background: #F28D40;
                border: none;
                border-radius: 8px;
                color: white;
                font-size: 14px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #D77A35;
            }
        """)
        self.table_btn.clicked.connect(lambda: self.switch_view("table"))
        
        self.chart_btn = QPushButton("📈 Chart")
        self.chart_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.5);
                border: 2px solid #F28D40;
                border-radius: 8px;
                color: #333333;
                font-size: 14px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.8);
            }
        """)
        self.chart_btn.clicked.connect(lambda: self.switch_view("chart"))
        
        button_layout.addStretch()
        button_layout.addWidget(self.table_btn)
        button_layout.addWidget(self.chart_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # 堆叠视图
        self.stacked_widget = QStackedWidget()
        
        # 创建表格视图
        self.table_widget = QWidget()
        self.create_table_view()
        self.stacked_widget.addWidget(self.table_widget)
        
        # 创建图表视图
        self.chart_widget = QWidget()
        self.create_chart_view()
        self.stacked_widget.addWidget(self.chart_widget)
        
        layout.addWidget(self.stacked_widget)
        
        # 个人排名信息
        self.user_info_frame = QFrame()
        self.user_info_frame.setStyleSheet("""
            QFrame {
                background-color: #FFF3E8;
                border-radius: 12px;
                border: 2px solid #F28D40;
                padding: 15px;
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
    
    def create_table_view(self):
        table_layout = QVBoxLayout()
        
        # 排行榜表格
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Rank", "Username", "Points"])
        
        # 设置列宽
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        # 隐藏行号
        self.table.verticalHeader().setVisible(False)
        
        # 设置表格不可点击
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        
        # 设置表格样式
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border-radius: 12px;
                border: 2px solid rgba(0, 0, 0, 0.1);
            }
            QTableWidget::item {
                padding: 12px;
                font-size: 14px;
                color: #333333;
            }
            QTableWidget::item:alternate {
                background-color: #FFF8F0;
            }
            QHeaderView::section {
                background-color: #FFF3E8;
                color: #333333;
                padding: 12px;
                font-weight: bold;
                font-size: 14px;
                border: none;
            }
            QTableView QTableCornerButton::section {
                background-color: #FFF3E8;
                border: none;
            }
        """)
        
        table_layout.addWidget(self.table)
        self.table_widget.setLayout(table_layout)
    
    def create_chart_view(self):
        chart_layout = QVBoxLayout()
        
        # 创建图表
        self.chart = QChart()
        self.chart.setTitle("Top 50 Users Points")
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        self.chart.setBackgroundBrush(QColor("#FFF3E8"))
        self.chart.setTitleBrush(QColor("#333333"))
        
        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        self.chart_view.setStyleSheet("""
            QChartView {
                background: white;
                border-radius: 12px;
                border: 2px solid rgba(0, 0, 0, 0.1);
            }
        """)
        
        chart_layout.addWidget(self.chart_view)
        self.chart_widget.setLayout(chart_layout)
    
    def switch_view(self, view_type):
        self.current_view = view_type
        
        if view_type == "table":
            self.table_btn.setStyleSheet("""
                QPushButton {
                    background: #F28D40;
                    border: none;
                    border-radius: 8px;
                    color: white;
                    font-size: 14px;
                    padding: 10px 20px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #D77A35;
                }
            """)
            self.chart_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.5);
                    border: 2px solid #F28D40;
                    border-radius: 8px;
                    color: #333333;
                    font-size: 14px;
                    padding: 10px 20px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.8);
                }
            """)
            self.stacked_widget.setCurrentWidget(self.table_widget)
        else:
            self.table_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.5);
                    border: 2px solid #F28D40;
                    border-radius: 8px;
                    color: #333333;
                    font-size: 14px;
                    padding: 10px 20px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.8);
                }
            """)
            self.chart_btn.setStyleSheet("""
                QPushButton {
                    background: #F28D40;
                    border: none;
                    border-radius: 8px;
                    color: white;
                    font-size: 14px;
                    padding: 10px 20px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #D77A35;
                }
            """)
            self.update_chart()
            self.stacked_widget.setCurrentWidget(self.chart_widget)
    
    def update_chart(self):
        # 清除旧的系列和坐标轴
        self.chart.removeAllSeries()
        # 移除所有坐标轴
        for axis in self.chart.axes():
            self.chart.removeAxis(axis)
        
        # 创建柱状图系列
        bar_set = QBarSet("Points")
        top_20 = self.rank_list[:20]
        
        for user in top_20:
            bar_set.append(user["points"])
        
        bar_series = QBarSeries()
        bar_series.append(bar_set)
        bar_series.setLabelsVisible(True)
        
        self.chart.addSeries(bar_series)
        
        # 设置X轴
        axis_x = QValueAxis()
        axis_x.setRange(0, len(top_20))
        axis_x.setTitleText("Rank")
        axis_x.setLabelFormat("%d")
        self.chart.addAxis(axis_x, Qt.AlignBottom)
        bar_series.attachAxis(axis_x)
        
        # 设置Y轴
        axis_y = QValueAxis()
        if top_20:
            max_points = max(user["points"] for user in top_20)
            axis_y.setRange(0, max_points * 1.1)
        else:
            axis_y.setRange(0, 100)
        axis_y.setTitleText("Points")
        self.chart.addAxis(axis_y, Qt.AlignLeft)
        bar_series.attachAxis(axis_y)
        
        # 设置柱子颜色
        bar_set.setColor(QColor("#F28D40"))
        bar_set.setBorderColor(QColor("#D77A35"))
    
    def load_rank_data(self):
        self.rank_list = get_rank_list()
        current_user = session.user
        
        print("Rank list data:", self.rank_list)
        print("Current user:", current_user)
        
        # 显示前50名
        top_50 = self.rank_list[:50]
        self.table.setRowCount(len(top_50))
        
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
        
        # 填充前50名数据
        for i, user in enumerate(top_50):
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
        
        # 更新图表
        if self.current_view == "chart":
            self.update_chart()
    
    def set_user(self, user):
        # 当用户登录成功后，重新加载排行榜数据
        print("RankPage set_user called with user:", user)
        # 确保session.user被更新
        session.user = user
        # 重新加载排行榜数据
        self.load_rank_data()
