
import sys
import math
import random
from utils.path_utils import resource_path
from PySide6.QtWidgets import QApplication, QWidget, QLabel
from PySide6.QtCore import (Qt, QTimer, QPointF, QRectF, QThread, Signal)
from PySide6.QtGui import (QPainter, QColor, QPen, QBrush, QRadialGradient,
                            QLinearGradient, QPainterPath, QFont, QMovie, QFontMetrics)


# ══════════════════════════════════════════════════════
#  后台预加载线程 —— 启动后立刻开始 import 重型模块
# ══════════════════════════════════════════════════════

class PreloadThread(QThread):
    progress = Signal(int)
    done     = Signal()

    def run(self):
        # 总共约 3.5 秒跑完，配合 T_PROGRESS=3.8s 启动
        # AppWindow 在主线程 0.8s 就开始创建，这里只是驱动进度条视觉
        steps = [10, 20, 35, 50, 62, 74, 84, 92, 97, 100]
        delays = [200, 250, 350, 400, 350, 300, 280, 350, 400, 300]  # ms
        for pct, delay in zip(steps, delays):
            self.msleep(delay)
            self.progress.emit(pct)
        self.done.emit()


# ══════════════════════════════════════════════════════
#  碎片粒子
# ══════════════════════════════════════════════════════
class Shard:
    def __init__(self, cx, cy):
        self.x  = cx + random.uniform(-30, 30)
        self.y  = cy + random.uniform(-20, 20)
        ang     = random.uniform(0, math.pi * 2)
        spd     = random.uniform(120, 280)
        self.vx = math.cos(ang) * spd
        self.vy = math.sin(ang) * spd - random.uniform(40, 120)
        self.gravity = random.uniform(180, 320)
        self.w  = random.uniform(8, 20)
        self.h  = random.uniform(5, 12)
        self.rot = random.uniform(0, 360)
        self.rot_spd = random.uniform(-180, 180)
        self.alpha = 1.0
        self.color = random.choice([
            QColor(253, 219, 180), QColor(245, 194, 138),
            QColor(254, 243, 199), QColor(251, 146,  60),
            QColor(253, 232, 216), QColor(252, 217, 168),
        ])

    def update(self, dt):
        self.vy  += self.gravity * dt
        self.x   += self.vx * dt
        self.y   += self.vy * dt
        self.rot += self.rot_spd * dt
        self.alpha = max(0.0, self.alpha - dt * 1.4)

    @property
    def alive(self):
        return self.alpha > 0.01


# ══════════════════════════════════════════════════════
#  浮动词粒子
# ══════════════════════════════════════════════════════
VOCAB = ['Hello', 'Campus', 'Dream', 'Study', 'English', 'Word',
         'Learn', 'DIICSU', 'Grow', 'Friend', 'Speak', 'Future',
         'Begin', 'Vocab', 'Reading', 'Listen', 'Write', 'Think']

class FloatWord:
    def __init__(self, w, h):
        self.word  = random.choice(VOCAB)
        self.x     = random.uniform(0.05, 0.95) * w
        self.y     = random.uniform(0.6,  1.05) * h
        self.vy    = random.uniform(-18, -35)
        self.alpha = 0.0
        self.size  = random.uniform(10, 14)
        self.rot   = random.uniform(-12, 12)
        self.life  = random.uniform(3.5, 6.0)
        self.age   = 0.0

    def update(self, dt):
        self.y   += self.vy * dt
        self.age += dt
        t = self.age / self.life
        if t < 0.15:
            self.alpha = t / 0.15
        elif t > 0.75:
            self.alpha = 1.0 - (t - 0.75) / 0.25
        else:
            self.alpha = 1.0

    @property
    def alive(self):
        return self.age < self.life


