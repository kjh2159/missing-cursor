from PyQt6 import QtWidgets, QtCore
from PyQt6.QtCore import Qt, QEvent
from toggle import get_toggler
from constant import (
    OPTIONS
)

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
    # clean-up stack
    while QtWidgets.QApplication.overrideCursor() is not None:
        QtWidgets.QApplication.restoreOverrideCursor()

app = QtWidgets.QApplication([])
app.setQuitOnLastWindowClosed(True)

w = Demo(); w.show()

# 전역 필터(앱 자식으로 붙여 자동 정리)
toggler = get_toggler(OPTIONS, app)
app.installEventFilter(toggler)

# 안전한 정리 핸들러
app.aboutToQuit.connect(_cleanup_override_cursor)

app.exec()
