import time
import ctypes
import threading

def enable_dark_titlebar(window):
    try:
        window.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        if not hwnd:
            hwnd = window.winfo_id()
        val = ctypes.c_int(1)
        res = ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(val), ctypes.sizeof(val))
        if res != 0:
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 19, ctypes.byref(val), ctypes.sizeof(val))
    except Exception:
        pass


class MicroChecklist:
    """Manages dynamic user tasks per session, completion states, active focus index, and spent time."""

    def __init__(self, initial_tasks=None, active_index=0):
        self._lock = threading.RLock()
        self.current_tasks = [self._normalize_task(t) for t in (initial_tasks or []) if isinstance(t, dict) and str(t.get("text", "")).strip()]
        self.session_history = {}  # session_num -> list of tasks
        self.session_task_times = {}  # task_text -> seconds spent in current active session
        self.active_index = 0
        self._ensure_valid_active_index(preferred=active_index)

    @staticmethod
    def _normalize_task(item):
        return {
            "text": str(item.get("text", "")).strip(),
            "done": bool(item.get("done", False)),
            "spent_seconds": max(0, int(item.get("spent_seconds", 0) or 0)),
        }

    def _ensure_valid_active_index(self, preferred=None):
        n = len(self.current_tasks)
        if n == 0:
            self.active_index = 0
            return
        idx = self.active_index if preferred is None else int(preferred or 0)
        if 0 <= idx < n and not self.current_tasks[idx]["done"]:
            self.active_index = idx
            return
        first_unfinished = next((i for i, t in enumerate(self.current_tasks) if not t["done"]), None)
        if first_unfinished is not None:
            self.active_index = first_unfinished
        else:
            self.active_index = max(0, min(n - 1, idx))

    @property
    def tasks(self):
        with self._lock:
            return [dict(t) for t in self.current_tasks]

    def get_tasks(self):
        return self.tasks

    def add_task(self, text):
        clean = str(text or "").strip()
        if not clean:
            return False
        with self._lock:
            had_unfinished = any(not t["done"] for t in self.current_tasks)
            self.current_tasks.append({"text": clean, "done": False, "spent_seconds": 0})
            if not had_unfinished:
                self.active_index = len(self.current_tasks) - 1
            return True

    def delete_task(self, index):
        with self._lock:
            if 0 <= index < len(self.current_tasks):
                del self.current_tasks[index]
                if index < self.active_index:
                    self.active_index -= 1
                self._ensure_valid_active_index()
                return True
            return False

    def update_task_text(self, index, text):
        with self._lock:
            if 0 <= index < len(self.current_tasks):
                clean = str(text or "").strip()
                if clean:
                    old_text = self.current_tasks[index]["text"]
                    self.current_tasks[index]["text"] = clean
                    if old_text != clean and old_text in self.session_task_times:
                        prev_sec = self.session_task_times.pop(old_text)
                        self.session_task_times[clean] = self.session_task_times.get(clean, 0) + prev_sec

    def set_task_done(self, index, done):
        with self._lock:
            if 0 <= index < len(self.current_tasks):
                new_done = bool(done)
                self.current_tasks[index]["done"] = new_done
                if new_done and index == self.active_index:
                    self._ensure_valid_active_index()
                elif not new_done and (
                    not (0 <= self.active_index < len(self.current_tasks))
                    or self.current_tasks[self.active_index]["done"]
                ):
                    self.active_index = index
                return new_done
            return False

    def toggle_task(self, index):
        with self._lock:
            if 0 <= index < len(self.current_tasks):
                new_done = not self.current_tasks[index]["done"]
                return self.set_task_done(index, new_done)
            return False

    def set_active_task(self, index):
        with self._lock:
            idx = int(index)
            if 0 <= idx < len(self.current_tasks):
                self.active_index = idx
                return True
            return False

    def tick_active_task(self, seconds=1):
        """Adds `seconds` to the current unfinished active focus task and session accumulator."""
        with self._lock:
            if not self.current_tasks:
                return None
            self._ensure_valid_active_index()
            if not (0 <= self.active_index < len(self.current_tasks)):
                return None
            task = self.current_tasks[self.active_index]
            if task["done"]:
                return None
            inc = max(1, int(seconds))
            task["spent_seconds"] = int(task.get("spent_seconds", 0)) + inc
            t_text = task["text"]
            self.session_task_times[t_text] = int(self.session_task_times.get(t_text, 0)) + inc
            return {
                "active_index": self.active_index,
                "times": [t["spent_seconds"] for t in self.current_tasks],
            }

    def get_session_tasks_breakdown(self):
        """Returns sorted list of goal time entries tracked in the current session."""
        with self._lock:
            done_map = {t["text"]: bool(t.get("done", False)) for t in self.current_tasks}
            items = []
            for text, sec in self.session_task_times.items():
                if sec > 0 and text:
                    items.append({
                        "text": text,
                        "seconds": int(sec),
                        "done": done_map.get(text, False),
                    })
            items.sort(key=lambda x: x["seconds"], reverse=True)
            return items

    def reset_session_times(self):
        with self._lock:
            self.session_task_times = {}

    def clear_all(self):
        with self._lock:
            self.current_tasks = []
            self.active_index = 0

    def load_preset(self, preset_name):
        with self._lock:
            if preset_name == "study":
                self.current_tasks = [
                    {"text": "Đọc lý thuyết & nắm ý chính bài học", "done": False, "spent_seconds": 0},
                    {"text": "Giải các bài tập mẫu & ví dụ minh họa", "done": False, "spent_seconds": 0},
                    {"text": "Tự làm bài tự luyện & soát lại lỗi", "done": False, "spent_seconds": 0},
                ]
            elif preset_name == "dev":
                self.current_tasks = [
                    {"text": "Phân tích yêu cầu & thiết kế logic", "done": False, "spent_seconds": 0},
                    {"text": "Code tính năng trọng tâm & unit test", "done": False, "spent_seconds": 0},
                    {"text": "Refactor mã nguồn & kiểm tra edge cases", "done": False, "spent_seconds": 0},
                ]
            elif preset_name == "writing":
                self.current_tasks = [
                    {"text": "Lập dàn ý chi tiết luận điểm", "done": False, "spent_seconds": 0},
                    {"text": "Viết bản thảo liên tục không xóa", "done": False, "spent_seconds": 0},
                    {"text": "Biên tập câu từ & hoàn thiện văn bản", "done": False, "spent_seconds": 0},
                ]
            elif preset_name == "empty":
                self.current_tasks = []
            self.active_index = 0
            return self.tasks

    def get_progress(self):
        with self._lock:
            total = len(self.current_tasks)
            if total == 0:
                return 0, 0
            done = sum(1 for t in self.current_tasks if t["done"])
            return done, total

    def archive_current_session(self, session_num):
        with self._lock:
            self.session_history[session_num] = [dict(t) for t in self.current_tasks]

    def reset_for_new_session(self, session_num):
        with self._lock:
            if not self.current_tasks:
                self.current_tasks = [
                    {"text": f"Nhiệm vụ 1 của Ca #{session_num}", "done": False, "spent_seconds": 0},
                    {"text": f"Nhiệm vụ 2 của Ca #{session_num}", "done": False, "spent_seconds": 0},
                ]
            else:
                for t in self.current_tasks:
                    t["done"] = False
            self._ensure_valid_active_index()