# ══════════════════════════════════════════════════════
#  主 Splash Widget
# ══════════════════════════════════════════════════════
class SplashScreen(QWidget):

    finished = Signal()   # 通知 main.py 可以显示 AppWindow 了

    # ── 动画时间轴（秒）──
    T_TEXT    = 0.5
    T_CRACK1  = 1.0
    T_WOBBLE1 = 1.7
    T_CRACK2  = 2.0
    T_WOBBLE2 = 2.5
    T_BURST   = 2.85
    T_FOX     = 2.95
    T_FADEOUT = 3.8    # ← 固定时间到了就开始淡出，不等进度条

    def __init__(self, parent=None):
        super().__init__(parent)

        # ── 所有属性必须最先初始化 ──
        self._time           = 0.0
        self._shards         = []
        self._float_words    = []
        self._progress       = 0
        self._burst_done     = False
        self._fox_visible    = False
        self._text_alpha     = 0.0
        self._light_alpha    = 0.0
        self._egg_visible    = True
        self._egg_wobble     = 0.0
        self._crack_phase    = 0
        self._crack_prog     = [0.0] * 6
        self._fox_scale      = 0.0
        self._fox_bounce_t   = 0.0
        self._fox_idle_t     = 0.0
        self._fading_out     = False
        self._fade_alpha     = 1.0

        # ── 窗口 ──
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setStyleSheet("background:#fdf6ee;")
        self.showMaximized()

        # ── Fox GIF ──
        self._fox_label = QLabel(self)
        self._fox_movie = QMovie(resource_path("resources/icons/fox_1.gif"))
        self._fox_label.setMovie(self._fox_movie)
        self._fox_label.setScaledContents(True)
        self._fox_label.setFixedSize(144, 244)
        self._fox_label.hide()

        # ── 60fps 主循环 ──
        self._ticker = QTimer(self)
        self._ticker.setInterval(16)
        self._ticker.timeout.connect(self._tick)
        self._ticker.start()

        # ── 浮动词定时生成 ──
        self._word_timer = QTimer(self)
        self._word_timer.setInterval(600)
        self._word_timer.timeout.connect(
            lambda: self._float_words.append(FloatWord(self.width(), self.height())))
        self._word_timer.start()

        # ══ 关键改动：预加载线程立刻启动，不等动画 ══
        self._thread = PreloadThread()
        self._thread.progress.connect(self._on_progress)
        self._thread.done.connect(self._on_preload_done)
        self._thread.start()   # ← t=0 立刻开始

    # ─────────────────────────────────────────
    #  预加载回调
    # ─────────────────────────────────────────
    def _on_progress(self, v):
        self._progress = v
        self.update()

    def _on_preload_done(self):
        # 预加载完成，进度条立刻跑满
        self._progress = 100
        self.update()
        # 如果动画已经到了淡出阶段就不管；否则什么都不做，等时间轴触发淡出

    # ─────────────────────────────────────────
    #  主循环 Tick
    # ─────────────────────────────────────────
    def _tick(self):
        dt = 0.016
        t  = self._time

        # 文字淡入
        if t >= self.T_TEXT:
            self._text_alpha = min(1.0, self._text_alpha + dt * 1.8)

        # 裂缝阶段
        if t >= self.T_CRACK1 and self._crack_phase < 1:
            self._crack_phase = 1
        if t >= self.T_CRACK2 and self._crack_phase < 2:
            self._crack_phase = 2
        n = 3 if self._crack_phase == 1 else (6 if self._crack_phase == 2 else 0)
        for i in range(n):
            self._crack_prog[i] = min(1.0, self._crack_prog[i] + dt * 3.5)

        # 摇晃
        if self.T_WOBBLE1 <= t < self.T_WOBBLE1 + 0.5:
            phase = (t - self.T_WOBBLE1) / 0.5
            self._egg_wobble = math.sin(phase * math.pi * 3) * 5 * (1 - phase)
        if self.T_WOBBLE2 <= t < self.T_WOBBLE2 + 0.45:
            phase = (t - self.T_WOBBLE2) / 0.45
            self._egg_wobble = math.sin(phase * math.pi * 4) * 8 * (1 - phase)

        # 透光
        if t >= self.T_CRACK1:
            self._light_alpha = min(0.85, self._light_alpha + dt * 0.6)
        if t >= self.T_BURST:
            self._light_alpha = max(0.0, self._light_alpha - dt * 2.5)

        # 爆裂
        if t >= self.T_BURST and not self._burst_done:
            self._burst_done  = True
            self._egg_visible = False
            cx = self.width()  // 2
            cy = self.height() // 2 - 60
            for _ in range(26):
                self._shards.append(Shard(cx, cy))

        # 狐狸出现
        if t >= self.T_FOX and not self._fox_visible:
            self._fox_visible  = True
            self._fox_bounce_t = 0.0
            self._fox_movie.start()
            self._fox_label.show()
            self._place_fox()

        # Fox 弹入
        if self._fox_visible and self._fox_scale < 1.0:
            self._fox_bounce_t += dt
            bt = min(1.0, self._fox_bounce_t / 0.55)
            if bt < 1.0:
                s = math.pow(2, -10 * bt) * math.sin((bt - 0.075) * (2 * math.pi) / 0.3) + 1
                self._fox_scale = max(0.0, min(1.3, s))
            else:
                self._fox_scale = 1.0
            self._apply_fox_transform()

        # Fox 悬浮
        if self._fox_visible and self._fox_scale >= 1.0:
            self._fox_idle_t += dt
            offset = int(math.sin(self._fox_idle_t * 1.8) * 7)
            cx = self.width()  // 2
            cy = self.height() // 2 - 60
            self._fox_label.move(cx - 72, cy - 122 + offset)

        # 碎片 / 浮动词更新
        for sh in self._shards:    sh.update(dt)
        for fw in self._float_words: fw.update(dt)
        self._shards      = [s for s in self._shards      if s.alive]
        self._float_words = [w for w in self._float_words if w.alive]

        # ══ 关键改动：时间到了就淡出，不依赖进度条 ══
        if t >= self.T_FADEOUT:
            self._fading_out = True

        if self._fading_out:
            self._fade_alpha = max(0.0, self._fade_alpha - dt * 1.4)
            self.setWindowOpacity(self._fade_alpha)
            if self._fade_alpha <= 0.0:
                self._ticker.stop()
                self._word_timer.stop()
                self._fox_movie.stop()
                self.finished.emit()   # 通知 main.py
                self.close()
                return

        self._time += dt
        self.update()

    # ─────────────────────────────────────────
    #  工具方法
    # ─────────────────────────────────────────
    def _place_fox(self):
        cx = self.width()  // 2
        cy = self.height() // 2 - 60
        self._fox_label.move(cx - 72, cy - 122)

    def _apply_fox_transform(self):
        w0, h0 = 144, 244
        cx = self.width()  // 2
        cy = self.height() // 2 - 60
        s  = self._fox_scale
        w  = max(1, int(w0 * s))
        h  = max(1, int(h0 * s))
        self._fox_label.setFixedSize(w, h)
        self._fox_label.move(cx - w // 2, cy - h // 2)

    # ─────────────────────────────────────────
    #  Paint
    # ─────────────────────────────────────────
    def paintEvent(self, _event):
        if not hasattr(self, '_time'):
            return

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        W, H = self.width(), self.height()
        cx, cy = W // 2, H // 2 - 60

        p.fillRect(0, 0, W, H, QColor('#fdf6ee'))

        # 浮动词
        for fw in self._float_words:
            p.save()
            p.translate(fw.x, fw.y)
            p.rotate(fw.rot)
            col = QColor(251, 146, 60, int(fw.alpha * 55))
            p.setPen(col)
            p.setFont(QFont('Segoe UI', int(fw.size), QFont.Bold))
            p.drawText(0, 0, fw.word)
            p.restore()

        # 光晕
        if self._light_alpha > 0.001:
            grad = QRadialGradient(QPointF(cx, cy), 180)
            grad.setColorAt(0,   QColor(255, 248, 235, int(self._light_alpha * 220)))
            grad.setColorAt(0.6, QColor(255, 248, 235, int(self._light_alpha * 80)))
            grad.setColorAt(1,   QColor(255, 248, 235, 0))
            p.setBrush(QBrush(grad))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(cx, cy), 200, 200)

        # 蛋
        if self._egg_visible:
            p.save()
            p.translate(cx, cy)
            p.rotate(self._egg_wobble)
            EW, EH = 160, 192
            egg_path = QPainterPath()
            egg_path.moveTo(0, -EH / 2)
            egg_path.cubicTo( EW * 0.62, -EH * 0.48,  EW * 0.62,  EH * 0.32,  0,  EH / 2)
            egg_path.cubicTo(-EW * 0.62,  EH * 0.32, -EW * 0.62, -EH * 0.48,  0, -EH / 2)
            grad = QRadialGradient(QPointF(-EW * 0.12, -EH * 0.18), EW * 0.9)
            grad.setColorAt(0,   QColor('#fff8f2'))
            grad.setColorAt(0.6, QColor('#fde8c8'))
            grad.setColorAt(1,   QColor('#f5c28a'))
            p.setBrush(QBrush(grad))
            p.setPen(QPen(QColor('#f0b070'), 1.5))
            p.drawPath(egg_path)
            # 光泽
            p.setBrush(QBrush(QColor(255, 255, 255, 80)))
            p.setPen(Qt.NoPen)
            p.save()
            p.translate(-EW * 0.18, -EH * 0.22)
            p.rotate(-18)
            p.drawEllipse(QRectF(-13, -19, 26, 38))
            p.restore()
            # 裂缝
            CRACKS = [
                [(0,0),(-14,-30),(-6,-54),(-10,-80)],
                [(0,0),(-26,-14),(-46,-8),(-64,-16)],
                [(0,0),( 22,-14),( 42,-8),( 62,-16)],
                [(0,0),(  6, 26),(-8, 48),(-4, 70)],
                [(0,0),(-18, 16),(-34,10),(-48,22)],
                [(0,0),( 20, 18),( 38,12),( 52,24)],
            ]
            pen = QPen(QColor('#a06010'), 1.8)
            pen.setCapStyle(Qt.RoundCap)
            p.setPen(pen)
            for i, pts in enumerate(CRACKS):
                prog = self._crack_prog[i]
                if prog <= 0:
                    continue
                for seg in range(len(pts) - 1):
                    t0 = seg       / (len(pts) - 1)
                    t1 = (seg + 1) / (len(pts) - 1)
                    if prog <= t0:
                        break
                    lp = min(1.0, (prog - t0) / (t1 - t0))
                    x0, y0 = pts[seg]
                    x1, y1 = pts[seg + 1]
                    p.drawLine(QPointF(x0, y0), QPointF(x0 + (x1-x0)*lp, y0 + (y1-y0)*lp))
            p.restore()

        # 碎片
        for sh in self._shards:
            p.save()
            p.translate(sh.x, sh.y)
            p.rotate(sh.rot)
            col = QColor(sh.color)
            col.setAlphaF(sh.alpha)
            p.setBrush(QBrush(col))
            p.setPen(QPen(QColor(0xf0, 0xb0, 0x70, int(sh.alpha * 200)), 1.2))
            p.drawRoundedRect(QRectF(-sh.w/2, -sh.h/2, sh.w, sh.h), 2, 2)
            p.restore()

        # 品牌文字
        if self._text_alpha > 0.01:
            p.save()
            p.setOpacity(self._text_alpha)
            font = QFont('Segoe UI', 38, QFont.Bold)
            p.setFont(font)
            p.setPen(QColor('#f97316'))
            fm = QFontMetrics(font)
            brand = 'DIIFOX'
            p.drawText(W // 2 - fm.horizontalAdvance(brand) // 2, H // 2 + 130, brand)
            font2 = QFont('Segoe UI', 13)
            p.setFont(font2)
            p.setPen(QColor('#c4956a'))
            sub = 'ENGLISH · DIICSU · 2025'
            fm2 = QFontMetrics(font2)
            p.drawText(W // 2 - fm2.horizontalAdvance(sub) // 2, H // 2 + 158, sub)
            p.restore()

        # 进度条（纯视觉，不阻塞流程）
        BAR_W, BAR_H = 260, 6
        bx = W // 2 - BAR_W // 2
        by = H // 2 + 185
        p.setBrush(QBrush(QColor('#f5e4d0')))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(QRectF(bx, by, BAR_W, BAR_H), 3, 3)
        fill_w = BAR_W * self._progress / 100
        if fill_w > 0:
            grad2 = QLinearGradient(bx, 0, bx + BAR_W, 0)
            grad2.setColorAt(0, QColor('#fb923c'))
            grad2.setColorAt(1, QColor('#f97316'))
            p.setBrush(QBrush(grad2))
            p.drawRoundedRect(QRectF(bx, by, fill_w, BAR_H), 3, 3)
        font3 = QFont('Segoe UI', 10)
        p.setFont(font3)
        p.setPen(QColor('#dbb99a'))
        lbl = 'Loading your English journey...'
        fm3 = QFontMetrics(font3)
        p.drawText(W // 2 - fm3.horizontalAdvance(lbl) // 2, by + 22, lbl)

        p.end()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._fox_visible:
            self._place_fox()
