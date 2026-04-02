# ====================== 【万能注入版】调试器代码 ======================
# 本文件直接复制 粘贴到你的 PyQt 项目中 即可使用
from PySide6.QtWidgets import *
from PySide6.QtGui import QPalette, QColor, QCursor, QPixmap, QPen, QPainter
from PySide6.QtCore import Qt, QTimer, QPoint, QEvent, QSize


# debugger.py 完美最终版
class HighlightOverlay(QWidget):
    """全局控件高亮红框"""
    _instance = None

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.hide()

    @staticmethod
    def get():
        if not HighlightOverlay._instance:
            HighlightOverlay._instance = HighlightOverlay()
        return HighlightOverlay._instance

    def highlight(self, widget):
        if not widget or not widget.isVisible():
            self.hide()
            return
        try:
            # 优化1：修正坐标计算，确保高亮框位置准确
            global_rect = widget.rect()
            global_pos = widget.mapToGlobal(global_rect.topLeft())
            # 确保高亮框在屏幕可视区域
            self.setGeometry(global_pos.x(), global_pos.y(),
                             global_rect.width(), global_rect.height())
            widget.window().raise_()
            self.raise_()  # 提升窗口层级确保显示
            self.show()
        except Exception as e:
            print(f"高亮框显示失败: {e}")
            self.hide()

    # 🔥 终极保险：重写绘制事件，强制画背景
    def paintEvent(self, event):
        painter = QPainter(self)
        # 1. 窗口背景色（不透明红色）
        painter.setRenderHint(QPainter.Antialiasing)  # 圆角平滑
        painter.fillRect(self.rect(), QColor(255, 0, 0, 10))  # 红色半透明

        # 2. 边框颜色（白色）
        border_color = QColor(0, 0, 255)
        # 3. 边框宽度
        border_width = 1
        # 画边框
        pen = QPen(border_color)
        pen.setWidth(border_width)
        painter.setPen(pen)
        painter.drawRect(self.rect().adjusted(1, 1, -1, -1))


