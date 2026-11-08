import tkinter as tk
from tkinter import ttk, messagebox
import random
import ctypes
import time
from sound_manager import play_break_sound, play_focus_sound
from system_actions import wake_up_monitor, turn_off_monitor

HEALTH_TIPS = [
    ("👀 Thư giãn đôi mắt", "Quy tắc 20-20-20: Hãy nhìn vào một vật ở xa khoảng 6 mét trong 20 giây để giảm căng thẳng cho mắt."),
    ("💧 Bổ sung nước", "Uống một cốc nước lọc ấm để cấp nước cho tế bào và giúp não bộ duy trì sự tập trung cao độ."),
    ("🧘 Vươn vai & Thả lỏng", "Đứng dậy, đan hai tay vươn thẳng lên trần nhà, nhẹ nhàng nghiêng người sang trái và phải."),
    ("🚶 Vận động nhẹ", "Rời khỏi ghế và đi lại vài bước quanh phòng để kích thích tuần hoàn máu ở chân và lưng."),
    ("🌬️ Hít thở sâu", "Hít vào thật sâu bằng mũi trong 4 giây, giữ hơi 4 giây, và thở từ từ ra bằng miệng trong 6 giây."),
    ("💆 Giảm mỏi vai gáy", "Xoay khớp vai theo vòng tròn từ trước ra sau 5 lần, sau đó nghiêng nhẹ đầu sang từng bên.")
]

class POINT(ctypes.Structure):
    _fields_ = [('x', ctypes.c_long), ('y', ctypes.c_long)]

