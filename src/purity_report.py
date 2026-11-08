import tkinter as tk
from tkinter import ttk
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

class PurityReportModal:
    """Shows honest focus purity stats, checklist achievements, and distraction log."""
    def __init__(self, parent, stats, total_focus_minutes, checklist_history=None, brain_dump_notes=None, on_close_callback=None):
        self.parent = parent
        self.stats = stats
        self.total_focus_minutes = total_focus_minutes
        self.checklist_history = checklist_history or {}
        self.brain_dump_notes = brain_dump_notes or []
        self.on_close_callback = on_close_callback
        
        self.window = tk.Toplevel(parent)
        self.window.title("Báo cáo Năng suất & Độ tinh khiết")
        self.window.geometry("520x560")
        self.window.resizable(False, False)
        self.window.attributes('-topmost', True)
        self.window.configure(bg="#0b0f19")

        screen_w = parent.winfo_screenwidth()
        screen_h = parent.winfo_screenheight()
        pos_x = (screen_w - 520) // 2
        pos_y = (screen_h - 560) // 2
        self.window.geometry(f"+{pos_x}+{pos_y}")

        enable_dark_titlebar(self.window)
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()

    def _on_close(self):
        try:
            self.window.destroy()
        except Exception:
            pass
        if self.on_close_callback:
            self.on_close_callback()

    def _build_ui(self):
        container = tk.Frame(self.window, bg="#0b0f19", padx=20, pady=16)
        container.pack(fill="both", expand=True)

        # Header Title
        title_lbl = tk.Label(
            container,
            text="📊 BÁO CÁO NĂNG SUẤT CA HỌC",
            font=("Segoe UI", 12, "bold"),
            fg="#f8fafc",
            bg="#0b0f19"
        )
        title_lbl.pack(anchor="w")

        sub_lbl = tk.Label(
            container,
            text="Tổng kết độ tinh khiết tập trung và thành quả mục tiêu.",
            font=("Segoe UI", 8),
            fg="#64748b",
            bg="#0b0f19"
        )
        sub_lbl.pack(anchor="w", pady=(0, 10))

        # Purity Score Card
        score = self.stats.get("purity_percent", 100)
        if score >= 90:
            color = "#10b981"
            level_text = "🏆 XUẤT SẮC • TRẠNG THÁI DÒNG CHẢY (DEEP FLOW)"
        elif score >= 75:
            color = "#f59e0b"
            level_text = "🌿 KHÁ TỐT • CẦN GIẢM BỚT BẤM TAB NGOÀI"
        else:
            color = "#ef4444"
            level_text = "⚠️ XAO NHÃNG NHIỀU • CẦN RÈN KỶ LUẬT THÉP"

        score_card = tk.Frame(container, bg="#121826", padx=16, pady=10, highlightthickness=1, highlightbackground=color)
        score_card.pack(fill="x", pady=(0, 10))

        score_val = tk.Label(
            score_card,
            text=f"{score}% ĐỘ TINH KHIẾT",
            font=("Consolas", 22, "bold"),
            fg=color,
            bg="#121826"
        )
        score_val.pack()

        badge_level = tk.Label(
            score_card,
            text=level_text,
            font=("Segoe UI", 8, "bold"),
            fg=color,
            bg="#121826"
        )
        badge_level.pack(pady=(2, 0))

        # Stats Breakdown Grid
        grid_frame = tk.Frame(container, bg="#0b0f19")
        grid_frame.pack(fill="x", pady=(0, 10))

        # Focus time
        focus_col = tk.Frame(grid_frame, bg="#121826", padx=10, pady=8, highlightthickness=1, highlightbackground="#1f2d44")
        focus_col.pack(side="left", fill="both", expand=True, padx=(0, 4))
        tk.Label(focus_col, text="Thời gian học", font=("Segoe UI", 8), fg="#94a3b8", bg="#121826").pack()
        mins = self.total_focus_minutes if isinstance(self.total_focus_minutes, (int, float)) else 50
        tk.Label(focus_col, text=f"{mins} phút", font=("Segoe UI", 12, "bold"), fg="#f8fafc", bg="#121826").pack()

        # Distractions blocked
        blocked_cnt = self.stats.get("distraction_count", 0)
        dist_col = tk.Frame(grid_frame, bg="#121826", padx=10, pady=8, highlightthickness=1, highlightbackground="#1f2d44")
        dist_col.pack(side="left", fill="both", expand=True, padx=(4, 0))
        tk.Label(dist_col, text="Cố mở web xao nhãng", font=("Segoe UI", 8), fg="#94a3b8", bg="#121826").pack()
        col = "#10b981" if blocked_cnt == 0 else "#ef4444"
        tk.Label(dist_col, text=f"{blocked_cnt} lần", font=("Segoe UI", 12, "bold"), fg=col, bg="#121826").pack()

        # Distraction Events Log
        events = self.stats.get("distraction_events", [])
        log_frame = tk.Frame(container, bg="#121826", padx=12, pady=8, highlightthickness=1, highlightbackground="#1f2d44")
        log_frame.pack(fill="x", pady=(0, 12))

        log_title = tk.Label(log_frame, text="⚠️ Chi tiết các lần bị xao nhãng:", font=("Segoe UI", 8, "bold"), fg="#94a3b8", bg="#121826")
        log_title.pack(anchor="w", pady=(0, 4))

        if not events:
            empty_lbl = tk.Label(
                log_frame,
                text="🎉 Tuyệt vời! Bạn không mở bất kỳ trang web hay app gây xao nhãng nào!",
                font=("Segoe UI", 8, "italic"),
                fg="#10b981",
                bg="#121826",
                pady=4
            )
            empty_lbl.pack(anchor="w")
        else:
            for ev in events[:3]:
                r = tk.Label(log_frame, text=f"• [{ev.get('time')}] Mở: {ev.get('title')[:40]} ({ev.get('duration')}s)", font=("Segoe UI", 8), fg="#fca5a5", bg="#121826", anchor="w")
                r.pack(fill="x")

        # Close button
        btn_close = tk.Button(
            container,
            text="🌿 Đóng & Bắt đầu nghỉ 10 phút",
            font=("Segoe UI", 9, "bold"),
            fg="#ffffff",
            bg="#0284c7",
            activebackground="#0369a1",
            activeforeground="#ffffff",
            relief="flat",
            padx=16,
            pady=6,
            cursor="hand2",
            command=self._on_close
        )
        btn_close.pack(anchor="e")
