import os
import sys

# Triple-layer defense against Windows Mark-of-the-Web (Zone.Identifier)
if getattr(sys, 'frozen', False):
    exe_dir = os.path.dirname(sys.executable)
    internal_dir = os.path.join(exe_dir, '_internal')
    if os.path.exists(internal_dir):
        if hasattr(os, 'add_dll_directory'):
            try:
                os.add_dll_directory(internal_dir)
                os.add_dll_directory(exe_dir)
            except Exception:
                pass
        os.environ['PATH'] = f"{internal_dir};{exe_dir};" + os.environ.get('PATH', '')
        
        # Automatically unblock all DLLs (strip Zone.Identifier alternate data streams)
        try:
            for root, _, files in os.walk(internal_dir):
                for f in files:
                    if f.lower().endswith(('.dll', '.exe', '.json')):
                        p = os.path.join(root, f)
                        zone_stream = p + ':Zone.Identifier'
                        if os.path.exists(zone_stream):
                            try:
                                os.remove(zone_stream)
                            except Exception:
                                pass
        except Exception:
            pass

import time
import json
import ctypes
import threading
import webview
import urllib.request
import webbrowser
import tempfile
import shutil
import zipfile
import subprocess

# Ensure src/ directory is in python search path
SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
if os.path.exists(SRC_DIR) and SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from sound_manager import play_break_sound, play_focus_sound, ensure_sounds, set_sound_volume
from system_actions import turn_off_monitor, wake_up_monitor, lock_workstation
from config_manager import load_config, save_config
from distraction_monitor import DistractionMonitor
from productivity_toolkit import MicroChecklist, BrainDumpManager
from focus_spotlight import FocusSpotlight

STATE_IDLE = "IDLE"
STATE_FOCUS = "FOCUS"
STATE_BREAK = "BREAK"
STATE_PAUSED = "PAUSED"

APP_VERSION = "2.1.0"
GITHUB_REPO = "baro-hcmut/focus_flow"

def parse_version_tuple(v_str):
    """Parses a version string like 'v1.0' or '1.0.0' into an integer tuple (1, 0, 0)."""
    cleaned = str(v_str).lower().lstrip('v')
    parts = []
    for p in cleaned.split('.'):
        digits = ''.join(c for c in p if c.isdigit())
        parts.append(int(digits) if digits else 0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])

