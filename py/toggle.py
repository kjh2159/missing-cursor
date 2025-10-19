from PyQt6 import QtWidgets, QtCore
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

def get_toggler(opt, app):
    if opt["SHAPE"].lower() == "crosshead" and opt["TRIGGER"].lower() == "spacebar":
        return CursorToggle(key=Qt.Key.Key_Space, cursor=Qt.CursorShape.CrossCursor, parent=app)
