from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtCore import Qt, QEvent

from collections import deque
import time

def make_windows_arrow_cursor(size: int = 24,
                              body_color: str | QtGui.QColor = "#FFFFFF",
                              outline_color: str | QtGui.QColor = "#000000",
                              shadow: bool = True) -> QtGui.QCursor:
    """
    Windows-like cursor style (white body, black outline, slight shade) QCursor creation.
    size: total size in pixels (width=height)
    """
    if isinstance(body_color, str):
        body_color = QtGui.QColor(body_color)
    if isinstance(outline_color, str):
        outline_color = QtGui.QColor(outline_color)

    def P(x, y):  # scale helper
        return QtCore.QPointF(x * s, y * s)

    # base grid for virtual cursor design
    #   tip ──▶ (1,1)
    base_pts = [
        (1, 1),   # tip
        (1, 19),  # left down
        (5, 15),  # inner notch
        (9, 23),  # tail corner
        (12, 21), # tail outer
        (8, 14),  # joint
        (15, 14), # right
    ]
    base = 24.0
    s = size / base

    # path
    path = QtGui.QPainterPath()
    path.moveTo(P(*base_pts[0]))
    for x, y in base_pts[1:]:
        path.lineTo(P(x, y))
    path.closeSubpath()

    # image canvas
    img = QtGui.QImage(size, size, QtGui.QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(0)
    p = QtGui.QPainter(img)
    p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)

    # 1) shade (slight bottom-right)
    if shadow:
        shadow_path = QtGui.QPainterPath(path)
        p.save()
        p.translate(s * 0.9, s * 0.9)
        p.fillPath(shadow_path, QtGui.QColor(0, 0, 0, 90))
        p.restore()

    # 2) body (white)
    p.fillPath(path, body_color)

    # 3) outline (black)
    pen = QtGui.QPen(outline_color)
    pen.setWidth(max(1, int(size // 24)))
    pen.setJoinStyle(QtCore.Qt.PenJoinStyle.MiterJoin)
    pen.setCapStyle(QtCore.Qt.PenCapStyle.FlatCap)
    p.setPen(pen)
    p.drawPath(path)

    p.end()

    pm = QtGui.QPixmap.fromImage(img)
    tip = P(1, 1)  # hotspot: arrow tip
    return QtGui.QCursor(pm, int(tip.x()), int(tip.y()))


def make_colored_like(shape: Qt.CursorShape, color="#00D8FF", size=24) -> QtGui.QCursor:
    # Qt.CursorShape.CrossCursor (for test)
    if shape in (Qt.CursorShape.ArrowCursor, Qt.CursorShape.UpArrowCursor):
        return make_windows_arrow_cursor(size=size, body_color=color, outline_color="#000000", shadow=True)


class CursorToggle(QtCore.QObject):
    def __init__(self, 
                 mode=0,
                 key=Qt.Key.Key_Space,  # default trigger key
                 /,
                 color="#FFFFFF",     # color
                 size=24,               # default size
                 parent=None,
                 shake_enabled=False,
                 window_ms=120, 
                 dist_threshold_px=280, 
                 idle_ms=350): 
        super().__init__(parent)
        self.key = key
        self.color = color
        self.size = size
        self.active = False
        self.mode = mode
        self.default_cursor = Qt.CursorShape.CrossCursor # mode 0

        # shake parameters
        self.shake_enabled = shake_enabled
        self._win_ms = window_ms
        self._dist_th = dist_threshold_px
        self._idle_ms = idle_ms
        self._moves = deque()  # (t_ms, x, y)
        self._last_apply_t = 0.0

        # idle timer
        self._idle_timer = QtCore.QTimer(self)
        self._idle_timer.setSingleShot(True)
        self._idle_timer.timeout.connect(self._restore_if_active)

    def eventFilter(self, obj, e):
        et = e.type()

        # key trigger
        if et == QEvent.Type.KeyPress and getattr(e, "key", None) and e.key() == self.key:
            if not getattr(e, "isAutoRepeat", lambda: False)():
                if not self.active:
                    self._apply_cursor_for(obj)
            return False

        # key release
        if et == QEvent.Type.KeyRelease and getattr(e, "key", None) and e.key() == self.key:
            if not getattr(e, "isAutoRepeat", lambda: False)():
                self._restore()
            return False

        # --- restore ---
        if et in (QEvent.Type.ApplicationDeactivate, QEvent.Type.FocusOut):
            self._restore()
            return False

        # shake trigger
        if self.shake_enabled and et == QEvent.Type.MouseMove:
            self._on_mouse_move(e)
            return False

        return False

    def _restore(self):
        if self.active:
            QtWidgets.QApplication.restoreOverrideCursor()
            self.active = False

    def _apply_cursor_for(self, obj):
        if self.mode != 0:
            cur = QtWidgets.QApplication.overrideCursor()
            shape = cur.shape() if cur else (obj.cursor().shape() if isinstance(obj, QtWidgets.QWidget)
                                             else Qt.CursorShape.ArrowCursor)
            colored = make_colored_like(shape, self.color, self.size)
            QtWidgets.QApplication.setOverrideCursor(colored)
        else:
            QtWidgets.QApplication.setOverrideCursor(self.default_cursor)
        self.active = True

    def _restore_if_active(self):
        # idle timer
        self._restore()

    def _on_mouse_move(self, e):
        # global position
        if hasattr(e, "globalPosition"):
            gx, gy = e.globalPosition().x(), e.globalPosition().y()
        else:
            gp = QtGui.QCursor.pos()
            gx, gy = gp.x(), gp.y()
        now_ms = time.time() * 1000.0

        # window_ms 
        self._moves.append((now_ms, gx, gy))
        cut = now_ms - self._win_ms
        while self._moves and self._moves[0][0] < cut:
            self._moves.popleft()

        # cumulative distance
        if len(self._moves) >= 2:
            dist = 0.0
            it = iter(self._moves)
            t0, x0, y0 = next(it)
            for t1, x1, y1 in it:
                dx, dy = (x1 - x0), (y1 - y0)
                dist += (dx*dx + dy*dy) ** 0.5
                t0, x0, y0 = t1, x1, y1

            # threshold check
            if dist >= self._dist_th and not self.active:
                # obj -> event reciever
                # widget/override shape extraction
                self._apply_cursor_for(e.target() if hasattr(e, "target") else QtWidgets.QApplication.widgetAt(QtGui.QCursor.pos()))

            # big move check (reset timer)
            if dist >= self._dist_th:
                self._idle_timer.start(self._idle_ms)
            else:
                # reset timer by small moves
                pass


def get_toggler(opt, app):
    # Red is a default color for highlight mode.
    if opt["TRIGGER"].lower() == "spacebar" and opt["ACTION"].lower() == "big-size":
        # case 1: hotkey + big-sized
        color = "#FFFFFF" # only big-size
        size = int(opt.get("SIZE", 96))
        return CursorToggle(1, Qt.Key.Key_Space, color=color, size=size, parent=app)
    elif opt["TRIGGER"].lower() == "shake" and opt["ACTION"].lower() == "highlight":
        # case 2: hotkey + colored
        color = opt.get("COLOR", "#FF0000")
        size = 24
        return CursorToggle(1, Qt.Key.Key_Space, color=color, size=size, parent=app)
    elif opt["TRIGGER"].lower() == "shake" and opt["ACTION"].lower() == "big-size":
        # case 3: shake + big-sized
        color =  "#FFFFFF"
        size = int(opt.get("SIZE", 96))
        return CursorToggle(1, None, color=color, size=size, parent=app,
                            shake_enabled=True,window_ms=300, dist_threshold_px=3000, idle_ms=350)
    elif opt["TRIGGER"].lower() == "shake" and opt["ACTION"].lower() == "big-size":
        # case 4: shake + colored
        color = opt.get("COLOR", "#FF0000")
        size = 24
        return CursorToggle(1, None, color=color, size=size, parent=app,
                            shake_enabled=True,window_ms=300, dist_threshold_px=3000, idle_ms=350)

    elif opt["TRIGGER"].lower() == "spacebar" and opt["SHAPE"].lower() == "corsshead":
        # default test case
        return CursorToggle(0, Qt.Key.Key_Space)
    else:
        return CursorToggle(0, Qt.Key.Key_Space)
