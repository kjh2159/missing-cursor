from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtCore import Qt, QEvent

class CursorToggle(QtCore.QObject):
    def __init__(self, key=Qt.Key.Key_Space, cursor=Qt.CursorShape.CrossCursor, parent=None):
        super().__init__(parent)
        self.key = key
        self.cursor = cursor
        self.active = False

    def eventFilter(self, obj, e):
        # 1) 키 누름: auto-repeat 무시
        if e.type() == QEvent.Type.KeyPress and getattr(e, "key", None) and e.key() == self.key:
            if not getattr(e, "isAutoRepeat", lambda: False)():
                if not self.active:
                    QtWidgets.QApplication.setOverrideCursor(self.cursor)
                    self.active = True
            return False

        # 2) 키 뗌: auto-repeat 무시하고 복구
        if e.type() == QEvent.Type.KeyRelease and getattr(e, "key", None) and e.key() == self.key:
            if not getattr(e, "isAutoRepeat", lambda: False)():
                self._restore()
            return False

        # 3) 앱 비활성/포커스 아웃일 때도 안전 복구
        if e.type() in (QEvent.Type.ApplicationDeactivate, QEvent.Type.FocusOut):
            self._restore()
            return False

        return False

    def _restore(self):
        if self.active:
            # 우리가 켠 것만 한 번 복구
            QtWidgets.QApplication.restoreOverrideCursor()
            self.active = False

class Demo(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hold SPACE to change cursor")
        self.setMinimumSize(400, 200)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # 포커스 받기 쉽게
        label = QtWidgets.QLabel("Hold SPACE → cross cursor\nRelease → normal cursor")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(label)

app = QtWidgets.QApplication([])
w = Demo(); w.show()

# 전역 필터 설치: 버튼/텍스트 위젯이 스페이스를 먹어도 감지 가능
toggler = CursorToggle(key=Qt.Key.Key_Space, cursor=Qt.CursorShape.CrossCursor)
app.installEventFilter(toggler)

# 앱 종료 시 혹시 남은 override 깨끗이 정리(방어적)
app.aboutToQuit.connect(lambda: [QtWidgets.QApplication.restoreOverrideCursor()
                                 for _ in iter(int, 1) if QtWidgets.QApplication.overrideCursor()])

app.exec()