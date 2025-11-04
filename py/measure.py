from pathlib import Path
import time, threading, re, glob, os
from typing import List, Tuple, Optional, Any, LiteralString

# constants
from constant import OPTIONS

# --- Module-level state (thread-safe) ---
_lock = threading.Lock()
_t0_ns: Optional[int] = None          # round start time (ns)
_round_no: int = 0
_total_rounds: int = 0
_out_path: LiteralString = os.path.join(OPTIONS["DIR"], OPTIONS["FILENAME"])
_header_written: bool = False
_clicks_in_round: int = 0

# NEW: robust de-duplication for multiple press notifications
_seen_click_keys: set = set()
_last_click_ns: Optional[int] = None   # fallback dedup when no event timestamp


# ----------------- I/O helpers -----------------
def _write_header() -> None:
    _out_path.parent.mkdir(parents=True, exist_ok=True)
    with _out_path.open("w", encoding="utf-8") as f:
        f.write("round,time(ms),clicks\n")


def _write_header_if_needed() -> None:
    global _header_written
    if not _header_written:
        _write_header()
        _header_written = True


def _append_result(round_no: int, elapsed_ms: float, clicks: int) -> None:
    _write_header_if_needed()
    with _out_path.open("a", encoding="utf-8") as f:
        f.write(f"{round_no},{elapsed_ms:.3f},{clicks}\n")


# ----------------- Public API -----------------
def setup_measure(total_rounds: int, out_path: str = "measure.txt") -> None:
    """Initialize session and (re)write CSV header."""
    global _round_no, _total_rounds, _out_path, _header_written, _t0_ns, _clicks_in_round, _seen_click_keys, _last_click_ns
    with _lock:
        _round_no = 0
        _total_rounds = int(total_rounds)
        _out_path = Path(out_path)
        _header_written = False
        _t0_ns = None
        _clicks_in_round = 0
        _seen_click_keys = set()
        _last_click_ns = None
        _write_header_if_needed()


def is_active() -> bool:
    """True iff a round is currently timing."""
    return _t0_ns is not None


def _event_key(ev: Any) -> Optional[Tuple[int, int, int, int]]:
    """Build a stable key for a mouse press to de-duplicate repeated deliveries.
    Key: (timestamp_ms, button, global_x, global_y)"""
    try:
        ts = int(ev.timestamp())  # QInputEvent::timestamp (ms, int)
        btn = int(ev.button())
        # PyQt6: globalPosition() -> QPointF ; older: globalPos() -> QPoint
        gp = getattr(ev, "globalPosition", None)
        if gp is not None:
            p = ev.globalPosition()
            gx, gy = int(p.x()), int(p.y())
        else:
            p = ev.globalPos()
            gx, gy = int(p.x()), int(p.y())
        return (ts, btn, gx, gy)
    except Exception:
        return None


def register_click(ev: Optional[Any] = None) -> None:
    """Increment click counter if a round is active.
    Accepts optional QMouseEvent to robustly de-duplicate duplicate press notifications."""
    global _clicks_in_round, _last_click_ns, _seen_click_keys
    with _lock:
        if _t0_ns is None:
            return

        # Prefer strong de-duping using event timestamp + position + button
        if ev is not None:
            key = _event_key(ev)
            if key is not None:
                if key in _seen_click_keys:
                    return
                _seen_click_keys.add(key)
                _clicks_in_round += 1
                return

        # Fallback: time-based guard (ignore re-entrancy within 1 ms window)
        now_ns = time.perf_counter_ns()
        if _last_click_ns is not None and (now_ns - _last_click_ns) < 1_000_000:  # 1 ms
            return
        _last_click_ns = now_ns
        _clicks_in_round += 1


def start_round(round_no: int) -> None:
    """Call immediately AFTER button & cursor placement.
    Resets click counter and de-dup structures, then starts the timer."""
    global _t0_ns, _round_no, _clicks_in_round, _seen_click_keys, _last_click_ns
    with _lock:
        _round_no = int(round_no)
        _clicks_in_round = 0
        _seen_click_keys = set()
        _last_click_ns = None
        _t0_ns = time.perf_counter_ns()


def end_round() -> Tuple[float, int]:
    """Call right when the user successfully clicks the button.
    Returns (elapsed_ms, clicks) and appends to CSV."""
    global _t0_ns, _round_no, _clicks_in_round, _seen_click_keys, _last_click_ns
    with _lock:
        if _t0_ns is None:
            elapsed_ms = 0.0
        else:
            elapsed_ns = time.perf_counter_ns() - _t0_ns
            elapsed_ms = elapsed_ns / 1e6
        clicks = _clicks_in_round
        _append_result(_round_no, elapsed_ms, clicks)
        # reset for next round
        _t0_ns = None
        _clicks_in_round = 0
        _seen_click_keys = set()
        _last_click_ns = None
        return elapsed_ms, clicks


def read_results(out_path: str = "measure.txt") -> List[Tuple[int, float, int]]:
    """Read CSV into a list of (round, time_ms, clicks)."""
    results: List[Tuple[int, float, int]] = []
    p = Path(out_path)
    if not p.exists():
        return results
    with p.open("r", encoding="utf-8") as f:
        _ = next(f, None)  # header
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            try:
                if len(parts) == 3:
                    r, t, c = parts
                    results.append((int(r), float(t), int(c)))
                elif len(parts) == 2:
                    r, t = parts
                    results.append((int(r), float(t), 0))
            except Exception:
                pass
    return results


# ----------------- Optional helpers -----------------
def discover_backgrounds(assets_dir: str = "./py/assets",
                         pattern: str = r"bg(\d+)\.(png|jpg|jpeg)$") -> List[Tuple[int, str]]:
    regex = re.compile(pattern, re.IGNORECASE)
    found = []
    for p in glob.glob(str(Path(assets_dir) / "bg*.*")):
        m = regex.search(Path(assets_dir, p).name) if False else regex.search(Path(p).name)
        if m:
            idx = int(m.group(1))
            found.append((idx, p))
    found.sort(key=lambda x: x[0])
    return found


def build_unique_bg_order(bg_indices: List[int], *, shuffle_seed: Optional[int] = None) -> List[int]:
    order = list(bg_indices)
    if shuffle_seed is not None:
        import random
        rnd = random.Random(shuffle_seed)
        rnd.shuffle(order)
    else:
        order.sort()
    return order