class BrainDumpManager:
    """Manages the Distraction Parking Lot: captures distracting thoughts and logged distraction events."""
    def __init__(self, initial_notes=None):
        # list of {"time": str, "text": str, "resolved": bool, "type": "manual" | "detected"}
        self.notes = list(initial_notes) if initial_notes else []

    def add_note(self, text, note_type="manual"):
        clean = text.strip()
        if clean:
            self.notes.insert(0, {
                "time": time.strftime("%H:%M"),
                "text": clean,
                "resolved": False,
                "type": note_type
            })
            return True
        return False

    def delete_note(self, index):
        if 0 <= index < len(self.notes):
            del self.notes[index]
            return True
        return False

    def toggle_resolved(self, index):
        if 0 <= index < len(self.notes):
            self.notes[index]["resolved"] = not self.notes[index]["resolved"]
            return self.notes[index]["resolved"]
        return False

    def get_notes(self):
        return self.notes

    def clear_all(self):
        self.notes = []

    def clear_resolved(self):
        self.notes = [n for n in self.notes if not n.get("resolved", False)]

    def clear(self):
        self.notes = []

    def get_stats(self):
        total = len(self.notes)
        resolved = sum(1 for n in self.notes if n.get("resolved", False))
        detected = sum(1 for n in self.notes if n.get("type") == "detected")
        return {
            "total": total,
            "resolved": resolved,
            "unresolved": total - resolved,
            "detected": detected
        }