def check_github_update():
    """Queries GitHub Releases API for the latest release and compares with current version."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    req = urllib.request.Request(url, headers={
        "User-Agent": f"FocusFlow-App/{APP_VERSION}",
        "Accept": "application/vnd.github+json"
    })
    try:
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            latest_tag = data.get("tag_name", "").strip()
            cur_tuple = parse_version_tuple(APP_VERSION)
            latest_tuple = parse_version_tuple(latest_tag)

            has_update = latest_tuple > cur_tuple

            download_url = data.get("html_url", "")
            for asset in data.get("assets", []):
                if asset.get("name", "").endswith(".zip"):
                    download_url = asset.get("browser_download_url")
                    break

            return {
                "has_update": has_update,
                "current_version": f"v{APP_VERSION.lstrip('v')}",
                "latest_version": latest_tag,
                "release_name": data.get("name", latest_tag),
                "release_notes": data.get("body", ""),
                "release_url": data.get("html_url", ""),
                "download_url": download_url,
                "published_at": data.get("published_at", "")
            }
    except Exception as e:
        return {
            "has_update": False,
            "error": str(e),
            "current_version": f"v{APP_VERSION.lstrip('v')}"
        }

PID_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.app.pid')
APP_ICON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'focus_flow_v2.ico')
if not os.path.exists(APP_ICON_PATH):
    APP_ICON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'app_icon.ico')
if not os.path.exists(APP_ICON_PATH):
    APP_ICON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app_icon.ico')
user32 = ctypes.windll.user32

try:
    from System import Action as DotNetAction
except Exception:
    DotNetAction = None

try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Antigravity.FocusFlow.Pomodoro.Pro")
except Exception:
    pass

def apply_app_icon(hwnd):
    """Sets the custom high-res icon to the Win32 window and taskbar asynchronously."""
    try:
        IMAGE_ICON = 1
        LR_LOADFROMFILE = 0x00000010
        LR_DEFAULTSIZE = 0x00000040
        WM_SETICON = 0x0080
        if os.path.exists(APP_ICON_PATH):
            hicon = user32.LoadImageW(None, APP_ICON_PATH, IMAGE_ICON, 0, 0, LR_LOADFROMFILE | LR_DEFAULTSIZE)
            if hicon:
                user32.PostMessageW(hwnd, WM_SETICON, 0, hicon) # ICON_SMALL (non-blocking)
                user32.PostMessageW(hwnd, WM_SETICON, 1, hicon) # ICON_BIG (non-blocking)
    except Exception:
        pass


def manage_single_instance():
    """Kills any lingering previous instance of main.py to prevent duplicate processes."""
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                old_pid = int(f.read().strip())
            if old_pid != os.getpid():
                try:
                    os.kill(old_pid, 9)
                except (OSError, ProcessLookupError):
                    pass
        except Exception:
            pass
    try:
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
    except Exception:
        pass


def ensure_desktop_shortcut():
    """Automatically creates a Desktop shortcut for Focus Flow if in frozen (standalone .exe) mode and shortcut does not exist."""
    if not getattr(sys, 'frozen', False):
        return
    try:
        exe_path = sys.executable
        exe_dir = os.path.dirname(exe_path)
        icon_candidates = [
            os.path.join(exe_dir, 'app_icon.ico'),
            os.path.join(exe_dir, '_internal', 'assets', 'focus_flow_v2.ico'),
            os.path.join(exe_dir, 'assets', 'focus_flow_v2.ico'),
            exe_path
        ]
        icon_path = next((p for p in icon_candidates if os.path.exists(p)), exe_path)

        import win32com.client
        wscript = win32com.client.Dispatch("WScript.Shell")
        user_profile = os.environ.get("USERPROFILE", "")
        desktop_dirs = [
            wscript.SpecialFolders("Desktop"),
            os.path.join(user_profile, "Desktop"),
            os.path.join(user_profile, "OneDrive", "Desktop"),
        ]
        try:
            buf = ctypes.create_unicode_buffer(260)
            ctypes.windll.shell32.SHGetFolderPathW(None, 0, None, 0, buf)
            if buf.value:
                desktop_dirs.insert(0, buf.value)
        except Exception:
            pass

        for d in set(desktop_dirs):
            if os.path.exists(d):
                lnk_path = os.path.join(d, "Focus Flow.lnk")
                sc = wscript.CreateShortcut(lnk_path)
                sc.TargetPath = exe_path
                sc.WorkingDirectory = exe_dir
                sc.IconLocation = f"{icon_path},0"
                sc.Description = "Focus Flow • Pomodoro 50/10 Pro"
                sc.Save()
                try:
                    ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x1000, None, None)
                except Exception:
                    pass
    except Exception:
        pass


class PomodoroApp:
    def __init__(self):
        manage_single_instance()
        ensure_desktop_shortcut()
        ensure_sounds()

        # Load configurations
        self.config = load_config()
        set_sound_volume(self.config.get("sound_volume", 80))
        self.focus_duration = self.config.get("focus_minutes", 50) * 60
        self.break_duration = self.config.get("break_minutes", 10) * 60
        self.target_sessions_val = self.config.get("target_sessions", 3)
        self.enforcement_mode = self.config.get("enforcement_mode", "overlay")
        if self.enforcement_mode == "turnoff":
            self.enforcement_mode = "screen_off"

        # State Variables
        self.state = STATE_IDLE
        self.prev_state = STATE_IDLE
        self.remaining_seconds = self.focus_duration
        self.total_target_seconds = self.focus_duration

        # Load today's history accurately: today starts fresh from daily_history[today]
        today_key = time.strftime("%Y-%m-%d")
        self.current_date = today_key
        history = self.config.setdefault("daily_history", {})
        today_data = history.get(today_key, {})
        self.completed_today = today_data.get("sessions", 0)
        self.total_focus_min = today_data.get("minutes", 0)
        self.current_session = self.completed_today + 1

        self.is_running = True
        self.is_mini_mode = False
        self._mini_mode_lock = threading.Lock()
        self._last_mini_toggle_ts = 0.0
        self._state_lock = threading.Lock()
        self._reflection_pending = False
        self.is_fullscreen_overlay = False
        self.current_distracted_hwnd = None
        self.app_mode = "study" # "study" (Học tập & Làm việc) or "eyecare" (Bảo vệ mắt)
        self.window = None

        # Productivity Modules (Persisted in config.json)
        self.checklist = MicroChecklist(self.config.get("checklist_tasks", []))
        self.brain_dump = BrainDumpManager(self.config.get("brain_dump_notes", []))
        self.spotlight = None
        self._is_updating = False

        self.distraction_monitor = DistractionMonitor(
            brain_dump_manager=self.brain_dump,
            on_barrier_trigger=self._on_distraction_barrier
        )
        self.distraction_monitor.barrier_enabled = self.config.get("friction_barrier_enabled", True)

        # Background countdown timer thread
        self.timer_thread = threading.Thread(target=self._timer_loop, daemon=True)

    def attach_window(self, window):
        self.window = window
        self.window.events.loaded += self._on_window_loaded
        self.window.events.closed += self._on_window_closed
        self.timer_thread.start()

    def _on_window_loaded(self):
        """Initial state push to webview."""
        stats = {
            "completed": self.completed_today,
            "minutes": self.total_focus_min
        }
        js_code = f"window.initAppState({json.dumps(self.config)}, {json.dumps(stats)}, {json.dumps(self.checklist.tasks)}, {json.dumps(self.brain_dump.notes)});"
        self.eval_js(js_code)

        def _set_icon_deferred():
            time.sleep(0.2)
            try:
                native_form = getattr(self.window, 'native', None)
                if native_form and hasattr(native_form, 'Handle'):
                    hwnd = native_form.Handle.ToInt32()
                    if hwnd:
                        apply_app_icon(hwnd)
                        return
            except Exception:
                pass
            try:
                import win32gui
                hwnd = win32gui.FindWindow(None, "Focus Flow • Pomodoro 50/10 Pro")
                if hwnd:
                    apply_app_icon(hwnd)
            except Exception:
                pass

        threading.Thread(target=_set_icon_deferred, daemon=True).start()

        def _check_update_deferred():
            time.sleep(3.0)
            try:
                res = check_github_update()
                if res.get("has_update"):
                    self.eval_js(f"window.onUpdateAvailable && window.onUpdateAvailable({json.dumps(res)});")
            except Exception:
                pass

        threading.Thread(target=_check_update_deferred, daemon=True).start()

    def _on_window_closed(self):
        self.on_close()

    def _run_on_ui_thread(self, fn):
        """
        Non-blocking dispatcher to execute WinForms/Win32 UI mutations safely on the UI thread.
        Prevents cross-thread SetWindowPos/TopMost deadlocks ('not responding' dialog).
        """
        if not self.window or not self.is_running:
            return False
        try:
            native_form = getattr(self.window, 'native', None)
            if native_form and hasattr(native_form, 'BeginInvoke'):
                if hasattr(native_form, 'IsDisposed') and native_form.IsDisposed:
                    return False
                global DotNetAction
                if DotNetAction is None:
                    try:
                        from System import Action as SysAction
                        DotNetAction = SysAction
                    except Exception:
                        pass
                if DotNetAction:
                    def _dispatch_ui():
                        try:
                            if self.is_running and not (hasattr(native_form, 'IsDisposed') and native_form.IsDisposed):
                                fn(native_form)
                        except Exception:
                            pass
                    native_form.BeginInvoke(DotNetAction(_dispatch_ui))
                    return True
        except Exception:
            pass
        return False

    def eval_js(self, code):
        """
        Non-blocking, thread-safe JavaScript dispatcher for pywebview on Windows.
        Directly uses WinForms BeginInvoke to prevent UI thread lockups and
        eliminate the 'Python is not responding' Windows dialog.
        """
        if not self.window or not self.is_running:
            return

        try:
            native_form = getattr(self.window, 'native', None)
            if native_form and hasattr(native_form, 'BeginInvoke'):
                if hasattr(native_form, 'IsDisposed') and native_form.IsDisposed:
                    return
                browser = getattr(native_form, 'browser', None)
                wv = getattr(browser, 'webview', None)
                if wv:
                    global DotNetAction
                    if DotNetAction is None:
                        try:
                            from System import Action as SysAction
                            DotNetAction = SysAction
                        except Exception:
                            pass
                    if DotNetAction:
                        def _dispatch():
                            try:
                                if self.is_running and wv:
                                    wv.ExecuteScriptAsync(code)
                            except Exception:
                                pass
                        native_form.BeginInvoke(DotNetAction(_dispatch))
                        return
        except Exception:
            pass

        # Fallback for startup or non-WinForms edge cases (only if app is active)
        def _bg_eval():
            try:
                if self.window and self.is_running:
                    self.window.evaluate_js(code)
            except Exception:
                pass
        threading.Thread(target=_bg_eval, daemon=True).start()

    def sync_timer_to_js(self):
        stats = {
            "completed": self.completed_today,
            "minutes": self.total_focus_min
        }
        code = f"window.updateTimer({self.remaining_seconds}, {self.total_target_seconds}, '{self.state}', {self.current_session}, {self.target_sessions_val}, {json.dumps(stats)}, '{self.app_mode}');"
        self.eval_js(code)

    def set_app_mode(self, mode="study"):
        self.app_mode = mode # "study" (Học tập & Làm việc) or "eyecare" (Bảo vệ mắt)
        if mode == "eyecare":
            self.focus_duration = 50 * 60
            self.break_duration = 10 * 60
            self.distraction_monitor.barrier_enabled = False
        else:
            self.focus_duration = self.config.get("focus_minutes", 50) * 60
            self.break_duration = self.config.get("break_minutes", 10) * 60
            self.distraction_monitor.barrier_enabled = self.config.get("friction_barrier_enabled", True)
        self.reset_timer()

    def set_custom_timer(self, minutes, mode=None):
        m = max(1, int(minutes))
        if mode:
            self.app_mode = mode
        self._reflection_pending = False
        self.focus_duration = m * 60
        self.remaining_seconds = self.focus_duration
        self.total_target_seconds = self.focus_duration
        self.state = STATE_IDLE
        if self.app_mode == "eyecare":
            self.distraction_monitor.barrier_enabled = False
        else:
            self.distraction_monitor.barrier_enabled = self.config.get("friction_barrier_enabled", True)
        self.sync_timer_to_js()

    def sync_tasks_to_js(self):
        self.config["checklist_tasks"] = self.checklist.tasks
        save_config(self.config)
        code = f"window.updateTasks({json.dumps(self.checklist.tasks)});"
        self.eval_js(code)

    def sync_parking_to_js(self):
        self.config["brain_dump_notes"] = self.brain_dump.notes
        save_config(self.config)
        code = f"window.updateParking({json.dumps(self.brain_dump.notes)});"
        self.eval_js(code)

    def _timer_loop(self):
        """1-second precision countdown loop."""
        while self.is_running:
            time.sleep(1.0)
            if not self.is_running:
                break

            # Midnight date rollover check: seamlessly transition to new day without restart
            now_day = time.strftime("%Y-%m-%d")
            if now_day != self.current_date:
                self.current_date = now_day
                history = self.config.setdefault("daily_history", {})
                today_data = history.get(now_day, {})
                self.completed_today = today_data.get("sessions", 0)
                self.total_focus_min = today_data.get("minutes", 0)
                self.current_session = self.completed_today + 1
                self.config["completed_sessions"] = self.completed_today
                self.config["total_focus_minutes"] = self.total_focus_min
                save_config(self.config)
                if hasattr(self, 'distraction_monitor') and self.distraction_monitor:
                    self.distraction_monitor.on_date_changed(now_day)
                self.sync_timer_to_js()

            if self.state == STATE_FOCUS:
                self.remaining_seconds -= 1
                self._check_productivity_nudges()
                if self.remaining_seconds <= 0:
                    self._on_focus_finished()
                else:
                    self.sync_timer_to_js()

            elif self.state == STATE_BREAK:
                self.remaining_seconds -= 1
                if self.remaining_seconds <= 0:
                    self._on_break_finished(auto_start=False)
                else:
                    self.sync_timer_to_js()

    def _check_productivity_nudges(self):
        """Mid-session prompts and 20-20-20 eye care micro-blink."""
        halfway_sec = self.focus_duration // 2
        # Halfway nudge at 50%
        if self.config.get("halfway_nudge_enabled", True) and self.remaining_seconds == halfway_sec:
            self.eval_js("window.showToast('⏳ Đã đi được một nửa ca học! Giữ vững nhịp độ nhé.');")

        # Wrap-up nudge at 3 minutes remaining
        if self.config.get("wrapup_nudge_enabled", True) and self.remaining_seconds == 180:
            self.eval_js("window.showToast('🏁 Còn 3 phút! Hãy tổng kết nội dung và hoàn thiện mục tiêu.');")

        # 20-20-20 Eye Care Micro-Blink (every 20m while >5m remains before main break)
        if self.config.get("eye_care_enabled", True):
            elapsed = self.focus_duration - self.remaining_seconds
            if elapsed > 0 and elapsed % 1200 == 0 and self.remaining_seconds > 300:
                self.eval_js("window.startEyeMicroBreak && window.startEyeMicroBreak(20);")

    def _on_distraction_barrier(self, title, hwnd):
        """Called when DistractionMonitor catches an off-task window."""
        self.current_distracted_hwnd = hwnd
        if self.is_mini_mode:
            self.restore_full_window()
        last_key = getattr(self.distraction_monitor, "last_distracted_key", "") or ""
        is_flexible = any(p in last_key for p in ("youtube", "facebook", "reddit", "x_"))
        self.eval_js(f"window.showFrictionBarrier({json.dumps(title)}, {json.dumps(is_flexible)});")
        self.sync_parking_to_js()

        def _bring_to_front(native_form):
            w_hwnd = native_form.Handle.ToInt32() if hasattr(native_form, 'Handle') else 0
            if w_hwnd:
                if user32.IsIconic(w_hwnd):
                    user32.ShowWindow(w_hwnd, 9) # SW_RESTORE
                user32.SetForegroundWindow(w_hwnd)

        if not self._run_on_ui_thread(_bring_to_front):
            try:
                self.window.restore()
            except Exception:
                pass

    def start_timer(self):
        with self._state_lock:
            self._reflection_pending = False
            if self.state == STATE_IDLE:
                self.state = STATE_FOCUS
                self.remaining_seconds = self.focus_duration
                self.total_target_seconds = self.focus_duration
                play_focus_sound()
                self.distraction_monitor.start_monitoring()
                self.sync_timer_to_js()

            elif self.state == STATE_PAUSED:
                self.state = self.prev_state if self.prev_state != STATE_IDLE else STATE_FOCUS
                if self.state == STATE_FOCUS:
                    self.distraction_monitor.start_monitoring()
                self.sync_timer_to_js()

    def toggle_pause(self):
        with self._state_lock:
            if self._reflection_pending:
                return
            if self.state in (STATE_FOCUS, STATE_BREAK):
                self.prev_state = self.state
                self.state = STATE_PAUSED
                self.distraction_monitor.stop_monitoring()
                self.sync_timer_to_js()
            elif self.state == STATE_PAUSED:
                # Re-use start_timer logic outside lock or inline safely
                self.state = self.prev_state if self.prev_state != STATE_IDLE else STATE_FOCUS
                if self.state == STATE_FOCUS:
                    self.distraction_monitor.start_monitoring()
                self.sync_timer_to_js()

    def reset_timer(self):
        with self._state_lock:
            self._reflection_pending = False
            self.state = STATE_IDLE
            self.prev_state = STATE_IDLE
            self.remaining_seconds = self.focus_duration
            self.total_target_seconds = self.focus_duration
            self.distraction_monitor.stop_monitoring()
            self.distraction_monitor.reset_current_session()
            self.sync_timer_to_js()

    def skip_phase(self):
        with self._state_lock:
            if self._reflection_pending:
                # Already finished focus and awaiting reflection modal -> skip straight into break
                action = "enter_break"
            elif self.state == STATE_FOCUS:
                action = "finish_focus"
            elif self.state == STATE_BREAK:
                action = "finish_break"
            elif self.state == STATE_PAUSED:
                if getattr(self, 'prev_state', None) == STATE_BREAK:
                    action = "finish_break"
                else:
                    action = "finish_focus"
            else:
                return

        if action == "enter_break":
            self.enter_break_mode()
        elif action == "finish_focus":
            self._on_focus_finished()
        elif action == "finish_break":
            self._on_break_finished(auto_start=False)

    def _on_focus_finished(self):
        with self._state_lock:
            if self._reflection_pending or self.state not in (STATE_FOCUS, STATE_PAUSED):
                return
            self._reflection_pending = True
            self.state = STATE_PAUSED
            self.prev_state = STATE_IDLE

            # Calculate actual focus time (crediting ONLY actual time studied, not unspent planned duration)
            elapsed_seconds = max(0, self.total_target_seconds - max(0, self.remaining_seconds))
            actual_minutes = int(round(elapsed_seconds / 60))

            # Stats update
            if actual_minutes > 0:
                self.completed_today += 1
                self.total_focus_min += actual_minutes
                self.config["completed_sessions"] = self.completed_today
                self.config["total_focus_minutes"] = self.total_focus_min

                # Daily history recording
                today_key = time.strftime("%Y-%m-%d")
                history = self.config.setdefault("daily_history", {})
                if today_key not in history:
                    history[today_key] = {"sessions": 0, "minutes": 0}
                history[today_key]["sessions"] = self.completed_today
                history[today_key]["minutes"] = self.total_focus_min

                save_config(self.config)

        play_break_sound()
        self.distraction_monitor.stop_monitoring()

        # If in mini HUD mode, restore to full normal window size so the modal is fully visible and clickable
        if self.is_mini_mode:
            self.restore_full_window()

        self.sync_timer_to_js()

        # Purely evaluate THIS finished session (not mixed with earlier sessions of the day)
        purity_data = self.distraction_monitor.get_session_purity_stats(max(1, actual_minutes) if actual_minutes > 0 else 1)

        if actual_minutes > 0:
            goal_text = ""
            for t in self.checklist.tasks:
                if not t.get("done"):
                    goal_text = t.get("text", "")
                    break
            if not goal_text and self.checklist.tasks:
                goal_text = self.checklist.tasks[0].get("text", "")
            self.distraction_monitor.archive_completed_session(self.current_session, actual_minutes, goal_text)
        else:
            self.distraction_monitor.reset_current_session()

        # Show reflection/summary modal
        if self.app_mode == "eyecare":
            self.eval_js(f"window.showEyeCareFinishedModal({json.dumps(purity_data)});")
        else:
            self.eval_js(f"window.showReflectionModal({self.current_session}, {json.dumps(purity_data)});")

    def enter_break_mode(self):
        with self._state_lock:
            self._reflection_pending = False
            self.state = STATE_BREAK
            self.remaining_seconds = self.break_duration
            self.total_target_seconds = self.break_duration
        self.sync_timer_to_js()

        # Hardcore break enforcement: ALWAYS activate fullscreen topmost lockout
        if not self.is_fullscreen_overlay and self.window:
            try:
                self.is_fullscreen_overlay = True
                native_form = getattr(self.window, 'native', None)
                if native_form and not getattr(native_form, 'is_fullscreen', False):
                    self.window.toggle_fullscreen()
                elif not native_form:
                    self.window.toggle_fullscreen()
                if not self._run_on_ui_thread(lambda nf: setattr(nf, 'TopMost', True)):
                    self.window.on_top = True
            except Exception:
                pass

        # Specific enforcement actions
        if self.enforcement_mode in ("screen_off", "turnoff"):
            turn_off_monitor()
        elif self.enforcement_mode == "lock":
            lock_workstation()

        # Start active Break Watchdog Thread to prevent Alt+Tab, snapping, and enforce 100% strict discipline
        self._start_break_watchdog()

    def _start_break_watchdog(self):
        """Active Win32 Watchdog: Ensures other apps do not steal foreground during break without freezing message pump."""
        def _watchdog_loop():
            last_screen_off_time = time.time()
            HWND_TOPMOST = -1
            SWP_SHOWWINDOW = 0x0040
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001

            while self.is_running and self.state == STATE_BREAK:
                time.sleep(1.0)
                if not self.is_running or self.state != STATE_BREAK:
                    break

                try:
                    native_form = getattr(self.window, 'native', None)
                    if native_form and hasattr(native_form, 'Handle'):
                        w_hwnd = native_form.Handle.ToInt32()
                        if w_hwnd:
                            fg = user32.GetForegroundWindow()
                            if fg:
                                from ctypes import wintypes
                                fg_pid = wintypes.DWORD()
                                user32.GetWindowThreadProcessId(fg, ctypes.byref(fg_pid))
                                # Only if a DIFFERENT process stole foreground, bring break window back:
                                # NEVER call SetForegroundWindow when user clicks inside this process (WebView2 child)
                                if fg_pid.value and fg_pid.value != os.getpid():
                                    def _enforce_break_topmost(nf):
                                        hwnd_val = nf.Handle.ToInt32()
                                        user32.SetWindowPos(hwnd_val, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)
                                        user32.SetForegroundWindow(hwnd_val)
                                    self._run_on_ui_thread(_enforce_break_topmost)
                except Exception:
                    pass

                # If in screen_off mode, automatically turn off screen again after 15s if user wiggled mouse
                if self.enforcement_mode in ("screen_off", "turnoff"):
                    if time.time() - last_screen_off_time > 15:
                        last_screen_off_time = time.time()
                        turn_off_monitor()

        threading.Thread(target=_watchdog_loop, daemon=True).start()

    def _on_break_finished(self, auto_start=False):
        play_focus_sound()
        
        # Exit fullscreen overlay cleanly
        if self.is_fullscreen_overlay and self.window:
            try:
                self.is_fullscreen_overlay = False
                native_form = getattr(self.window, 'native', None)
                if native_form and getattr(native_form, 'is_fullscreen', False):
                    self.window.toggle_fullscreen()
                elif not native_form:
                    self.window.toggle_fullscreen()
                def _restore_after_break(nf):
                    nf.TopMost = False
                    nf.resize(520, 720, webview.window.FixPoint.NORTH | webview.window.FixPoint.WEST)
                if not self._run_on_ui_thread(_restore_after_break):
                    self.window.on_top = False
                    self.window.resize(520, 720)
            except Exception:
                pass

        if self.enforcement_mode in ("screen_off", "turnoff"):
            wake_up_monitor()

        # Advance session: each session is just 1 session
        self.current_session += 1
        self.remaining_seconds = self.focus_duration
        self.total_target_seconds = self.focus_duration

        # User request: Khi ấn skip ca nghỉ thì giờ học phải đứng yên chứ không phải kiểu đồng hồ tập trung nó tự chạy liền.
        should_auto_start = auto_start and self.config.get("auto_start_next_focus", False)
        if should_auto_start:
            self.state = STATE_FOCUS
            self.distraction_monitor.start_monitoring()
        else:
            self.state = STATE_IDLE
            self.distraction_monitor.stop_monitoring()

        self.sync_timer_to_js()
        self.eval_js("window.hideRestModal && window.hideRestModal();")

    def toggle_spotlight(self):
        def _run_spotlight():
            if self.spotlight is None:
                self.spotlight = FocusSpotlight(parent=None)
            self.spotlight.toggle()
        threading.Thread(target=_run_spotlight, daemon=True).start()

    def toggle_mini_mode(self):
        if not self.window:
            return
        with self._mini_mode_lock:
            now = time.monotonic()
            if now - self._last_mini_toggle_ts < 0.35:
                return
            self._last_mini_toggle_ts = now
            target = not self.is_mini_mode
            self.is_mini_mode = target
        self._apply_window_mode(target)

    def set_mini_mode(self, enabled=True):
        if not self.window:
            return
        target = bool(enabled)
        with self._mini_mode_lock:
            self.is_mini_mode = target
        self._apply_window_mode(target)

    def restore_full_window(self):
        """Restores window from mini HUD mode back to standard 520x720 normal size."""
        if not self.window:
            return
        with self._mini_mode_lock:
            self.is_mini_mode = False
        self._apply_window_mode(False)

    def _apply_window_mode(self, target_mini):
        """Atomically applies window size, TopMost, and CSS mini-mode on the WinForms UI thread."""
        def _apply_on_ui(native_form):
            with self._mini_mode_lock:
                is_mini = self.is_mini_mode

            browser = getattr(native_form, 'browser', None)
            wv = getattr(browser, 'webview', None)
            w_hwnd = native_form.Handle.ToInt32() if hasattr(native_form, 'Handle') else 0

            fp_nw = webview.window.FixPoint.NORTH | webview.window.FixPoint.WEST
            if is_mini:
                native_form.resize(365, 96, fp_nw)
                native_form.TopMost = True
                if wv:
                    wv.ExecuteScriptAsync("document.body.classList.add('mini-mode');")
            else:
                if w_hwnd and user32.IsIconic(w_hwnd):
                    user32.ShowWindow(w_hwnd, 9)  # SW_RESTORE
                native_form.resize(520, 720, fp_nw)
                native_form.TopMost = False
                if w_hwnd:
                    user32.SetForegroundWindow(w_hwnd)
                if wv:
                    wv.ExecuteScriptAsync("document.body.classList.remove('mini-mode');")

        if not self._run_on_ui_thread(_apply_on_ui):
            try:
                if target_mini:
                    self.window.resize(365, 96)
                    self.window.on_top = True
                    self.eval_js("document.body.classList.add('mini-mode');")
                else:
                    self.window.resize(520, 720)
                    self.window.on_top = False
                    self.eval_js("document.body.classList.remove('mini-mode');")
            except Exception:
                pass

    def start_in_app_update(self, download_url=None):
        if getattr(self, '_is_updating', False):
            return {"status": "busy", "message": "Đang trong quá trình cập nhật..."}
        self._is_updating = True
        threading.Thread(target=self._run_in_app_update, args=(download_url,), daemon=True).start()
        return {"status": "started"}

    def _run_in_app_update(self, download_url=None):
        try:
            target_url = download_url
            if not target_url or not str(target_url).startswith("http"):
                res = check_github_update()
                target_url = res.get("download_url") or res.get("release_url")

            if not target_url or not str(target_url).startswith("http"):
                raise ValueError("Không tìm thấy đường dẫn tải gói cập nhật.")

            temp_root = os.path.join(tempfile.gettempdir(), "focus_flow_inapp_update")
            if os.path.exists(temp_root):
                try:
                    shutil.rmtree(temp_root, ignore_errors=True)
                except Exception:
                    pass
            os.makedirs(temp_root, exist_ok=True)
            zip_path = os.path.join(temp_root, "update.zip")

            req = urllib.request.Request(target_url, headers={
                "User-Agent": f"FocusFlow-App/{APP_VERSION}",
                "Accept": "*/*"
            })

            with urllib.request.urlopen(req, timeout=30) as resp:
                content_len_hdr = resp.headers.get('Content-Length')
                total_size = int(content_len_hdr) if content_len_hdr and content_len_hdr.isdigit() else 0
                downloaded = 0
                chunk_size = 65536
                last_ui_update = 0

                with open(zip_path, 'wb') as f:
                    while True:
                        chunk = resp.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        now = time.time()
                        if total_size > 0:
                            pct = (downloaded / total_size) * 100.0
                        else:
                            pct = 50.0

                        if now - last_ui_update > 0.08:
                            last_ui_update = now
                            mb_down = downloaded / (1024 * 1024)
                            mb_total = total_size / (1024 * 1024) if total_size > 0 else 0
                            self.eval_js(f"window.onUpdateProgress && window.onUpdateProgress({pct:.1f}, {mb_down:.1f}, {mb_total:.1f}, 'Đang tải bản cập nhật...');")

            mb_down = downloaded / (1024 * 1024)
            self.eval_js(f"window.onUpdateProgress && window.onUpdateProgress(100.0, {mb_down:.1f}, {mb_down:.1f}, 'Đang giải nén tập tin...');")

            extract_dir = os.path.join(temp_root, "extracted")
            os.makedirs(extract_dir, exist_ok=True)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)

            payload_dir = extract_dir
            if not os.path.exists(os.path.join(payload_dir, "Focus Flow.exe")):
                for root, dirs, files in os.walk(extract_dir):
                    if "Focus Flow.exe" in files:
                        payload_dir = root
                        break

            if getattr(sys, 'frozen', False):
                app_dir = os.path.dirname(sys.executable)
                exe_name = os.path.basename(sys.executable)
            else:
                app_dir = os.path.dirname(os.path.abspath(__file__))
                exe_name = "Focus Flow.exe"

            current_pid = os.getpid()
            bat_path = os.path.join(tempfile.gettempdir(), f"focus_flow_updater_{current_pid}.bat")

            bat_content = f"""@echo off
