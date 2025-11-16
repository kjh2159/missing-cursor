import random, time
import os, glob, re
from pathlib import Path

from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtCore import Qt, QEvent

from toast import Toast
import measure

class _ClickFilter(QtCore.QObject):
    def __init__(self):
        super().__init__()

    def eventFilter(self, obj, ev):
        if ev.type() != QEvent.Type.MouseButtonPress:
            return False
        if not isinstance(ev, QtGui.QMouseEvent):
            return False
        if ev.button() != Qt.MouseButton.LeftButton:
            return False

        measure.register_click(ev)
        return False

class Sleeper(QtCore.QObject):
    done = QtCore.pyqtSignal()

    @QtCore.pyqtSlot(int)
    def run(self, ms):
        # Sleep only current thread (GUI does not stop)
        QtCore.QThread.msleep(ms)
        self.done.emit()

class Demo(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Missing Cursor Demo")
        self.setMinimumSize(500, 350)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        info = QtWidgets.QLabel(
            "Hold SPACE → cross cursor / Release → normal\n"
            "TEST demo version"
        )
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # ---------- low / mid / high directories----------
        self.bg_levels = ("low", "mid", "high")
        pat = re.compile(r"bg(\d+)\.(png|jpg|jpeg)$", re.I)

        all_by_level: dict[str, list[str]] = {lvl: [] for lvl in self.bg_levels}
        base_root = Path("./py/assets")

        for lvl in self.bg_levels:
            dir_path = base_root / lvl
            if not dir_path.exists():
                continue
            for p in dir_path.glob("bg*.*"):
                if pat.search(p.name):
                    all_by_level[lvl].append(str(p))

        self.bg_paths = self._build_mixed_bg_sequence(all_by_level)

        if not self.bg_paths:
            self.bg_paths = ["./py/assets/mid/bg1.png"]

        self.total_rounds = len(self.bg_paths)
        self.round_no = 0
        self.bg_path = self.bg_paths[0]

        # out_path=None -> auto path decision
        measure.setup_measure(self.total_rounds, out_path=None)
        # ---------------------------------------------------------------

        self.container = QtWidgets.QWidget(self)  # button region
        self.container.setObjectName("bg")
        self.container.setStyleSheet("")
        lay = QtWidgets.QVBoxLayout(self)
        lay.addWidget(info)
        lay.addWidget(self.container, stretch=1)

        self.rand_btn = None  # created button

        # clicks 
        self._click_filter = _ClickFilter()
        QtWidgets.QApplication.instance().installEventFilter(self._click_filter)

        # do single shot the randomization after show (after geometry is stablized)
        QtCore.QTimer.singleShot(0, self.randomize_once)

    def _build_mixed_bg_sequence(self, all_by_level: dict[str, list[str]]) -> list[str]:
        pools: dict[str, list[str]] = {lvl: paths[:] for lvl, paths in all_by_level.items() if paths}
        seq: list[str] = []
        last_level: str | None = None
        rng = random.Random()

        while True:
            non_empty = [lvl for lvl, paths in pools.items() if paths]
            if not non_empty:
                break

            candidates = [lvl for lvl in non_empty if lvl != last_level]
            if not candidates:
                candidates = non_empty

            lvl = rng.choice(candidates)
            paths = pools[lvl]
            idx = rng.randrange(len(paths))
            path = paths.pop(idx)

            seq.append(path)
            last_level = lvl

        return seq

    # single shot
    def randomize_once(self):
        if self.round_no >= self.total_rounds:
            Toast.show_toast(parent=self, text="All rounds finished!", duration_ms=1200, pos="top-center")
            self.close()
            return
        
        self.round_no += 1

        # random pause
        pause = random.randint(1000, 5000) # (1 - 5 sec)

        # remove existing button
        if self.rand_btn:
            self.rand_btn.setParent(None)
            self.rand_btn.deleteLater()
            self.rand_btn = None

        # sleeper (THREAD way)
        self._thr = QtCore.QThread(self)     # maintain reference (prevent garbage collection)
        self._worker = Sleeper()
        self._worker.moveToThread(self._thr)

        self._thr.started.connect(lambda: self._worker.run(pause)) # ms
        self._worker.done.connect(self._randomize_once_impl)  # real implementation
        self._worker.done.connect(self._thr.quit)
        self._worker.done.connect(self._worker.deleteLater)
        self._thr.finished.connect(self._thr.deleteLater)
        self._thr.start()

    def _randomize_once_impl(self):
        if self.round_no > self.total_rounds:
            Toast.show_toast(parent=self, text="All rounds finished!", duration_ms=1200, pos="top-center")
            return
    
        self.randomize_background()
        self.place_random_button()
        self.move_cursor_randomly()
        Toast.show_toast(parent=self, text="Find and click the button from now!", duration_ms=1000, pos="top-center")

        measure.start_round(self.round_no)

    def place_random_button(self):
        # re-create random button
        self.rand_btn = QtWidgets.QPushButton("Click Me!", self.container)
        self.rand_btn.setFont(QtGui.QFont("Arial", 16, QtGui.QFont.Weight.Bold))
        # self.rand_btn.resize(self.rand_btn.sizeHint())

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
            elapsed_ms, clicks = measure.end_round(self.bg_paths)
            Toast.show_toast(parent=self,
                     text=f"Round {self.round_no} : {elapsed_ms:.1f} ms, {clicks} clicks",
                     duration_ms=900, pos="top-center")
            self.randomize_once()

        self.rand_btn.clicked.connect(on_clicked)
        self.rand_btn.show()

    def move_cursor_randomly(self, min_dist_px: int = 150):
        # conversion:
        # choose random coordinates in container → global coordinates
        cr = self.container.contentsRect()
        if cr.width() <= 0 or cr.height() <= 0:
            return
        
        # center of button
        btn_center = None
        if self.rand_btn is not None and self.rand_btn.isVisible():
            # container position
            g = self.rand_btn.geometry()
            btn_center = g.center()
        
        rng = random.Random()
        min_dist_sq = float(min_dist_px) ** 2

        best_pt = None
        best_d2 = -1.0

        # too small region -> limit the number of trials
        for _ in range(50): # number of trials
            rx = random.randint(cr.left(), cr.right())
            ry = random.randint(cr.top(), cr.bottom())
            cand = QtCore.QPoint(rx, ry)

            if btn_center is not None:
                dx = cand.x() - btn_center.x()
                dy = cand.y() - btn_center.y()
                d2 = dx**2 + dy**2

                if d2 < min_dist_sq:
                    continue

                if d2 > best_d2:
                    best_d2 = d2
                    best_pt = cand
                    continue

            
            # condition is satisfied
            best_pt = cand
            break

        # there's no best, then use the farest one.
        if best_pt is None:
            return
        
        global_pt = self.container.mapToGlobal(best_pt)
        QtGui.QCursor.setPos(global_pt)

    def randomize_background(self):
        if not self.bg_paths:
            return
        idx = min(self.round_no - 1, len(self.bg_paths) - 1)
        self.bg_path = self.bg_paths[idx]
        style_path = self.bg_path.replace("\\", "/")
        self.container.setStyleSheet(f"""
            QWidget#bg {{
                border-image: url('{style_path}') 0 0 0 0 stretch stretch;
            }}
        """)

def cleanup_override_cursor():
    # clean-up stack
    while QtWidgets.QApplication.overrideCursor() is not None:
        QtWidgets.QApplication.restoreOverrideCursor()

def install_click_filter_once():
    app = QtWidgets.QApplication.instance()
    if app is None:
        return
    if app.property("_click_filter_installed"):
        return
    f = _ClickFilter()
    app.installEventFilter(f)
    app._click_filter_ref = f                 # GC protection
    app.setProperty("_click_filter_installed", True)