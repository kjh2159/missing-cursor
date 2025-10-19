import random, time

from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtCore import Qt, QEvent

from toast import Toast

class Sleeper(QtCore.QObject):
    done = QtCore.pyqtSignal()

    @QtCore.pyqtSlot(int)
    def run(self, ms):
        # 현재 쓰레드에서만 sleep (GUI 멈추지 않음)
        QtCore.QThread.msleep(ms)  # 또는: import time; time.sleep(ms/1000)
        self.done.emit()

class Demo(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Random cursor & button")
        self.setMinimumSize(500, 350)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        info = QtWidgets.QLabel(
            "Hold SPACE → cross cursor / Release → normal\n"
            "TEST demo version"
        )
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.container = QtWidgets.QWidget(self)  # button region
        self.container.setObjectName("bg")
        self.bg_path = "./py/assets/bg1.png" # test
        self.container.setStyleSheet(f"") # the background would be change like this form
        
        lay = QtWidgets.QVBoxLayout(self)
        lay.addWidget(info)
        lay.addWidget(self.container, stretch=1)

        self.rand_btn = None  # created button

        # do single shot the randomization after show (after geometry is stablized)
        QtCore.QTimer.singleShot(0, self.randomize_once)

    # single shot
    def randomize_once(self):
        # remove existing button
        if self.rand_btn:
            self.rand_btn.setParent(None)
            self.rand_btn.deleteLater()
            self.rand_btn = None

        # sleeper (THREAD way)
        self._thr = QtCore.QThread(self)     # 참조 유지용(로컬 변수만 두면 GC될 수 있음)
        self._worker = Sleeper()
        self._worker.moveToThread(self._thr)

        self._thr.started.connect(lambda: self._worker.run(1000)) #ms
        self._worker.done.connect(self._randomize_once_impl)  #버튼 배치 실행
        self._worker.done.connect(self._thr.quit)
        self._worker.done.connect(self._worker.deleteLater)
        self._thr.finished.connect(self._thr.deleteLater)
        self._thr.start()

    def _randomize_once_impl(self):
        self.randomize_background()
        self.place_random_button()
        self.move_cursor_randomly()
        Toast.show_toast(parent=self, text="Find and click the button from now!", duration_ms=1200, pos="top-center")

    def place_random_button(self):
        # re-create random button
        self.rand_btn = QtWidgets.QPushButton("Random Button", self.container)
        self.rand_btn.resize(self.rand_btn.sizeHint())

        # calculate button size and container region
        br = self.rand_btn.frameGeometry()
        cr = self.container.contentsRect()
        max_x = max(cr.width() - br.width(), 0)
        max_y = max(cr.height() - br.height(), 0)

        rx = random.randint(cr.left(), cr.left() + max_x)
        ry = random.randint(cr.top(), cr.top() + max_y)
        self.rand_btn.move(rx, ry)

        # when clicking the button
        def on_clicked():
            pass
        self.rand_btn.clicked.connect(self.randomize_once)

        self.rand_btn.show()

    def move_cursor_randomly(self):
        # conversion:
        # choose random coordinates in container → global coordinates
        cr = self.container.contentsRect()
        if cr.width() <= 0 or cr.height() <= 0:
            return
        rx = random.randint(cr.left(), cr.right())
        ry = random.randint(cr.top(), cr.bottom())
        local_pt = QtCore.QPoint(rx, ry)
        global_pt = self.container.mapToGlobal(local_pt)
        QtGui.QCursor.setPos(global_pt)

    def randomize_background(self):
        idx = random.randint(1, 10)
        self.bg_path = f"./py/assets/bg{idx}.png"
        self.container.setStyleSheet(f"""
            QWidget#bg {{
                border-image: url('{self.bg_path}') 0 0 0 0 stretch stretch;
            }}
        """)

def cleanup_override_cursor():
    # clean-up stack
    while QtWidgets.QApplication.overrideCursor() is not None:
        QtWidgets.QApplication.restoreOverrideCursor()
