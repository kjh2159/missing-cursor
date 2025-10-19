import random

from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtCore import Qt, QEvent

from toast import Toast

class Demo(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Random cursor & button")
        self.setMinimumSize(500, 350)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        info = QtWidgets.QLabel(
            "Hold SPACE → cross cursor / Release → normal\n"
            "Window shows → cursor moves randomly & a button spawns randomly."
        )
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.container = QtWidgets.QWidget(self)  # 버튼 올릴 영역
        lay = QtWidgets.QVBoxLayout(self)
        lay.addWidget(info)
        lay.addWidget(self.container, stretch=1)

        self.rand_btn = None  # 생성된 랜덤 버튼 참조용

        # show 된 직후에 랜덤 배치 실행 (geometry가 안정화된 뒤)
        QtCore.QTimer.singleShot(0, self.randomize_once)

    # 한 번만 실행: 랜덤 커서 이동 + 랜덤 버튼 생성
    def randomize_once(self):
        Toast.show_toast(parent=self, text="랜덤 위치로 이동했어요", duration_ms=1200, pos="top-right")
        self.place_random_button()
        self.move_cursor_randomly()

    def place_random_button(self):
        # 기존 버튼 있으면 제거
        if self.rand_btn:
            self.rand_btn.setParent(None)
            self.rand_btn.deleteLater()
            self.rand_btn = None

        self.rand_btn = QtWidgets.QPushButton("Random Button", self.container)
        self.rand_btn.resize(self.rand_btn.sizeHint())

        # 버튼 크기/컨테이너 영역 계산
        br = self.rand_btn.frameGeometry()
        cr = self.container.contentsRect()
        max_x = max(cr.width() - br.width(), 0)
        max_y = max(cr.height() - br.height(), 0)

        rx = random.randint(cr.left(), cr.left() + max_x)
        ry = random.randint(cr.top(), cr.top() + max_y)
        self.rand_btn.move(rx, ry)

        # 클릭 시 동작: pass (아무 것도 안 함)
        def on_clicked():
            pass
        self.rand_btn.clicked.connect(self.randomize_once)

        self.rand_btn.show()

    def move_cursor_randomly(self):
        # 컨테이너 기준 랜덤 좌표 선택 → 전역 좌표로 변환
        cr = self.container.contentsRect()
        if cr.width() <= 0 or cr.height() <= 0:
            return
        rx = random.randint(cr.left(), cr.right())
        ry = random.randint(cr.top(), cr.bottom())
        local_pt = QtCore.QPoint(rx, ry)
        global_pt = self.container.mapToGlobal(local_pt)
        QtGui.QCursor.setPos(global_pt)


def cleanup_override_cursor():
    # clean-up stack
    while QtWidgets.QApplication.overrideCursor() is not None:
        QtWidgets.QApplication.restoreOverrideCursor()