class _DebugWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎯 PyQt 窗口调试器 | F1开关 | F2暂停 | 多窗口监控 | 鼠标动态抓取控件 | 红色高亮蓝框 | 自动复制到剪贴板")
        self.setFixedSize(720, 700)
        # self.setFixedSize(320, 420)
        self.last_items = []
        self.last_widget = None
        self._init_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self._scan)
        self.timer.start(100)  # 0.1 秒 刷新

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        tip = QLabel("🎯 鼠标悬浮任意控件 → 实时显示目标控件的全部信息")
        tip.setAlignment(Qt.AlignCenter)
        tip.setStyleSheet("font-size:15px; font-weight:bold; color:#222;")
        layout.addWidget(tip)

        self.status_label = QLabel("📋 调试就绪，悬浮查看控件")
        layout.addWidget(self.status_label)

        layout.addWidget(QLabel("✅ 控件样式"))
        self.form_layout = QFormLayout()
        self.form_layout.setSpacing(7)
        layout.addLayout(self.form_layout)

        layout.addWidget(QLabel("📝 控件内容"))
        self.content_label = QLabel()
        self.content_label.setWordWrap(True)
        layout.addWidget(self.content_label)

        layout.addWidget(QLabel("✅ 图片/图标信息"))
        pic_label = QLabel("(无图片)",self)
        pic_label.setWordWrap(True)
        self.pic_wrap = QWidget()
        self.pic_layout = QHBoxLayout(self.pic_wrap)
        self.pic_layout.setContentsMargins(0, 0, 0, 0)
        self.pic_layout.addWidget(pic_label)
        layout.addWidget(self.pic_wrap)

        layout.addWidget(QLabel("✅ 子控件树"))
        self.tree_edit = QTextEdit()
        self.tree_edit.setMaximumHeight(220)
        self.tree_edit.setReadOnly(True)
        layout.addWidget(self.tree_edit)

    def _get_text(self, w):
        try:
            if hasattr(w, "text"):
                return w.text().strip() and "text: "+w.text().strip() or "(空)"
            if hasattr(w, "toPlainText"):
                return w.toPlainText().strip() and "toPlainText: "+w.toPlainText().strip() or "(空)"
            if hasattr(w, "title"):
                return w.title().strip() and "title: "+w.title().strip() or "(空)"
            return "(无内容)"
        except:
            return "(获取失败)"

    def _get_size(self, w):
        try:
            minmax = f"最小: {w.minimumWidth()}×{w.minimumHeight()}" + (w.maximumWidth()<5000 and w.maximumHeight()<5000 and f"，最大: {w.maximumWidth()}×{w.maximumHeight()};" or ";")
            margins = f"内边距: 左{w.contentsMargins().left()}, 上{w.contentsMargins().top()}，右{w.contentsMargins().right()}, 下{w.contentsMargins().bottom()};"
            msg = f"位置({w.x()},{w.y()}), {w.width()}×{w.height()}; {minmax} {margins}"
            return msg
        except:
            return "(获取失败)"

    def _get_layout(self, lay):
        msg = f"{lay.__class__.__name__}" + (lay.objectName() and "(" + lay.objectName() + ")" or "")
        pmsg = f"{lay.parentWidget().__class__.__name__}" + (
                    lay.parentWidget().objectName() and "(" + lay.parentWidget().objectName() + ")" or "")
        margin = lay.contentsMargins()
        margins = f"左{margin.left()}, 上{margin.top()}, 右{margin.right()}, 下{margin.bottom()}"
        spacing = lay.spacing() if hasattr(lay, "spacing") else "无"
        # return f"{msg}<{pmsg} (边距: {margins}; 间距: {spacing}; 子项: {lay.count()})"
        return f"{msg} (边距: {margins}; 间距: {spacing}; 子项: {lay.count()})"

    def _get_pixinfo(self, w):
        try:
            pix = None
            if hasattr(w, "pixmap") and w.pixmap():
                pix = w.pixmap()
            if hasattr(w, "icon") and not pix:
                ico = w.icon()
                if not ico.isNull():
                    # pix = ico.pixmap(32, 32)
                    pix = ico.pixmap(w.iconSize())
            if not pix or pix.isNull():
                return "无图片/图标", None
            return f"图片尺寸：{pix.width()}×{pix.height()}", pix
        except:
            return "获取图片信息失败", None

    def _get_childinfo(self, c):
        msg = f"{c.__class__.__name__}" + (c.objectName() and "(" + c.objectName() + ")" or "")
        pmsg = f"{c.parent().__class__.__name__}" + (
                    c.parent().objectName() and "(" + c.parent().objectName() + ")" or "")
        # pixinfo = self._get_pixinfo(c)[1] and not self._get_pixinfo(c)[1].isNull() and "| " + self._get_pixinfo(c)[0] or ""
        info,pix = self._get_pixinfo(c)
        pixinfo = pix and not pix.isNull() and "| " + info or ""
        layinfo = c.layout() and "| " + self._get_layout(c.layout()) or ""
        # childinfo = f"├─ {msg}<{pmsg} | {self._get_text(c)} {pixinfo} {layinfo}"
        childinfo = f"├─ {msg} | {self._get_text(c)} {pixinfo} {layinfo}"
        return childinfo

    def _scan(self):
        # 判断鼠标是否在调试器窗口内（包括子控件）
        mouse_pos = QCursor.pos()
        mw = QApplication.widgetAt(mouse_pos)

        if not mw:
            # print("out")
            # 窗口外部隐藏高亮框，防止被其他应用隐藏
            HighlightOverlay.get().hide()
            return

        # AI生成的无效代码
        # w = QApplication.widgetAt(mouse_pos)
        # if w == self.root and self.root == mw:
        #     print("target window")
        #     HighlightOverlay.get().hide()
        #     return

        if mw == self:
            # print("self")
            return

        # 如果鼠标在调试器窗口内，不执行扫描逻辑
        # if mw and is_ancestor_of(mw, self):
        if mw and self.isAncestorOf(mw):
            HighlightOverlay.get().hide()
            # print("child")
            return

        # 控件未变化
        HighlightOverlay.get().highlight(mw)
        if mw == self.last_widget:
            return
        self.last_widget = mw

        # 清空控件数组
        self._clear()
        palette = mw.palette()
        info = {}
        info["类型"] = mw.__class__.__name__
        info["对象名"] = mw.objectName() or "(未设置)"
        info["尺寸"] = self._get_size(mw)

        f = mw.font()
        info["文字属性"] = f"字体: {f.family()}; 字号: {f.pointSize()}px; 加粗: "+("是" if f.bold() else "否")
        
        if isinstance(mw, QPushButton):
            info["文字色"] = palette.color(QPalette.ButtonText).name()
            info["背景色"] = palette.color(QPalette.Button).name()
        else:
            info["文字色"] = palette.color(QPalette.WindowText).name()
            info["背景色"] = palette.color(QPalette.Window).name()

        info["布局"] = mw.layout() and self._get_layout(mw.layout()) or "无布局"
        info["QSS"] = mw.styleSheet() if len(mw.styleSheet()) > 0 else "无"

        # 创建并组装每行显示的内容
        for k, v in info.items():
            lab = QLabel(f"{k}：")
            if "色" in k:
                wrap = QWidget()
                h = QHBoxLayout(wrap)
                h.setContentsMargins(0, 0, 0, 0)
                box = QLabel()
                box.setFixedSize(18, 18)
                box.setStyleSheet(f"background-color:{v}; border:1px solid #ccc;")
                h.addWidget(box)
                h.addWidget(QLabel(f" {v}"))
                self.form_layout.addRow(lab, wrap)
                self.last_items += [lab, wrap]
            else:
                vlab = QLabel(str(v[:80] + "..." if len(v) > 80 else v))
                vlab.setWordWrap(True)
                self.form_layout.addRow(lab, vlab)
                self.last_items += [lab, vlab]
        copy_text = "=== 样式信息 ===\n" + "\n".join(f"{k}: {v}" for k, v in info.items())

        content = self._get_text(mw)
        self.content_label.setText(content)
        copy_text += "\n\n===控件内容 ===\n" + content
        
        picinfo,pix = self._get_pixinfo(mw)
        self.clear_layout(self.pic_layout)
        if not pix or pix.isNull():
            pic_label = QLabel(picinfo,self)
            pic_label.setWordWrap(True)
            self.pic_layout.addWidget(pic_label)
        else:
            box = QLabel(self)
            box.setFixedSize(18, 18)
            box.setPixmap(pix.scaled(18, 18, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.pic_layout.addWidget(box)
            self.pic_layout.addWidget(QLabel(f" {picinfo}",self))
        copy_text += "\n\n=== 图片/图标信息 ===\n" + picinfo

        # 获取子控件树内容(递归函数dfs)
        tree = []
        # children包含隐藏组件，布局树单独遍历
        def dfs(node, d=0):
            for c in node.children():
                # 只处理控件，不处理布局和动画等
                if isinstance(c, QWidget):
                    tree.append("  " * d + self._get_childinfo(c))
                    dfs(c, d + 1)
                elif isinstance(c, QLayout):
                    tree.append("  " * d + f"├─ {self._get_layout(c.layout())}")
                    dfs(c, d + 1)
        dfs(mw)
        tree_str = "\n".join(tree) if tree else "无子控件"
        self.tree_edit.setText(tree_str)

        copy_text += "\n\n=== 子控件树 ===\n" + tree_str
        QApplication.clipboard().setText(copy_text)
        # self.copy_label.setText(f"✅ 已复制：{style['控件类型']} | {style['内容']}")

        self.status_label.setText(f"✅ 查看：{info['类型']} | {content}")

    # 删除last_items数组中的子控件
    def _clear(self):
        for i in self.last_items:
            # if isinstance(i, QLabel):
            #     i.clear() # 清空控件里的内容（图片/文字/背景）
            i.deleteLater() # 彻底销毁控件本身
        self.last_items.clear()

    # 递归删除所有子控件
    def clear_layout(self,layout):
        # 从后往前删，防止索引错乱
        while layout.count() > 0:
            # 取出子项
            item = layout.takeAt(0)
            # 如果是控件 → 彻底删除
            if item.widget():
                item.widget().deleteLater()
            # 如果是子布局 → 递归删除
            elif item.layout():
                self.clear_layout(item.layout())
            # 删除项本身
            del item

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_F1:
            self.close()
        elif e.key() == Qt.Key_F2:
            print("toggleScan")
            self.toggleScan()
        else:
            super().keyPressEvent(e)

    def closeEvent(self, e):
        # 优化3：关闭时仅停止定时器和隐藏高亮框，不操作剪贴板（保留最新内容）
        self.timer.stop()
        HighlightOverlay.get().hide()
        # 移除所有剪贴板相关的备份/恢复逻辑，确保剪贴板内容不受影响
        super().closeEvent(e)

    def closeDW(self, e):
        self.timer.stop()
        HighlightOverlay.get().hide()

    def toggleScan(self):
        if self.timer.isActive():
            self.timer.stop()
            HighlightOverlay.get().hide()
        else:
            # 重新获取最新监控控件
            self.timer.start()
            # HighlightOverlay.get().highlight() 

# 绑定后保存全局实例，关闭调试窗口后可重启
class StyleInlineDebugger:
    _instance = None

    def __init__(self):
        self.mws = []
        self.dw = None

    # 替换监控窗口的事件处理
    def _bind(self, mw):
        self.mws += [mw]
        # self.mws.append(mw)
        orig = mw.keyPressEvent
        def key(e):
            if e.key() == Qt.Key_F1:
                # print("toggleWin")
                self.toggleWin()
            elif self.dw and e.key() == Qt.Key_F2:
                # print("toggleScan")
                self.toggleScan()
            else:
                orig(e)
        # self.mouse_window.keyPressEvent = lambda e: e.key()==Qt.Key_F1 and toggleWin(self)
        mw.keyPressEvent = key

        orig2 = mw.closeEvent
        def closeDW(e):
            print("closeDW")
            if self.dw:
                self.dw.closeDW(e)
            orig2(e)
        mw.closeEvent = closeDW

    def toggleWin(self):
        if not self.dw or not self.dw.isVisible():
            self.dw = _DebugWindow()
            self.dw.show()
        else:
            self.dw.close()
            self.dw = None

    def toggleScan(self):
        if not self.dw:
            # 未启或关闭，重启
            self.toggleWin()
        else:
            self.dw.toggleScan()


def bind_debugger(window):
    if not StyleInlineDebugger._instance:
        StyleInlineDebugger._instance = StyleInlineDebugger()
    StyleInlineDebugger._instance._bind(window)


# PyQt 窗口调试器 | F1开关 | F2暂停 | 支持同一应用内多个窗口 | 鼠标动态抓取控件 | 红色高亮蓝框 | 自动复制到剪贴板
# ========== 你的主窗口 __init__ 里只需要加这两行 ==========
# from StyleInlineDebugger import bind_debugger
# bind_debugger(self)
