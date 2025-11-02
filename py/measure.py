# Create measure.py with the required measurement utilities.
from pathlib import Path
import time
import threading
import re
import glob
from typing import List, Tuple, Optional

# --- Module-level state (kept simple & threadsafe for Qt usage) ---
_lock = threading.Lock()
_t0_ns: Optional[int] = None
_round_no: int = 0
_total_rounds: int = 0
_out_path: Path = Path("measure.txt")
_header_written: bool = False


def _write_header_if_needed():
    global _header_written
    if not _header_written:
        _out_path.parent.mkdir(parents=True, exist_ok=True)
        with _out_path.open("w", encoding="utf-8") as f:
            f.write("round,time(ms)\n")
        _header_written = True


def discover_backgrounds(assets_dir: str = "./py/assets", pattern: str = r"bg(\d+)\.(png|jpg|jpeg)$") -> List[Tuple[int, str]]:
    """
    Scan assets_dir for bg*.png (or jpg/jpeg) and return a sorted list of (index, path).
    Example files: bg1.png, bg2.png, ..., bg10.png
    """
    regex = re.compile(pattern, re.IGNORECASE)
    found = []
    for p in glob.glob(str(Path(assets_dir) / "bg*.*")):
        m = regex.search(Path(p).name)
        if m:
            idx = int(m.group(1))
            found.append((idx, p))
    # sort by numeric index (stable order)
    found.sort(key=lambda x: x[0])
    return found


def setup_measure(total_rounds: int, out_path: str = "measure.txt") -> None:
    """
    Initialize measurement session. Call once before starting rounds.
    """
    global _round_no, _total_rounds, _out_path, _header_written, _t0_ns
    with _lock:
        _round_no = 0
        _total_rounds = int(total_rounds)
        _out_path = Path(out_path)
        _header_written = False
        _t0_ns = None
        _write_header_if_needed()


def start_round(round_no: int) -> None:
    """
    Mark the 'start' moment for a given round (immediately AFTER the button & cursor are placed).
    """
    global _t0_ns, _round_no
    with _lock:
        _round_no = int(round_no)
        _t0_ns = time.perf_counter_ns()


def end_round() -> float:
    """
    Mark the 'end' moment (right when the user clicks the button).
    Returns elapsed milliseconds for convenience.
    """
    global _t0_ns, _round_no
    with _lock:
        if _t0_ns is None:
            # If for some reason start wasn't called, record zero-length to avoid crashing.
            elapsed_ms = 0.0
        else:
            elapsed_ns = time.perf_counter_ns() - _t0_ns
            elapsed_ms = elapsed_ns / 1e6
        _append_result(_round_no, elapsed_ms)
        _t0_ns = None
        return elapsed_ms


def _append_result(round_no: int, elapsed_ms: float) -> None:
    _write_header_if_needed()
    with _out_path.open("a", encoding="utf-8") as f:
        f.write(f"{round_no},{elapsed_ms:.3f}\n")


def build_unique_bg_order(bg_indices: List[int], *, shuffle_seed: Optional[int] = None) -> List[int]:
    """
    Given a list of available background indices (unique), return an order covering each exactly once.
    If shuffle_seed is provided, ordering is shuffled deterministically.
    """
    order = list(bg_indices)
    if shuffle_seed is not None:
        import random
        rnd = random.Random(shuffle_seed)
        rnd.shuffle(order)
    else:
        # Keep sorted order by default for reproducibility
        order.sort()
    return order


# Optional helper to summarize results (not required but can be handy)
def read_results(out_path: str = "measure.txt") -> List[Tuple[int, float]]:
    """
    Read the measurement results file back into memory.
    """
    results = []
    p = Path(out_path)
    if not p.exists():
        return results
    with p.open("r", encoding="utf-8") as f:
        next(f, None)  # skip header
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r, t = line.split(",", 1)
                results.append((int(r), float(t)))
            except Exception:
                pass
    return results

print("measure.py created with measurement helpers. Save path:", str(_out_path))
