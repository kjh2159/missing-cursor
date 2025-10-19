from PyQt6 import QtWidgets, QtCore, QtGui

class Toast(QtWidgets.QWidget):
    """Simple in-app toast: fade-in, stay, fade-out."""
    def __init__(self, parent=None, *, duration_ms=1500, margin=16, radius=10):
        super().__init__(parent, flags=QtCore.Qt.WindowType.FramelessWindowHint | 
                                   QtCore.Qt.WindowType.ToolTip)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnTopHint, True)

        self._duration = duration_ms
        self._margin = margin
        self._radius = radius

        self._label = QtWidgets.QLabel("", self)
        self._label.setStyleSheet("""
            QLabel {
                color: white;
                padding: 8px 12px;
                font: 13px "SF Pro Text","Apple SD Gothic Neo","Malgun Gothic";
            }
        """)
        self._label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._label)

        # Opacity animation
        self._eff = QtWidgets.QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._eff)
        self._anim = QtCore.QPropertyAnimation(self._eff, b"opacity", self)
        self._anim.setDuration(200)  # fade in/out 200ms

        # Auto close timer
        self._timer = QtCore.QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._start_fade_out)


    def paintEvent(self, e):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        bg = QtGui.QColor(20, 20, 20, 200)

        rectf = QtCore.QRectF(self.rect())
        path = QtGui.QPainterPath()
        path.addRoundedRect(rectf, float(self._radius), float(self._radius))

        p.fillPath(path, bg)


    def _start_fade_out(self):
        self._anim.stop()
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        self._anim.setDuration(200)
        self._anim.finished.connect(self.close)
        self._anim.start()


    def _place(self, parent, pos="bottom-right"):
        if parent is None:
            screen = QtGui.QGuiApplication.primaryScreen().availableGeometry()
            pr = self.frameGeometry()
            x = screen.right() - pr.width() - self._margin
            y = screen.bottom() - pr.height() - self._margin
            self.move(x, y)
            return
        pr = self.frameGeometry()
        gr = parent.geometry() if parent.isWindow() else parent.window().geometry()
        # 기본: 오른쪽-아래
        x = gr.right() - pr.width() - self._margin
        y = gr.bottom() - pr.height() - self._margin
        if pos == "bottom-left":
            x = gr.left() + self._margin
        elif pos == "top-right":
            y = gr.top() + self._margin
        elif pos == "top-left":
            x = gr.left() + self._margin; y = gr.top() + self._margin
        self.move(x, y)


    @staticmethod
    def show_toast(parent, text: str, *, duration_ms=1500, pos="bottom-right"):
        w = Toast(parent, duration_ms=duration_ms)
        w._label.setText(text)
        w.adjustSize()
        w._place(parent if isinstance(parent, QtWidgets.QWidget) else None, pos=pos)

        # fade in
        w._anim.stop()
        w._eff.setOpacity(0.0)
        QtWidgets.QWidget.show(w)  # ← 이제 안전하지만, 이름도 바꿨으니 충돌 없음
        w._anim.setStartValue(0.0)
        w._anim.setEndValue(1.0)
        w._anim.setDuration(200)
        w._anim.start()

        # stay then fade out
        w._timer.start(duration_ms)
        return w
