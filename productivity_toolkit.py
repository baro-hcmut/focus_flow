import time
import ctypes

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
    """Manages dynamic user tasks per session, adding/removing/editing, and completion states."""
    def __init__(self):
        self.current_tasks = []
        self.session_history = {} # session_num -> list of tasks

    @property
    def tasks(self):
        return self.current_tasks

    def get_tasks(self):
        return self.current_tasks

    def add_task(self, text):
        clean = text.strip()
        if clean:
            self.current_tasks.append({"text": clean, "done": False})
            return True
        return False

    def delete_task(self, index):
        if 0 <= index < len(self.current_tasks):
            del self.current_tasks[index]
            return True
        return False

    def update_task_text(self, index, text):
        if 0 <= index < len(self.current_tasks):
            clean = text.strip()
            if clean:
                self.current_tasks[index]["text"] = clean

    def set_task_done(self, index, done):
        if 0 <= index < len(self.current_tasks):
            self.current_tasks[index]["done"] = bool(done)
            return self.current_tasks[index]["done"]
        return False

    def toggle_task(self, index):
        if 0 <= index < len(self.current_tasks):
            self.current_tasks[index]["done"] = not self.current_tasks[index]["done"]
            return self.current_tasks[index]["done"]
        return False

    def clear_all(self):
        self.current_tasks = []

    def load_preset(self, preset_name):
        if preset_name == "study":
            self.current_tasks = [
                {"text": "Đọc lý thuyết & nắm ý chính bài học", "done": False},
                {"text": "Giải các bài tập mẫu & ví dụ minh họa", "done": False},
                {"text": "Tự làm bài tự luyện & soát lại lỗi", "done": False}
            ]
        elif preset_name == "dev":
            self.current_tasks = [
                {"text": "Phân tích yêu cầu & thiết kế logic", "done": False},
                {"text": "Code tính năng trọng tâm & unit test", "done": False},
                {"text": "Refactor mã nguồn & kiểm tra edge cases", "done": False}
            ]
        elif preset_name == "writing":
            self.current_tasks = [
                {"text": "Lập dàn ý chi tiết luận điểm", "done": False},
                {"text": "Viết bản thảo liên tục không xóa", "done": False},
                {"text": "Biên tập câu từ & hoàn thiện văn bản", "done": False}
            ]
        elif preset_name == "empty":
            self.current_tasks = []
        return self.current_tasks

    def get_progress(self):
        total = len(self.current_tasks)
        if total == 0:
            return 0, 0
        done = sum(1 for t in self.current_tasks if t["done"])
        return done, total

    def archive_current_session(self, session_num):
        self.session_history[session_num] = [dict(t) for t in self.current_tasks]

    def reset_for_new_session(self, session_num):
        # Uncheck existing tasks or prepare new template if empty
        if not self.current_tasks:
            self.current_tasks = [
                {"text": f"Nhiệm vụ 1 của Ca #{session_num}", "done": False},
                {"text": f"Nhiệm vụ 2 của Ca #{session_num}", "done": False}
            ]
        else:
            for t in self.current_tasks:
                t["done"] = False


class BrainDumpManager:
    """Manages the Distraction Parking Lot: captures distracting thoughts and logged distraction events."""
    def __init__(self):
        # list of {"time": str, "text": str, "resolved": bool, "type": "manual" | "detected"}
        self.notes = []

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

