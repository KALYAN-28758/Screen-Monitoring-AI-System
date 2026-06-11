import psutil
import platform

# Windows-only support
if platform.system() == "Windows":
    import win32gui
else:
    win32gui = None

# Store previous state
previous_windows = set()
previous_processes = set()


def get_running_processes():
    """Get all running process names."""
    processes = set()

    for proc in psutil.process_iter(["name"]):
        try:
            name = proc.info.get("name")
            if name:
                processes.add(name)
        except Exception:
            pass

    return processes


def get_window_titles():
    """Get visible window titles (Windows only)."""

    if win32gui is None:
        return set()

    titles = set()

    def callback(hwnd, _):
        try:
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd).strip()

                if title and title not in (
                    "Program Manager",
                    "Windows Input Experience",
                ):
                    titles.add(title)

        except Exception:
            pass

    try:
        win32gui.EnumWindows(callback, None)
    except Exception:
        pass

    return titles


def analyze_background_apps():
    global previous_windows
    global previous_processes

    current_processes = get_running_processes()

    # Windows only
    if platform.system() == "Windows":
        current_windows = get_window_titles()
    else:
        current_windows = set()

    changes = []

    new_processes = current_processes - previous_processes
    closed_processes = previous_processes - current_processes

    new_windows = current_windows - previous_windows
    closed_windows = previous_windows - current_windows

    if new_processes:
        changes.append({
            "type": "new_apps",
            "data": sorted(list(new_processes))
        })

    if closed_processes:
        changes.append({
            "type": "closed_apps",
            "data": sorted(list(closed_processes))
        })

    if new_windows:
        changes.append({
            "type": "new_windows",
            "data": sorted(list(new_windows))
        })

    if closed_windows:
        changes.append({
            "type": "closed_windows",
            "data": sorted(list(closed_windows))
        })

    previous_processes = current_processes
    previous_windows = current_windows

    return {
        "platform": platform.system(),
        "running_apps_count": len(current_processes),
        "open_windows_count": len(current_windows),
        "changes": changes
    }