class RestOverlay:
    def __init__(self, parent, remaining_seconds, on_emergency_exit, on_break_finish, on_start_next_early=None, auto_prep_seconds=180, hardcore=True, turn_off_display_flag=False):
        self.parent = parent
        self.remaining_seconds = remaining_seconds
        self.total_seconds = remaining_seconds
        self.on_emergency_exit = on_emergency_exit
        self.on_break_finish = on_break_finish
        self.on_start_next_early = on_start_next_early
        self.auto_prep_seconds = auto_prep_seconds
        self.hardcore = hardcore
        self.turn_off_display_flag = turn_off_display_flag
        
        self.is_closed = False
        self.is_prep_mode = False
        self.prep_banner = None
        self._drag_data = {"x": 0, "y": 0}
        
        # Cursor tracking to keep screen off if user moves mouse in hardcore screen_off mode
        self.last_cursor_pos = self._get_cursor_pos()
        
        self.window = tk.Toplevel(parent)
        self.window.title("Thời gian nghỉ ngơi")
        self.window.attributes('-fullscreen', True)
        self.window.attributes('-topmost', True)
        self.window.configure(bg="#080c14")
        
        # Intercept closing
        if self.hardcore:
            self.window.protocol("WM_DELETE_WINDOW", self._hardcore_block)
            self.window.bind("<Alt-F4>", lambda e: "break")
            self.window.bind("<Escape>", lambda e: "break")
        else:
            self.window.protocol("WM_DELETE_WINDOW", self.request_emergency_exit)
            self.window.bind("<Escape>", lambda e: self.request_emergency_exit())
        
        self._build_ui()
        self._pick_new_tip()
        self._update_clock()
        self._tick_countdown()

    def _get_cursor_pos(self):
        try:
            pt = POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
            return (pt.x, pt.y)
        except Exception:
            return (0, 0)

    def _hardcore_block(self):
        """Block Alt+F4 in hardcore mode."""
        pass

    def _build_ui(self):
        container = tk.Frame(self.window, bg="#080c14")
        container.place(relx=0.5, rely=0.5, anchor="center")

        # Top Badge
        badge_frame = tk.Frame(container, bg="#132338", padx=16, pady=6)
        badge_frame.pack(pady=(0, 16))
        
        badge_text = "🔒 KỶ LUẬT THÉP • NGHỈ NGƠI KHÔNG THỂ LÁCH" if self.hardcore else "🌿 ĐÃ ĐẾN GIỜ NGHỈ NGƠI • HÃY RỜI MÀN HÌNH"
        badge_color = "#f59e0b" if self.hardcore else "#38bdf8"
        self.badge_lbl = tk.Label(
            badge_frame,
            text=badge_text,
            font=("Segoe UI", 12, "bold"),
            fg=badge_color,
            bg="#132338"
        )
        self.badge_lbl.pack()

        # Large Digital Countdown
        self.time_lbl = tk.Label(
            container,
            text=self._format_time(self.remaining_seconds),
            font=("Consolas", 72, "bold"),
            fg="#f8fafc",
            bg="#080c14"
        )
        self.time_lbl.pack(pady=8)

        # Progress bar
        self.progress_canvas = tk.Canvas(container, width=420, height=8, bg="#1e293b", highlightthickness=0)
        self.progress_canvas.pack(pady=12)
        self.progress_bar = self.progress_canvas.create_rectangle(0, 0, 420, 8, fill=badge_color, width=0)

        # Card for Health Tip
        tip_card = tk.Frame(container, bg="#0f172a", padx=28, pady=20, highlightthickness=1, highlightbackground="#1e293b")
        tip_card.pack(pady=16, fill="x")

        self.tip_title_lbl = tk.Label(
            tip_card,
            text="",
            font=("Segoe UI", 14, "bold"),
            fg="#38bdf8",
            bg="#0f172a"
        )
        self.tip_title_lbl.pack(anchor="w", pady=(0, 6))

        self.tip_desc_lbl = tk.Label(
            tip_card,
            text="",
            font=("Segoe UI", 11),
            fg="#94a3b8",
            bg="#0f172a",
            wraplength=480,
            justify="left"
        )
        self.tip_desc_lbl.pack(anchor="w")

        # Action status frame
        self.actions_frame = tk.Frame(container, bg="#080c14")
        self.actions_frame.pack(pady=(16, 8))

        if self.hardcore:
            # In hardcore mode: show status explaining 7' lock + 3' auto prep
            self.hardcore_status_lbl = tk.Label(
                self.actions_frame,
                text="⚡ Màn hình đang khóa cứng 7 phút đầu để bảo vệ mắt.\nSẽ tự động mở sáng ở đúng 3 phút cuối (03:00) để bạn tìm bài tập!",
                font=("Segoe UI", 10, "bold"),
                fg="#f59e0b",
                bg="#080c14",
                justify="center"
            )
            self.hardcore_status_lbl.pack()
        else:
            # Normal mode: allow manual switch
            btn_prep = tk.Button(
                self.actions_frame,
                text="💻 Mở máy tìm bài tập / Chuẩn bị ca sau",
                font=("Segoe UI", 11, "bold"),
                fg="#0f172a",
                bg="#38bdf8",
                activebackground="#0284c7",
                activeforeground="#ffffff",
                relief="flat",
                padx=16,
                pady=7,
                cursor="hand2",
                command=self.switch_to_prep_mode
            )
            btn_prep.pack(side="left", padx=6)

            btn_exit = tk.Button(
                self.actions_frame,
                text="Thoát hẳn (Esc)",
                font=("Segoe UI", 10),
                fg="#94a3b8",
                bg="#1e293b",
                activebackground="#334155",
                activeforeground="#f8fafc",
                relief="flat",
                padx=14,
                pady=7,
                cursor="hand2",
                command=self.request_emergency_exit
            )
            btn_exit.pack(side="left", padx=6)

    def _format_time(self, seconds):
        m = max(0, seconds) // 60
        s = max(0, seconds) % 60
        return f"{m:02d}:{s:02d}"

    def _pick_new_tip(self):
        title, desc = random.choice(HEALTH_TIPS)
        self.tip_title_lbl.config(text=title)
        self.tip_desc_lbl.config(text=desc)

    def _update_clock(self):
        if self.is_closed:
            return
            
        time_str = self._format_time(self.remaining_seconds)
        self.time_lbl.config(text=time_str)
        
        ratio = max(0.0, min(1.0, self.remaining_seconds / self.total_seconds))
        bar_width = int(420 * ratio)
        self.progress_canvas.coords(self.progress_bar, 0, 0, bar_width, 8)

        if self.is_prep_mode and hasattr(self, 'prep_clock_lbl') and self.prep_banner:
            self.prep_clock_lbl.config(text=f"⏳ CHUẨN BỊ CA SAU: {time_str}")

    def _tick_countdown(self):
        if self.is_closed:
            return

        if self.remaining_seconds <= 0:
            self.close()
            if self.on_break_finish:
                self.on_break_finish()
            return

        # Check for auto transition to prep mode (3 minutes mark = 180s)
        if not self.is_prep_mode and self.auto_prep_seconds > 0 and self.remaining_seconds <= self.auto_prep_seconds:
            wake_up_monitor()
            self.switch_to_prep_mode(auto=True)

        # In hardcore screen_off mode: if user shakes mouse during 7m lock, re-turn off screen
        if self.hardcore and self.turn_off_display_flag and not self.is_prep_mode:
            cur_pos = self._get_cursor_pos()
            if abs(cur_pos[0] - self.last_cursor_pos[0]) > 10 or abs(cur_pos[1] - self.last_cursor_pos[1]) > 10:
                self.last_cursor_pos = cur_pos
                # User shook mouse, re-blank monitor!
                turn_off_monitor()

        self.remaining_seconds -= 1
        self._update_clock()

        # Change tips every 60 seconds
        if not self.is_prep_mode and self.remaining_seconds > 0 and self.remaining_seconds % 60 == 0:
            self._pick_new_tip()

        self.window.after(1000, self._tick_countdown)

    def switch_to_prep_mode(self, auto=False):
        """Lowers full-screen blackout and displays top floating banner so user can prepare next session exercises."""
        if self.is_prep_mode:
            return
            
        self.is_prep_mode = True
        wake_up_monitor()
        self.window.withdraw() # Hide full-screen blackout

        # Soft chime alert that prep time has arrived
        play_break_sound()

        # Create top floating prep banner
        self.prep_banner = tk.Toplevel(self.parent)
        self.prep_banner.title("Chuẩn bị ca học tiếp theo")
        
        screen_w = self.parent.winfo_screenwidth()
        banner_w = 640
        banner_h = 52
        pos_x = max(10, (screen_w - banner_w) // 2)
        pos_y = 15

        self.prep_banner.geometry(f"{banner_w}x{banner_h}+{pos_x}+{pos_y}")
        self.prep_banner.overrideredirect(True)
        self.prep_banner.attributes('-topmost', True)
        self.prep_banner.configure(bg="#0f172a")

        container = tk.Frame(self.prep_banner, bg="#1e293b", padx=12, pady=6, highlightthickness=1, highlightbackground="#f59e0b" if self.hardcore else "#38bdf8")
        container.pack(fill="both", expand=True)

        time_str = self._format_time(self.remaining_seconds)
        self.prep_clock_lbl = tk.Label(
            container,
            text=f"⏳ CHUẨN BỊ CA SAU: {time_str}",
            font=("Segoe UI", 11, "bold"),
            fg="#f59e0b" if self.hardcore else "#38bdf8",
            bg="#1e293b"
        )
        self.prep_clock_lbl.pack(side="left", padx=(4, 12))

        # Tip hint on banner
        hint_lbl = tk.Label(
            container,
            text="Hãy mở bài tập & tài liệu ca tới",
            font=("Segoe UI", 8),
            fg="#94a3b8",
            bg="#1e293b"
        )
        hint_lbl.pack(side="left", padx=(0, 10))

        # Action: Start next study session early (if done finding exercises)
        btn_start_now = tk.Button(
            container,
            text="▶ Vào học ngay",
            font=("Segoe UI", 9, "bold"),
            fg="#ffffff",
            bg="#059669",
            activebackground="#047857",
            activeforeground="#ffffff",
            relief="flat",
            padx=12,
            pady=3,
            cursor="hand2",
            command=self.start_study_early
        )
        btn_start_now.pack(side="left", padx=4)

        if not self.hardcore:
            btn_back_rest = tk.Button(
                container,
                text="🌿 Tiếp tục nghỉ",
                font=("Segoe UI", 9),
                fg="#e2e8f0",
                bg="#334155",
                activebackground="#475569",
                activeforeground="#ffffff",
                relief="flat",
                padx=10,
                pady=3,
                cursor="hand2",
                command=self.return_to_rest_mode
            )
            btn_back_rest.pack(side="left", padx=4)

        # Make floating banner draggable so it doesn't block Chrome tabs or buttons
        container.bind("<Button-1>", self._start_banner_drag)
        container.bind("<B1-Motion>", self._do_banner_drag)
        self.prep_clock_lbl.bind("<Button-1>", self._start_banner_drag)
        self.prep_clock_lbl.bind("<B1-Motion>", self._do_banner_drag)

    def return_to_rest_mode(self):
        if self.is_prep_mode:
            self.is_prep_mode = False
            if self.prep_banner:
                self.prep_banner.destroy()
                self.prep_banner = None
            self.window.deiconify()
            self.window.attributes('-fullscreen', True)
            self.window.attributes('-topmost', True)

    def start_study_early(self):
        self.close()
        if self.on_start_next_early:
            self.on_start_next_early()
        elif self.on_break_finish:
            self.on_break_finish()

    def _start_banner_drag(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def _do_banner_drag(self, event):
        if self.prep_banner:
            x = self.prep_banner.winfo_pointerx() - self._drag_data["x"]
            y = self.prep_banner.winfo_pointery() - self._drag_data["y"]
            self.prep_banner.geometry(f"+{x}+{y}")

    def request_emergency_exit(self):
        if self.hardcore:
            return  # No emergency exit allowed in hardcore
        self.window.attributes('-topmost', False)
        ans = messagebox.askyesno(
            "Thoát khẩn cấp",
            "Bạn có chắc muốn kết thúc sớm giờ nghỉ ngơi và quay lại làm việc ngay không?",
            parent=self.window
        )
        if ans:
            self.close()
            if self.on_emergency_exit:
                self.on_emergency_exit()
        else:
            self.window.attributes('-topmost', True)

    def close(self):
        self.is_closed = True
        if self.prep_banner:
            try:
                self.prep_banner.destroy()
            except Exception:
                pass
            self.prep_banner = None
        try:
            self.window.destroy()
        except Exception:
            pass
