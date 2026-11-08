import os
import time
import tkinter as tk
import ctypes

TRAP_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'so_tay_bat_bay.txt')

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


class TrapNotebookManager:
    """Manages trap notes, mistake reflections, and friction ratings per session."""
    def __init__(self):
        self.session_reflections = [] # list of {"session": int, "rating": str, "trap": str, "time": str}

    def record_reflection(self, session_num, rating, trap_text):
        trap_clean = trap_text.strip()
        now_str = time.strftime("%Y-%m-%d %H:%M")
        
        reflection = {
            "session": session_num,
            "rating": rating, # "smooth", "bump", "struggle"
            "trap": trap_clean,
            "time": now_str
        }
        self.session_reflections.append(reflection)

        # If a trap/mistake was noted, append to text file for permanent review
        if trap_clean:
            try:
                with open(TRAP_FILE, 'a', encoding='utf-8') as f:
                    rating_symbol = "🟢" if rating == "smooth" else ("🟡" if rating == "bump" else "🔴")
                    f.write(f"[{now_str}] Ca #{session_num} {rating_symbol}\n")
                    f.write(f"  -> Bẫy/Lỗi: {trap_clean}\n\n")
            except Exception as e:
                print(f"Error writing trap file: {e}")

    def get_reflections(self):
        return self.session_reflections

    def read_all_traps_from_file(self):
        if not os.path.exists(TRAP_FILE):
            return "Chưa có bẫy hoặc lỗi sai nào được ghi lại trong sổ tay."
        try:
            with open(TRAP_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                return content if content else "Sổ tay bắt bẫy đang trống."
        except Exception as e:
            return f"Không thể đọc file: {e}"


class SessionReflectionModal:
    """Quick 15-second reflection popup right as focus finishes."""
    def __init__(self, parent, session_num, on_complete_callback=None):
        self.parent = parent
        self.session_num = session_num
        self.on_complete_callback = on_complete_callback
        self.selected_rating = "smooth"
        self.remaining_seconds = 20

        self.window = tk.Toplevel(parent)
        self.window.title(f"Đúc kết Ca #{session_num}")
        self.window.geometry("490x320")
        self.window.resizable(False, False)
        self.window.attributes('-topmost', True)
        self.window.configure(bg="#0b0f19")

        # Center on screen
        screen_w = parent.winfo_screenwidth()
        screen_h = parent.winfo_screenheight()
        pos_x = (screen_w - 490) // 2
        pos_y = (screen_h - 320) // 2
        self.window.geometry(f"+{pos_x}+{pos_y}")

        enable_dark_titlebar(self.window)

        self._build_ui()
        self._countdown()

    def _build_ui(self):
        container = tk.Frame(self.window, bg="#121826", padx=20, pady=16, highlightthickness=1, highlightbackground="#38bdf8")
        container.pack(fill="both", expand=True, padx=10, pady=10)

        # Title
        t_lbl = tk.Label(
            container,
            text=f"🎯 ĐÚC KẾT CA HỌC #{self.session_num}",
            font=("Segoe UI", 11, "bold"),
            fg="#38bdf8",
            bg="#121826"
        )
        t_lbl.pack(anchor="w")

        sub = tk.Label(
            container,
            text="Đánh giá độ trơn tru và ghi lại bẫy/lỗi sai vừa gặp:",
            font=("Segoe UI", 8),
            fg="#94a3b8",
            bg="#121826"
        )
        sub.pack(anchor="w", pady=(0, 10))

        # 3 One-touch Rating Buttons
        rate_frame = tk.Frame(container, bg="#121826")
        rate_frame.pack(fill="x", pady=(0, 12))

        self.btn_smooth = tk.Button(
            rate_frame,
            text="🟢 Rất trơn tru",
            font=("Segoe UI", 9, "bold"),
            fg="#ffffff",
            bg="#059669",
            activebackground="#047857",
            activeforeground="#ffffff",
            relief="flat",
            padx=10,
            pady=6,
            cursor="hand2",
            command=lambda: self._select_rating("smooth")
        )
        self.btn_smooth.pack(side="left", expand=True, fill="x", padx=2)

        self.btn_bump = tk.Button(
            rate_frame,
            text="🟡 Có vướng mắc",
            font=("Segoe UI", 9),
            fg="#cbd5e1",
            bg="#182236",
            activebackground="#233048",
            activeforeground="#ffffff",
            relief="flat",
            padx=10,
            pady=6,
            cursor="hand2",
            command=lambda: self._select_rating("bump")
        )
        self.btn_bump.pack(side="left", expand=True, fill="x", padx=2)

        self.btn_struggle = tk.Button(
            rate_frame,
            text="🔴 Khá chật vật",
            font=("Segoe UI", 9),
            fg="#cbd5e1",
            bg="#182236",
            activebackground="#233048",
            activeforeground="#ffffff",
            relief="flat",
            padx=10,
            pady=6,
            cursor="hand2",
            command=lambda: self._select_rating("struggle")
        )
        self.btn_struggle.pack(side="left", expand=True, fill="x", padx=2)

        # Trap Input
        trap_label = tk.Label(
            container,
            text="📖 Bẫy đề thi / Lỗi sai vừa mắc (bấm Enter để lưu):",
            font=("Segoe UI", 8, "bold"),
            fg="#f59e0b",
            bg="#121826"
        )
        trap_label.pack(anchor="w", pady=(4, 2))

        self.entry_trap = tk.Entry(
            container,
            font=("Segoe UI", 9),
            bg="#0b0f19",
            fg="#f8fafc",
            insertbackground="#ffffff",
            relief="flat",
            highlightthickness=1,
            highlightbackground="#1f2d44"
        )
        self.entry_trap.pack(fill="x", ipady=4, pady=(0, 12))
        self.entry_trap.focus_set()
        self.entry_trap.bind("<Return>", lambda e: self._submit())

        # Footer Actions
        foot = tk.Frame(container, bg="#121826")
        foot.pack(fill="x")

        self.lbl_countdown = tk.Label(
            foot,
            text=f"Tự động chuyển nghỉ sau {self.remaining_seconds}s...",
            font=("Segoe UI", 8, "italic"),
            fg="#64748b",
            bg="#121826"
        )
        self.lbl_countdown.pack(side="left")

        btn_submit = tk.Button(
            foot,
            text="Xong & Sang giờ nghỉ ➜",
            font=("Segoe UI", 9, "bold"),
            fg="#ffffff",
            bg="#0284c7",
            activebackground="#0369a1",
            activeforeground="#ffffff",
            relief="flat",
            padx=14,
            pady=5,
            cursor="hand2",
            command=self._submit
        )
        btn_submit.pack(side="right")

    def _select_rating(self, rating):
        self.selected_rating = rating
        if rating == "smooth":
            self.btn_smooth.config(bg="#059669", fg="#ffffff", font=("Segoe UI", 9, "bold"))
            self.btn_bump.config(bg="#182236", fg="#cbd5e1", font=("Segoe UI", 9))
            self.btn_struggle.config(bg="#182236", fg="#cbd5e1", font=("Segoe UI", 9))
        elif rating == "bump":
            self.btn_smooth.config(bg="#182236", fg="#cbd5e1", font=("Segoe UI", 9))
            self.btn_bump.config(bg="#d97706", fg="#ffffff", font=("Segoe UI", 9, "bold"))
            self.btn_struggle.config(bg="#182236", fg="#cbd5e1", font=("Segoe UI", 9))
        else: # struggle
            self.btn_smooth.config(bg="#182236", fg="#cbd5e1", font=("Segoe UI", 9))
            self.btn_bump.config(bg="#182236", fg="#cbd5e1", font=("Segoe UI", 9))
            self.btn_struggle.config(bg="#dc2626", fg="#ffffff", font=("Segoe UI", 9, "bold"))

    def _countdown(self):
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            if self.lbl_countdown.winfo_exists():
                self.lbl_countdown.config(text=f"Tự động chuyển nghỉ sau {self.remaining_seconds}s...")
            self.window.after(1000, self._countdown)
        else:
            self._submit()

    def _submit(self):
        trap_text = self.entry_trap.get()
        # Record into manager
        try:
            from trap_notebook import TrapNotebookManager
            TrapNotebookManager().record_reflection(self.session_num, self.selected_rating, trap_text)
        except Exception:
            pass

        try:
            self.window.destroy()
        except Exception:
            pass

        if self.on_complete_callback:
            self.on_complete_callback()