chcp 65001 >nul
title Cập nhật Focus Flow...

:wait_loop
powershell -NoProfile -Command "if (Get-Process -Id {current_pid} -ErrorAction SilentlyContinue) {{ exit 1 }} else {{ exit 0 }}"
if %ERRORLEVEL% EQU 1 (
    timeout /t 1 /nobreak >nul
    goto wait_loop
)
timeout /t 1 /nobreak >nul

set "BACKUP_DIR=%TEMP%\\focus_flow_backup_{current_pid}"
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"
if exist "{app_dir}\\config.json" copy /y "{app_dir}\\config.json" "%BACKUP_DIR%\\" >nul

xcopy /s /e /y /q "{payload_dir}\\*" "{app_dir}\\" >nul

if exist "%BACKUP_DIR%\\config.json" copy /y "%BACKUP_DIR%\\config.json" "{app_dir}\\" >nul
rmdir /s /q "%BACKUP_DIR%" 2>nul

powershell -NoProfile -Command "Get-ChildItem -Path '{app_dir}' -Recurse | Unblock-File -ErrorAction SilentlyContinue" 2>nul

start "" "{app_dir}\\{exe_name}"

timeout /t 2 /nobreak >nul
rmdir /s /q "{temp_root}" 2>nul
(goto) 2>nul & del "%~f0"
"""
            with open(bat_path, "w", encoding="utf-8") as f:
                f.write(bat_content)

            self.eval_js("window.onUpdateProgress && window.onUpdateProgress(100.0, 0, 0, 'Cập nhật thành công! Đang khởi động lại...');")
            time.sleep(0.7)

            creation_flags = 0
            if hasattr(subprocess, 'CREATE_NO_WINDOW'):
                creation_flags |= subprocess.CREATE_NO_WINDOW
            if hasattr(subprocess, 'DETACHED_PROCESS'):
                creation_flags |= subprocess.DETACHED_PROCESS

            subprocess.Popen(
                ["cmd.exe", "/c", bat_path],
                creationflags=creation_flags,
                close_fds=True
            )

            try:
                self.is_running = False
                if os.path.exists(PID_FILE):
                    os.remove(PID_FILE)
            except Exception:
                pass

            os._exit(0)

        except Exception as e:
            self._is_updating = False
            err_msg = str(e).replace("'", "\\'").replace('"', '\\"').replace('\n', ' ')
            self.eval_js(f"window.onUpdateError && window.onUpdateError('{err_msg}');")

    def on_close(self):
        self.is_running = False
        try:
            self.distraction_monitor.stop_monitoring()
        except Exception:
            pass
        if os.path.exists(PID_FILE):
            try:
                os.remove(PID_FILE)
            except Exception:
                pass
        try:
            if self.window:
                self.window.destroy()
        except Exception:
            pass
        sys.exit(0)


class Api:
    """JS Bridge Interface exposed to Webview (window.pywebview.api)"""
    def __init__(self, app: PomodoroApp):
        self._app = app

    def start_timer(self):
        self._app.start_timer()

    def toggle_pause(self):
        self._app.toggle_pause()

    def reset_timer(self):
        self._app.reset_timer()

    def skip_phase(self):
        self._app.skip_phase()

    def skip_session(self):
        self._app.skip_phase()

    def add_task(self, text):
        self._app.checklist.add_task(text)
        self._app.sync_tasks_to_js()

    def delete_task(self, idx):
        self._app.checklist.delete_task(int(idx))
        self._app.sync_tasks_to_js()

    def update_task_text(self, idx, text):
        self._app.checklist.update_task_text(int(idx), text)
        self._app.sync_tasks_to_js()

    def toggle_task(self, idx):
        self._app.checklist.toggle_task(int(idx))
        self._app.sync_tasks_to_js()

    def clear_all_tasks(self):
        self._app.checklist.clear_all()
        self._app.sync_tasks_to_js()

    def load_tasks_preset(self, preset_name):
        self._app.checklist.load_preset(preset_name)
        self._app.sync_tasks_to_js()

    def save_quick_dump(self, text):
        self._app.brain_dump.add_note(text, note_type="manual")
        self._app.sync_parking_to_js()

    def toggle_parking_resolved(self, idx):
        self._app.brain_dump.toggle_resolved(int(idx))
        self._app.sync_parking_to_js()

    def delete_parking_note(self, idx):
        self._app.brain_dump.delete_note(int(idx))
        self._app.sync_parking_to_js()

    def clear_parking_lot(self):
        self._app.brain_dump.clear()
        self._app.sync_parking_to_js()

    def clear_resolved_parking(self):
        self._app.brain_dump.clear_resolved()
        self._app.sync_parking_to_js()

    def set_app_mode(self, mode):
        self._app.set_app_mode(mode)
        return "ok"

    def set_youtube_fb_study(self, enabled):
        self._app.distraction_monitor.set_youtube_fb_study_mode(bool(enabled))
        return "ok"

    def reclassify_usage_item(self, key, new_cat, scope="daily", session_num=None):
        self._app.distraction_monitor.reclassify_item(key, new_cat, scope=scope, session_num=session_num)
        return "ok"

    def friction_allow_as_study(self, mode="video"):
        if mode == "session":
            self._app.distraction_monitor.allow_session_youtube_study()
        else:
            self._app.distraction_monitor.allow_current_video_as_study()
        if self._app.current_distracted_hwnd:
            try:
                user32.SetForegroundWindow(self._app.current_distracted_hwnd)
            except Exception:
                pass
        self._app.eval_js("window.hideFrictionBarrier();")

    def set_custom_study_keywords(self, keywords_str):
        self._app.distraction_monitor.set_custom_study_keywords(keywords_str)
        kw_list = list(self._app.distraction_monitor.custom_study_keywords)
        self._app.config["custom_study_keywords"] = kw_list
        save_config(self._app.config)
        return kw_list

    def set_target_sessions(self, target):
        self._app.target_sessions_val = int(target)
        self._app.config["target_sessions"] = self._app.target_sessions_val
        save_config(self._app.config)
        self._app.sync_timer_to_js()

    def get_purity_report(self):
        total_mins = max(1, self._app.focus_duration // 60)
        return self._app.distraction_monitor.get_purity_stats(total_mins)

    def get_analytics_bundle(self):
        total_mins = max(1, self._app.focus_duration // 60)
        is_active = (self._app.state == STATE_FOCUS)
        return self._app.distraction_monitor.get_analytics_bundle(
            session_num=self._app.current_session,
            is_focus_active=is_active,
            total_focus_minutes=total_mins
        )

    def set_custom_timer(self, minutes, mode=None):
        self._app.set_custom_timer(int(minutes), mode)
        return "ok"

    def apply_preset(self, focus_min, break_min):
        f_min = max(1, int(focus_min))
        b_min = max(1, int(break_min))
        self._app.focus_duration = f_min * 60
        self._app.break_duration = b_min * 60
        self._app.config["focus_minutes"] = f_min
        self._app.config["break_minutes"] = b_min
        save_config(self._app.config)
        # When setting/applying a study cycle, update timer and stand ready at IDLE if not currently on a break
        if self._app.state != STATE_BREAK:
            self._app._reflection_pending = False
            self._app.state = STATE_IDLE
            self._app.remaining_seconds = self._app.focus_duration
            self._app.total_target_seconds = self._app.focus_duration
            self._app.distraction_monitor.stop_monitoring()
        self._app.sync_timer_to_js()

    def set_enforcement_mode(self, mode):
        normalized = "screen_off" if mode in ("screen_off", "turnoff") else mode
        self._app.enforcement_mode = normalized
        self._app.config["enforcement_mode"] = normalized
        save_config(self._app.config)

    def set_feature_toggle(self, key, is_enabled):
        val = bool(is_enabled)
        self._app.config[key] = val
        save_config(self._app.config)
        if key == "friction_barrier_enabled":
            self._app.distraction_monitor.barrier_enabled = val

    def toggle_feature_config(self, key, is_enabled):
        return self.set_feature_toggle(key, is_enabled)

    def toggle_spotlight(self):
        self._app.toggle_spotlight()

    def toggle_mini_mode(self):
        self._app.toggle_mini_mode()

    def restore_full_window(self):
        self._app.restore_full_window()

    def minimize_app(self):
        if self._app.window:
            self._app.window.minimize()

    def close_app(self):
        self._app.on_close()

    def start_next_session_early(self):
        self._app._on_break_finished(auto_start=False)

    def submit_reflection(self, rating, note_text=""):
        self._app.enter_break_mode()

    def enter_break_mode(self):
        self._app.enter_break_mode()
        return "ok"

    def extend_eyecare_work(self, minutes=5):
        self._app._reflection_pending = False
        self._app.state = STATE_FOCUS
        self._app.remaining_seconds = int(minutes) * 60
        self._app.total_target_seconds = int(minutes) * 60
        self._app.sync_timer_to_js()
        return "ok"

    def add_break_time(self, minutes=5):
        """Adds extra minutes to the current break."""
        if self._app.state == STATE_BREAK:
            self._app.remaining_seconds += int(minutes) * 60
            self._app.total_target_seconds += int(minutes) * 60
            self._app.sync_timer_to_js()
            return "ok"
        return "not_in_break"

    def friction_back_to_study(self):
        if self._app.current_distracted_hwnd:
            try:
                user32.ShowWindow(self._app.current_distracted_hwnd, 6) # SW_MINIMIZE
            except Exception:
                pass
        self._app.eval_js("window.hideFrictionBarrier();")
        # User requested: lúc ấn quay lại bàn học thì tôi muốn nó ở giao diện của mini hud chứ k phải giao diện to.
        self._app.set_mini_mode(True)

    def friction_allow_distraction(self):
        if self._app.current_distracted_hwnd:
            # User requested: cỡ 1-2 phút sau sẽ hiện lại chứ k cho phép mở các trang giải trí luôn.
            # Snooze barrier for 120 seconds (2 minutes), then barrier triggers again!
            self._app.distraction_monitor.snooze_hwnd(self._app.current_distracted_hwnd, duration_seconds=120)
            try:
                user32.SetForegroundWindow(self._app.current_distracted_hwnd)
            except Exception:
                pass
        self._app.eval_js("window.hideFrictionBarrier();")
        # Switch to mini HUD so Focus Flow doesn't obscure the user's screen during the 2 minutes
        self._app.set_mini_mode(True)

    def set_sound_volume(self, vol):
        v = max(0, min(100, int(vol)))
        self._app.config["sound_volume"] = v
        save_config(self._app.config)
        set_sound_volume(v)
        return "ok"

    def test_sound(self):
        play_focus_sound()
        return "ok"

    def get_daily_history(self):
        return self._app.config.get("daily_history", {})

    def check_for_updates(self):
        return check_github_update()

    def start_in_app_update(self, download_url=None):
        return self._app.start_in_app_update(download_url)

    def open_external_url(self, url):
        if url and (url.startswith("https://") or url.startswith("http://")):
            try:
                webbrowser.open(url)
                return "ok"
            except Exception as e:
                return str(e)
        return "invalid_url"


def main():
    app = PomodoroApp()
    api = Api(app)

    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", "index.html")

    window = webview.create_window(
        title="Focus Flow • Pomodoro 50/10 Pro",
        url=html_path,
        js_api=api,
        width=520,
        height=720,
        resizable=True,
        min_size=(240, 75),
        frameless=True,
        easy_drag=True,
        shadow=True,
        background_color='#090a0f',
        text_select=True
    )

    app.attach_window(window)
    webview.start(debug=False)


if __name__ == "__main__":
    main()
