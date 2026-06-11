import mss
import mss.tools
from PIL import Image
import io
import json
import os
from datetime import datetime
from backend.config import settings


# ---------------- ACTIVE WINDOW ----------------
def get_active_window_info() -> dict:
    info = {"title": "Unknown", "app": "Unknown", "all_windows": []}

    try:
        import win32gui
        import win32process
        import psutil

        hwnd = win32gui.GetForegroundWindow()
        info["title"] = win32gui.GetWindowText(hwnd)

        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        try:
            proc = psutil.Process(pid)
            info["app"] = proc.name()
        except Exception:
            pass
    except Exception:
        pass

    try:
        import pygetwindow as gw
        windows = gw.getAllTitles()
        info["all_windows"] = [w for w in windows if w.strip()]
    except Exception:
        pass

    return info


# ---------------- SCREENSHOT CAPTURE ----------------
def capture_full_screen():
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)

        img = Image.frombytes(
            "RGB",
            screenshot.size,
            screenshot.bgra,
            "raw",
            "BGRX"
        )

        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=settings.SCREENSHOT_QUALITY)

        return buffer.getvalue(), {
            "width": screenshot.width,
            "height": screenshot.height,
        }


# ---------------- SAVE FILE (FINAL FIX) ----------------
def save_screenshot(img_bytes: bytes, filename: str) -> str:
    upload_dir = settings.UPLOAD_DIR

    os.makedirs(upload_dir, exist_ok=True)

    filepath = os.path.join(upload_dir, filename)

    print("Saving screenshot to:", filepath)

    with open(filepath, "wb") as f:
        f.write(img_bytes)

    if not os.path.exists(filepath):
        raise RuntimeError(f"Screenshot NOT saved: {filepath}")

    print("Saved:", filename)

    return filename  # return filename ONLY (important fix)


# ---------------- MAIN PIPELINE ----------------
def capture_and_save() -> dict:
    img_bytes, img_meta = capture_full_screen()
    window_info = get_active_window_info()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"screen_{timestamp}.jpg"

    saved_filename = save_screenshot(img_bytes, filename)

    return {
        "filename": saved_filename,
        "filepath": os.path.join(settings.UPLOAD_DIR, saved_filename),
        "img_bytes": img_bytes,
        "active_window": window_info["title"],
        "active_app": window_info["app"],
        "all_windows": json.dumps(window_info["all_windows"]),
        "width": img_meta["width"],
        "height": img_meta["height"],
    }