from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtCore import Qt, QEvent

class CursorToggle(QtCore.QObject):
    def __init__(self, key=Qt.Key.Key_Space, cursor=Qt.CursorShape.CrossCursor, parent=None):
        super().__init__(parent)
        self.key = key
        self.cursor = cursor
        self.active = False

    def eventFilter(self, obj, e):
        if e.type() == QEvent.Type.KeyPress and getattr(e, "key", None) and e.key() == self.key:
            if not getattr(e, "isAutoRepeat", lambda: False)():
                if not self.active:
                    QtWidgets.QApplication.setOverrideCursor(self.cursor)
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

class Demo(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hold SPACE to change cursor")
        self.setMinimumSize(400, 200)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        label = QtWidgets.QLabel("Hold SPACE → cross cursor\nRelease → normal cursor")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(label)

def _cleanup_override_cursor():
    # 남아있을지 모르는 override cursor 스택을 싹 비움
    while QtWidgets.QApplication.overrideCursor() is not None:
        QtWidgets.QApplication.restoreOverrideCursor()

app = QtWidgets.QApplication([])
app.setQuitOnLastWindowClosed(True)

w = Demo(); w.show()

# 전역 필터(앱 자식으로 붙여 자동 정리)
toggler = CursorToggle(key=Qt.Key.Key_Space, cursor=Qt.CursorShape.CrossCursor, parent=app)
app.installEventFilter(toggler)

# 안전한 정리 핸들러
app.aboutToQuit.connect(_cleanup_override_cursor)

app.exec()
