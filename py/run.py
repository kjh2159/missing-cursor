import random

from PyQt6 import QtWidgets

from cursor import *
from toggle import get_toggler
from constant import (
    OPTIONS
)

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    app.setQuitOnLastWindowClosed(True)

    w = Demo(); w.show()

    # 전역 필터(앱 자식으로 붙여 자동 정리)
    toggler = get_toggler(OPTIONS, app)
    app.installEventFilter(toggler)

    # 안전한 정리 핸들러
    app.aboutToQuit.connect(cleanup_override_cursor)

    app.exec()
