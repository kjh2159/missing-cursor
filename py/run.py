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
    w.setMouseTracking(True) 

    # global filter, which is attched to the parent process as a child
    toggler = get_toggler(OPTIONS, app)
    app.installEventFilter(toggler)

    # safeguard to clean handler
    app.aboutToQuit.connect(cleanup_override_cursor)

    app.exec()
