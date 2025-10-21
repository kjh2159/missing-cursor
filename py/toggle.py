from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtCore import Qt, QEvent

from PyQt6 import QtGui, QtCore

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
                 parent=None): 
        super().__init__(parent)
        self.key = key
        self.color = color
        self.size = size
        self.active = False
        self.mode = mode
        self.default_cursor = Qt.CursorShape.CrossCursor # mode 0

    def eventFilter(self, obj, e):
        if e.type() == QEvent.Type.KeyPress and getattr(e, "key", None) and e.key() == self.key:
            if not getattr(e, "isAutoRepeat", lambda: False)():
                if not self.active and self.mode != 0:
                    # By option, (override → widget → base)
                    cur = QtWidgets.QApplication.overrideCursor()
                    shape = cur.shape() if cur else (obj.cursor().shape() if isinstance(obj, QtWidgets.QWidget) else Qt.CursorShape.ArrowCursor)
                    colored = make_colored_like(shape, self.color, self.size)
                    QtWidgets.QApplication.setOverrideCursor(colored)
                    self.active = True
                elif not self.active and self.mode == 0:
                    QtWidgets.QApplication.setOverrideCursor(self.default_cursor)
                    self.active = True
            return False

        if e.type() == QEvent.Type.KeyRelease and getattr(e, "key", None) and e.key() == self.key:
            if not getattr(e, "isAutoRepeat", lambda: False)():
                self._restore()
            return False

        if e.type() in (QEvent.Type.ApplicationDeactivate, QEvent.Type.FocusOut):
            self._restore()
            return False

        return False

    def _restore(self):
        if self.active:
            QtWidgets.QApplication.restoreOverrideCursor()
            self.active = False


def get_toggler(opt, app):
    if opt["TRIGGER"].lower() == "spacebar" and opt["ACTION"].lower() == "big-size":
        # case 1: hotkey + big-sized
        # case 2: hotkey + colored
        color = opt.get("COLOR", "#FFFFFF")
        size = int(opt.get("SIZE", 96))
        return CursorToggle(1, Qt.Key.Key_Space, color=color, size=size, parent=app)
    
    elif opt["TRIGGER"].lower() == "spacebar" and opt["SHAPE"].lower() == "corsshead":
        # default test case
        return CursorToggle(0, Qt.Key.Key_Space)
    else:
        return CursorToggle(0, Qt.Key.Key_Space)
