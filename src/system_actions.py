import ctypes
import time
import threading

HWND_BROADCAST = 0xFFFF
WM_SYSCOMMAND = 0x0112
SC_MONITORPOWER = 0xF170
MONITOR_OFF = 2
MONITOR_ON = -1
MOUSEEVENTF_MOVE = 0x0001

def turn_off_monitor():
    """Turns off the computer monitor display signal safely without blocking."""
    def _do_turn_off():
        try:
            user32 = ctypes.windll.user32
            res = ctypes.c_ulong()
            # SMTO_ABORTIFHUNG = 0x0002
            user32.SendMessageTimeoutW(HWND_BROADCAST, WM_SYSCOMMAND, SC_MONITORPOWER, MONITOR_OFF, 0x0002, 1000, ctypes.byref(res))
        except Exception:
            try:
                user32 = ctypes.windll.user32
                user32.PostMessageW(HWND_BROADCAST, WM_SYSCOMMAND, SC_MONITORPOWER, MONITOR_OFF)
            except Exception:
                pass
    threading.Thread(target=_do_turn_off, daemon=True).start()
    return True

def wake_up_monitor():
    """Simulates a subtle mouse movement to wake up the screen without blocking."""
    def _do_wake():
        try:
            user32 = ctypes.windll.user32
            user32.mouse_event(MOUSEEVENTF_MOVE, 1, 0, 0, 0)
            time.sleep(0.05)
            user32.mouse_event(MOUSEEVENTF_MOVE, -1, 0, 0, 0)
        except Exception:
            pass
    threading.Thread(target=_do_wake, daemon=True).start()
    return True

def lock_workstation():
    """Locks the Windows workstation (equivalent to Win + L)."""
    try:
        user32 = ctypes.windll.user32
        return user32.LockWorkStation() != 0
    except Exception as e:
        print(f"Error locking workstation: {e}")
        return False
