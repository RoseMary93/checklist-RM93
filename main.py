"""
RM93 待辦清單應用程式
一個功能完整的待辦事項管理工具，提供任務追蹤、優先順序管理、歷史紀錄等功能。

主要組件:
- HistoryWindow: 顯示所有任務的歷史紀錄表格
- TodoItem: 單個任務項目的UI元件
- DesktopTodo: 主應用程式窗口
"""

import sys
import sqlite3
from datetime import datetime, date
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QListWidget, QListWidgetItem, QCheckBox, 
                             QPushButton, QLabel, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QInputDialog, QAbstractItemView)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
import os


class HistoryWindow(QWidget):
    """歷史紀錄視窗 - 以表格格式顯示所有任務的建立、完成時間及狀態"""
    def __init__(self):
        """初始化歷史紀錄窗口，設置表格和UI樣式"""
        super().__init__()
        self.setWindowTitle("待辦任務歷史紀錄")
        self.resize(600, 400)
        
        # 設置應用圖標
        icon_path = os.path.join(os.path.dirname(__file__), 'checklist_logo.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # 套用溫暖的色系與字型設定
        self.setStyleSheet("background-color: #FDF5E6; color: black; font-family: '微軟正黑體'; font-size: 13px;")
        
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["任務名稱", "建立時間", "完成時間", "狀態"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("QTableWidget { background-color: white; gridline-color: #D4C960; color: black; }")
        
        layout.addWidget(self.table)
        self.load_history()

    def load_history(self):
        """從資料庫加載所有任務歷史並填充表格"""
        conn = sqlite3.connect('todo_history.db')
        cursor = conn.cursor()
        cursor.execute("SELECT task, created, finished, is_done FROM tasks ORDER BY created DESC")
        rows = cursor.fetchall()
        self.table.setRowCount(len(rows))
        
        for i, (task, created, finished, is_done) in enumerate(rows):
            status = "✅ 已完成" if is_done else "⏳ 待辦中"
            self.table.setItem(i, 0, QTableWidgetItem(task))
            self.table.setItem(i, 1, QTableWidgetItem(created))
            self.table.setItem(i, 2, QTableWidgetItem(finished if finished else "-"))
            self.table.setItem(i, 3, QTableWidgetItem(status))
        conn.close()

class TodoItem(QWidget):
    """任務項目UI元件 - 包含勾選框、任務文字、編輯/刪除/上下移動按鈕"""
    
    def __init__(self, task_id, task_name, is_done, parent_app):
        """
        初始化任務項目
        
        Args:
            task_id: 任務在資料庫中的ID
            task_name: 任務描述文字
            is_done: 是否已完成 (布林值)
            parent_app: 父應用程式實例，用於回呼事件
        """
        super().__init__()
        self.task_id = task_id
        self.parent_app = parent_app
        self.task_name = task_name
        
        # 主容器佈局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5) 
        layout.setSpacing(8)

        # 勾選框
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(bool(is_done))
        self.checkbox.setStyleSheet("""
            QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid #999; background: white; border-radius: 3px; }
            QCheckBox::indicator:checked { background-color: #808080; border: 1px solid #808080; }
        """)
        self.checkbox.stateChanged.connect(lambda: self.parent_app.toggle_task(self.task_id, self.checkbox.isChecked()))

        # 任務標籤（支援自動換行）
        self.label = QLabel(task_name)
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignVCenter)
        if is_done:
            self.label.setStyleSheet("font-size: 13px; color: #777; text-decoration: line-through;")
        else:
            self.label.setStyleSheet("font-size: 13px; color: black;")
        
        layout.addWidget(self.checkbox)
        layout.addWidget(self.label, 1)  # 權重1讓文字佔滿中間區域

        # 動作按鈕容器
        btn_container_widget = QWidget()
        btn_container = QHBoxLayout(btn_container_widget)
        btn_container.setContentsMargins(0, 0, 0, 0)
        btn_container.setSpacing(2)

        # 編輯按鈕
        self.edit_btn = QPushButton("✎")
        self.edit_btn.setFixedSize(20, 20)
        self.edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.edit_btn.setStyleSheet("color: #4682B4; border: none; font-weight: bold; background: transparent; font-size: 12px;")
        self.edit_btn.clicked.connect(self.edit_task_name)
        btn_container.addWidget(self.edit_btn)

        # 刪除按鈕
        self.del_btn = QPushButton("✕")
        self.del_btn.setFixedSize(20, 20)
        self.del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.del_btn.setStyleSheet("color: #D32F2F; border: none; font-weight: bold; background: transparent; font-size: 11px;")
        self.del_btn.clicked.connect(lambda: self.parent_app.delete_task(self.task_id))
        btn_container.addWidget(self.del_btn)

        # 上移按鈕
        self.up_btn = QPushButton("↑")
        self.up_btn.setFixedSize(20, 20)
        self.up_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.up_btn.setStyleSheet("color: #FF8C00; border: none; font-weight: bold; background: transparent; font-size: 11px;")
        self.up_btn.clicked.connect(self.move_up)
        btn_container.addWidget(self.up_btn)

        # 下移按鈕
        self.down_btn = QPushButton("↓")
        self.down_btn.setFixedSize(20, 20)
        self.down_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.down_btn.setStyleSheet("color: #FF8C00; border: none; font-weight: bold; background: transparent; font-size: 11px;")
        self.down_btn.clicked.connect(self.move_down)
        btn_container.addWidget(self.down_btn)

        layout.addWidget(btn_container_widget)

    def edit_task_name(self):
        """開啟編輯對話框修改任務名稱"""
        new_text, ok = QInputDialog.getText(self, "編輯任務", "修改任務名稱:", QLineEdit.EchoMode.Normal, self.task_name)
        if ok and new_text.strip():
            self.parent_app.update_task_text(self.task_id, new_text.strip())

    def move_up(self):
        """將任務在列表中上移"""
        self.parent_app.move_task_up(self.task_id)

    def move_down(self):
        """將任務在列表中下移"""
        self.parent_app.move_task_down(self.task_id)

class DesktopTodo(QWidget):
    """主應用程式視窗 - 管理待辦清單的UI與資料庫交互"""
    
    def __init__(self):
        """初始化應用，設置資料庫、UI與任務列表"""
        super().__init__()
        self.is_pinned = False
        self.init_db()
        self.init_ui()
        self.load_tasks()

    def init_db(self):
        """初始化SQLite資料庫與任務表"""
        self.conn = sqlite3.connect('todo_history.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS tasks 
            (id INTEGER PRIMARY KEY AUTOINCREMENT, task TEXT, created TEXT, finished TEXT, is_done INTEGER, position INTEGER)''')
        self.conn.commit()

    def init_ui(self):
        """初始化使用者介面 - 設置視窗、樣式、佈局與各UI組件"""
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setMinimumSize(300, 350)
        self.resize(320, 450)
        self.setObjectName("MainWindow")
        
        # 應用全局樣式表
        self.setStyleSheet("""
            QWidget#MainWindow { background-color: #FFFACD; border: 1px solid #E6DB74; }
            QLabel { color: black; font-family: '微軟正黑體'; font-size: 13px; }
            QLineEdit { border: 1px solid #D4C960; padding: 6px; background: white; color: black; font-size: 13px; }
            QListWidget { border: none; background: transparent; outline: none; }
            QPushButton { background-color: #F0E68C; color: black; border: 1px solid #BDB76B; padding: 3px; font-size: 12px; }
            QPushButton:hover { background-color: #E6DB74; }
            .SectionTitle { font-weight: bold; background: #EEE8AA; padding: 5px; border-radius: 2px; font-size: 12px; color: #555; }
        """)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 標題列
        title = QLabel("📌 RM93 待辦清單")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-weight: bold; font-size: 15px; padding: 10px; background: #F0E68C; border-bottom: 1px solid #E6DB74;")
        self.main_layout.addWidget(title)

        # 內容區域
        content_container = QWidget()
        container_layout = QVBoxLayout(content_container)
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(8)

        # 任務輸入框
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("新增任務後按 Enter...")
        self.input_field.returnPressed.connect(self.add_task)
        container_layout.addWidget(self.input_field)

        # 待辦事項區
        container_layout.addWidget(QLabel("📝 待辦事項", objectName="SectionTitle"))
        self.todo_list = QListWidget()
        self.todo_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.todo_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.todo_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.todo_list.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.todo_list.model().rowsMoved.connect(self.on_rows_moved)
        container_layout.addWidget(self.todo_list, 3)

        # 完成任務區
        container_layout.addWidget(QLabel("✅ 本日完成任務", objectName="SectionTitle"))
        self.done_list = QListWidget()
        self.done_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.done_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        container_layout.addWidget(self.done_list, 2)

        self.main_layout.addWidget(content_container)

        # 底部按鈕欄
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(12, 0, 12, 12)
        self.history_btn = QPushButton("歷史紀錄")
        self.history_btn.clicked.connect(self.show_history)
        self.pin_btn = QPushButton("📌 釘選")
        self.pin_btn.clicked.connect(self.toggle_pin)
        self.close_btn = QPushButton("關閉便籤")
        self.close_btn.clicked.connect(self.close)
        
        btn_layout.addWidget(self.history_btn)
        btn_layout.addWidget(self.pin_btn)
        btn_layout.addWidget(self.close_btn)
        self.main_layout.addLayout(btn_layout)

    def add_task(self):
        """新增任務到資料庫並刷新UI"""
        text = self.input_field.text().strip()
        if text:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # 取得最大position值以確保新任務排列在末尾
            self.cursor.execute("SELECT MAX(position) FROM tasks")
            max_pos = self.cursor.fetchone()[0]
            new_pos = (max_pos or 0) + 1
            
            self.cursor.execute("INSERT INTO tasks (task, created, is_done, position) VALUES (?, ?, 0, ?)", (text, now, new_pos))
            self.conn.commit()
            self.input_field.clear()
            self.load_tasks()

    def load_tasks(self):
        """從資料庫加載任務並分類顯示（待辦與今日完成）"""
        self.todo_list.clear()
        self.done_list.clear()
        today_str = date.today().strftime("%Y-%m-%d")

        # 載入未完成的任務
        self.cursor.execute("SELECT id, task, is_done FROM tasks WHERE is_done = 0 ORDER BY position ASC")
        for row in self.cursor.fetchall():
            self.add_item_to_widget(self.todo_list, row)

        # 載入今日完成的任務
        self.cursor.execute("SELECT id, task, is_done FROM tasks WHERE is_done = 1 AND finished LIKE ?", (f"{today_str}%",))
        for row in self.cursor.fetchall():
            self.add_item_to_widget(self.done_list, row)

    def add_item_to_widget(self, widget, row):
        """將任務項目加入到清單widget
        
        Args:
            widget: 目標QListWidget
            row: 資料庫查詢結果 (id, task_name, is_done)
        """
        item = QListWidgetItem(widget)
        custom = TodoItem(row[0], row[1], row[2], self)
        
        # 計算可用寬度並設定標籤固定寬度，強制啟用文字換行
        widget.updateGeometries()
        available_width = widget.viewport().width() - 140  # 扣除checkbox、按鈕、邊界與捲軸
        custom.label.setFixedWidth(available_width)
        
        # 刷新高度以適應換行文字
        custom.adjustSize()
        item.setSizeHint(custom.sizeHint())
        
        widget.addItem(item)
        widget.setItemWidget(item, custom)

    def update_task_text(self, task_id, new_name):
        """更新任務名稱"""
        self.cursor.execute("UPDATE tasks SET task=? WHERE id=?", (new_name, task_id))
        self.conn.commit()
        self.load_tasks()

    def toggle_task(self, task_id, is_checked):
        """標記任務完成/未完成，並記錄完成時間"""
        finished_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if is_checked else ""
        self.cursor.execute("UPDATE tasks SET is_done=?, finished=? WHERE id=?", (int(is_checked), finished_time, task_id))
        self.conn.commit()
        self.load_tasks()

    def delete_task(self, task_id):
        """從資料庫刪除任務"""
        self.cursor.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        self.conn.commit()
        self.load_tasks()

    def move_task_up(self, task_id):
        """將任務的position上移一格，並交換相鄰任務的排序"""
        self.cursor.execute("SELECT position FROM tasks WHERE id=?", (task_id,))
        current_pos = self.cursor.fetchone()[0]
        
        # 找到上一個position的任務
        self.cursor.execute("SELECT id, position FROM tasks WHERE is_done=0 AND position < ? ORDER BY position DESC LIMIT 1", (current_pos,))
        prev = self.cursor.fetchone()
        
        if prev:
            prev_id, prev_pos = prev
            # 交換position值
            self.cursor.execute("UPDATE tasks SET position=? WHERE id=?", (prev_pos, task_id))
            self.cursor.execute("UPDATE tasks SET position=? WHERE id=?", (current_pos, prev_id))
            self.conn.commit()
            self.load_tasks()

    def move_task_down(self, task_id):
        """將任務的position下移一格，並交換相鄰任務的排序"""
        self.cursor.execute("SELECT position FROM tasks WHERE id=?", (task_id,))
        current_pos = self.cursor.fetchone()[0]
        
        # 找到下一個position的任務
        self.cursor.execute("SELECT id, position FROM tasks WHERE is_done=0 AND position > ? ORDER BY position ASC LIMIT 1", (current_pos,))
        next_task = self.cursor.fetchone()
        
        if next_task:
            next_id, next_pos = next_task
            # 交換position值
            self.cursor.execute("UPDATE tasks SET position=? WHERE id=?", (next_pos, task_id))
            self.cursor.execute("UPDATE tasks SET position=? WHERE id=?", (current_pos, next_id))
            self.conn.commit()
            self.load_tasks()

    def on_rows_moved(self, parent, start, end, destination, row):
        """拖放完成後，重新計算並更新所有待辦任務的position值"""
        tasks = []
        for i in range(self.todo_list.count()):
            item = self.todo_list.item(i)
            widget = self.todo_list.itemWidget(item)
            if widget:
                tasks.append(widget.task_id)
        
        # 根據新順序更新position
        for idx, task_id in enumerate(tasks):
            self.cursor.execute("UPDATE tasks SET position=? WHERE id=?", (idx + 1, task_id))
        self.conn.commit()

    def show_history(self):
        """開啟歷史紀錄視窗"""
        self.history_win = HistoryWindow()
        self.history_win.show()

    def toggle_pin(self):
        """切換釘選狀態，決定視窗是否始終置頂"""
        self.is_pinned = not self.is_pinned
        if self.is_pinned:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
            self.pin_btn.setText("📌 取消釘選")
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
            self.pin_btn.setText("📌 釘選")
        self.show()

    def resizeEvent(self, event):
        """視窗大小改變時，重新計算任務列高度以適應換行"""
        self.load_tasks()
        super().resizeEvent(event)

    def mousePressEvent(self, event):
        """記錄滑鼠按下位置，用於拖動無邊框視窗"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        """實現無邊框視窗的拖動功能"""
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(self.pos() + event.globalPosition().toPoint() - self.drag_pos)
            self.drag_pos = event.globalPosition().toPoint()


if __name__ == "__main__":
    """應用程式入口點"""
    app = QApplication(sys.argv)
    window = DesktopTodo()
    window.show()
    window.raise_()           # 將視窗推到最上層
    window.activateWindow()   # 取得操作焦點
    sys.exit(app.exec())