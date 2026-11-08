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
        self.current_session = 1
        self.completed_today = self.config.get("completed_sessions", 0)
        self.total_focus_min = self.config.get("total_focus_minutes", 0)

        self.is_running = True
        self.is_mini_mode = False
        self.is_fullscreen_overlay = False
        self.current_distracted_hwnd = None
        self.app_mode = "study" # "study" (Tập trung học) or "eyecare" (Nghỉ mắt 50/10)
        self.window = None

        # Productivity Modules
        self.checklist = MicroChecklist()
        self.brain_dump = BrainDumpManager()
        self.spotlight = None

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

    def _on_window_closed(self):
        self.on_close()

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
        self.app_mode = mode # "study" (Tập trung học) or "eyecare" (Nghỉ mắt 50/10)
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
        self.focus_duration = m * 60
        self.remaining_seconds = self.focus_duration
        self.total_target_seconds = self.focus_duration
        self.state = STATE_IDLE
        if self.app_mode == "eyecare":
            self.distraction_monitor.barrier_enabled = False
        else:
            self.distraction_monitor.barrier_enabled = self.config.get("friction_barrier_enabled", True)
        self.distraction_monitor.reset_stats()
        self.sync_timer_to_js()

    def sync_tasks_to_js(self):
        code = f"window.updateTasks({json.dumps(self.checklist.tasks)});"
        self.eval_js(code)

    def sync_parking_to_js(self):
        code = f"window.updateParking({json.dumps(self.brain_dump.notes)});"
        self.eval_js(code)

    def _timer_loop(self):
        """1-second precision countdown loop."""
        while self.is_running:
            time.sleep(1.0)
            if not self.is_running:
                break

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
                    self._on_break_finished()
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

        # 20-20-20 Eye Care Micro-Blink (e.g. at 20m and 40m marks)
        if self.config.get("eye_care_enabled", True):
            elapsed = self.focus_duration - self.remaining_seconds
            if elapsed in (1200, 2400):
                self.eval_js("window.showToast('👀 Nhắc nhở 20-20-20: Đảo mắt nhìn xa 6 mét trong 20 giây để giảm căng thẳng cho mắt!');")

    def _on_distraction_barrier(self, title, hwnd):
        """Called when DistractionMonitor catches an off-task window."""
        self.current_distracted_hwnd = hwnd
        if self.is_mini_mode:
            self.restore_full_window()
        self.eval_js(f"window.showFrictionBarrier({json.dumps(title)});")
        self.sync_parking_to_js()
        try:
            native_form = getattr(self.window, 'native', None)
            if native_form and hasattr(native_form, 'Handle'):
                w_hwnd = native_form.Handle.ToInt32()
                if w_hwnd:
                    user32.ShowWindow(w_hwnd, 9) # SW_RESTORE (non-blocking)
                    user32.SetForegroundWindow(w_hwnd)
                    return
            self.window.restore()
        except Exception:
            pass

    def start_timer(self):
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
        if self.state in (STATE_FOCUS, STATE_BREAK):
            self.prev_state = self.state
            self.state = STATE_PAUSED
            self.distraction_monitor.stop_monitoring()
            self.sync_timer_to_js()
        elif self.state == STATE_PAUSED:
            self.start_timer()

    def reset_timer(self):
        self.state = STATE_IDLE
        self.remaining_seconds = self.focus_duration
        self.total_target_seconds = self.focus_duration
        self.distraction_monitor.stop_monitoring()
        self.sync_timer_to_js()

    def skip_phase(self):
        if self.state == STATE_FOCUS:
            self._on_focus_finished()
        elif self.state == STATE_BREAK:
            self._on_break_finished()
        elif self.state == STATE_PAUSED:
            if getattr(self, 'prev_state', None) == STATE_BREAK:
                self._on_break_finished()
            else:
                self._on_focus_finished()

    def _on_focus_finished(self):
        play_break_sound()
        self.distraction_monitor.stop_monitoring()
        self.state = STATE_PAUSED

        # If in mini HUD mode, restore to full normal window size so the modal is fully visible and clickable
        if self.is_mini_mode:
            self.restore_full_window()

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
            history[today_key]["sessions"] = history[today_key].get("sessions", 0) + 1
            history[today_key]["minutes"] = history[today_key].get("minutes", 0) + actual_minutes

            save_config(self.config)

        self.sync_timer_to_js()

        purity_data = self.distraction_monitor.get_purity_stats(max(1, actual_minutes) if actual_minutes > 0 else 1)

        # Show reflection/summary modal
        if self.app_mode == "eyecare":
            self.eval_js(f"window.showEyeCareFinishedModal({json.dumps(purity_data)});")
        else:
            self.eval_js(f"window.showReflectionModal({self.current_session}, {json.dumps(purity_data)});")

    def enter_break_mode(self):
        self.state = STATE_BREAK
        self.remaining_seconds = self.break_duration
        self.total_target_seconds = self.break_duration
        self.sync_timer_to_js()

        # Hardcore break enforcement: ALWAYS activate fullscreen topmost lockout
        if not self.is_fullscreen_overlay and self.window:
            try:
                self.is_fullscreen_overlay = True
                self.window.toggle_fullscreen()
                self.window.on_top = True
            except Exception:
                pass

        # Specific enforcement actions
        if self.enforcement_mode in ("screen_off", "turnoff"):
            turn_off_monitor()
        elif self.enforcement_mode == "lock":
            lock_workstation()

        # Start active Break Watchdog Thread to prevent Alt+Tab and enforce 100% strict discipline
        self._start_break_watchdog()

    def _start_break_watchdog(self):
        """Active Win32 Watchdog: Keeps the break overlay topmost and snaps back if user tries to switch windows."""
        def _watchdog_loop():
            last_screen_off_time = time.time()
            while self.is_running and self.state == STATE_BREAK:
                time.sleep(0.4)
                if not self.is_running or self.state != STATE_BREAK:
                    break

                try:
                    native_form = getattr(self.window, 'native', None)
                    if native_form and hasattr(native_form, 'Handle'):
                        w_hwnd = native_form.Handle.ToInt32()
                        if w_hwnd:
                            fg = user32.GetForegroundWindow()
                            if fg != w_hwnd:
                                HWND_TOPMOST = -1
                                SWP_NOMOVE = 0x0002
                                SWP_NOSIZE = 0x0001
                                SWP_SHOWWINDOW = 0x0040
                                user32.SetWindowPos(w_hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)
                                user32.BringWindowToTop(w_hwnd)
                                user32.SetForegroundWindow(w_hwnd)
                except Exception:
                    pass

                # If in screen_off mode, automatically turn off screen again after 15s if user wiggled mouse
                if self.enforcement_mode in ("screen_off", "turnoff"):
                    if time.time() - last_screen_off_time > 15:
                        last_screen_off_time = time.time()
                        turn_off_monitor()

        threading.Thread(target=_watchdog_loop, daemon=True).start()

    def _on_break_finished(self):
        play_focus_sound()
        
        # Exit fullscreen overlay if active
        if self.is_fullscreen_overlay and self.window:
            try:
                self.is_fullscreen_overlay = False
                self.window.toggle_fullscreen()
                self.window.on_top = False
                self.window.resize(520, 720)
            except Exception:
                pass

        if self.enforcement_mode in ("screen_off", "turnoff"):
            wake_up_monitor()

        # Advance session
        if self.target_sessions_val == 0 or self.current_session < self.target_sessions_val:
            self.current_session += 1
            self.state = STATE_FOCUS
            self.remaining_seconds = self.focus_duration
            self.total_target_seconds = self.focus_duration
            self.distraction_monitor.start_monitoring()
            self.sync_timer_to_js()
        else:
            self.state = STATE_IDLE
            self.current_session = 1
            self.remaining_seconds = self.focus_duration
            self.total_target_seconds = self.focus_duration
            self.sync_timer_to_js()
            self.eval_js("window.showToast('🏆 Chúc mừng! Bạn đã hoàn thành toàn bộ mục tiêu ca học hôm nay!');")

    def toggle_spotlight(self):
        def _run_spotlight():
            if self.spotlight is None:
                self.spotlight = FocusSpotlight(parent=None)
            self.spotlight.toggle()
        threading.Thread(target=_run_spotlight, daemon=True).start()

    def toggle_mini_mode(self):
        if not self.window:
            return
        if not self.is_mini_mode:
            self.is_mini_mode = True
            self.window.resize(365, 96)
            self.window.on_top = True
            self.eval_js("document.body.classList.add('mini-mode');")
        else:
            self.restore_full_window()

    def restore_full_window(self):
        """Restores window from mini HUD mode back to standard 520x720 normal size."""
        if not self.window:
            return
        self.is_mini_mode = False
        try:
            self.window.resize(520, 720)
            self.window.on_top = False
            self.eval_js("document.body.classList.remove('mini-mode');")
            native_form = getattr(self.window, 'native', None)
            if native_form and hasattr(native_form, 'Handle'):
                w_hwnd = native_form.Handle.ToInt32()
                if w_hwnd:
                    user32.ShowWindow(w_hwnd, 9) # SW_RESTORE
                    user32.SetForegroundWindow(w_hwnd)
        except Exception:
            pass

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

    def reclassify_usage_item(self, key, new_cat):
        self._app.distraction_monitor.reclassify_item(key, new_cat)
        return "ok"

    def friction_allow_as_study(self):
        if self._app.current_distracted_hwnd:
            self._app.distraction_monitor.allowed_hwnds.add(self._app.current_distracted_hwnd)
            if self._app.distraction_monitor.usage_records:
                last_key = list(self._app.distraction_monitor.usage_records.keys())[-1]
                self._app.distraction_monitor.reclassify_item(last_key, "online_study")
        self._app.eval_js("window.hideFrictionBarrier();")

    def set_target_sessions(self, target):
        self._app.target_sessions_val = int(target)
        self._app.config["target_sessions"] = self._app.target_sessions_val
        save_config(self._app.config)
        self._app.sync_timer_to_js()

    def get_purity_report(self):
        total_mins = max(1, self._app.focus_duration // 60)
        return self._app.distraction_monitor.get_purity_stats(total_mins)

    def set_custom_timer(self, minutes, mode=None):
        self._app.set_custom_timer(int(minutes), mode)
        return "ok"

    def apply_preset(self, focus_min, break_min):
        f_min = int(focus_min)
        b_min = int(break_min)
        self._app.focus_duration = f_min * 60
        self._app.break_duration = b_min * 60
        self._app.config["focus_minutes"] = f_min
        self._app.config["break_minutes"] = b_min
        save_config(self._app.config)
        if self._app.state == STATE_IDLE:
            self._app.remaining_seconds = self._app.focus_duration
            self._app.total_target_seconds = self._app.focus_duration
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
        self._app._on_break_finished()

    def submit_reflection(self, rating, note_text=""):
        self._app.enter_break_mode()

    def enter_break_mode(self):
        self._app.enter_break_mode()
        return "ok"

    def extend_eyecare_work(self, minutes=5):
        self._app.state = STATE_FOCUS
        self._app.remaining_seconds = int(minutes) * 60
        self._app.total_target_seconds = int(minutes) * 60
        self._app.sync_timer_to_js()
        return "ok"

    def friction_back_to_study(self):
        if self._app.current_distracted_hwnd:
            try:
                user32.ShowWindow(self._app.current_distracted_hwnd, 6) # SW_MINIMIZE
            except Exception:
                pass
        self._app.eval_js("window.hideFrictionBarrier();")
        if self._app.window:
            try:
                self._app.window.restore()
            except Exception:
                pass

    def friction_allow_distraction(self):
        if self._app.current_distracted_hwnd:
            self._app.distraction_monitor.allowed_hwnds.add(self._app.current_distracted_hwnd)
        self._app.eval_js("window.hideFrictionBarrier();")

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
