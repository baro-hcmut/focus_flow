import tkinter as tk
import ctypes
from ctypes import wintypes
import time

user32 = ctypes.windll.user32

class RECT(ctypes.Structure):
    _fields_ = [
        ('left', ctypes.c_long),
        ('top', ctypes.c_long),
        ('right', ctypes.c_long),
        ('bottom', ctypes.c_long)
    ]

class FocusSpotlight:
    """Focus Spotlight / Cinema Mode: Dims everything on screen except the study material."""
    def __init__(self, parent, on_close_callback=None):
        self.parent = parent
        self.on_close_callback = on_close_callback
        self.is_active = False
        self.dim_alpha = 0.68
        self.transparent_key = "#010101"
        self.bg_color = "#080c14"
        
        self.window = None
        self.canvas = None
        self.cutout_rect = None
        self.control_bar = None
        self.is_selecting = False
        self.start_x = 0
        self.start_y = 0
        self.current_box = (100, 100, 900, 700) # default rect

    def toggle(self):
        if self.is_active:
            self.hide()
        else:
            self.show()

    def show(self):
        if self.is_active:
            return
        self.is_active = True
        
        screen_w = user32.GetSystemMetrics(0)
        screen_h = user32.GetSystemMetrics(1)

        # Try auto-detecting current window under mouse or foreground before showing
        auto_rect = self._get_active_or_center_rect(screen_w, screen_h)
        self.current_box = auto_rect

        # 1. Fullscreen Dimmer Window
        if self.parent is None:
            self.window = tk.Tk()
        else:
            self.window = tk.Toplevel(self.parent)
            
        self.window.title("Rạp chiếu phim tập trung")
        self.window.attributes('-fullscreen', True)
        self.window.attributes('-topmost', True)
        self.window.attributes('-alpha', self.dim_alpha)
        self.window.attributes('-transparentcolor', self.transparent_key)
        self.window.configure(bg=self.bg_color)

        # 2. Canvas
        self.canvas = tk.Canvas(
            self.window,
            width=screen_w,
            height=screen_h,
            bg=self.bg_color,
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        # Draw the transparent hole cutout
        x1, y1, x2, y2 = self.current_box
        self.cutout_rect = self.canvas.create_rectangle(
            x1, y1, x2, y2,
            fill=self.transparent_key,
            outline="#38bdf8",
            width=2
        )

        # Bindings for dragging a custom area
        self.canvas.bind("<Button-1>", self._on_canvas_press)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)
        self.window.bind("<F9>", lambda e: self.hide())
        self.window.bind("<Escape>", lambda e: self.hide())

        # 3. Floating Control Bar (Tiny pill at screen top)
        self._build_control_bar(screen_w)

        if self.parent is None:
            self.window.mainloop()

    def _get_active_or_center_rect(self, screen_w, screen_h):
        try:
            hwnd = user32.GetForegroundWindow()
            if hwnd:
                r = RECT()
                user32.GetWindowRect(hwnd, ctypes.byref(r))
                w = r.right - r.left
                h = r.bottom - r.top
                # If window is valid size and not full screen
                if 200 < w < screen_w + 50 and 200 < h < screen_h + 50:
                    pad = 6
                    return (max(0, r.left - pad), max(0, r.top - pad), min(screen_w, r.right + pad), min(screen_h, r.bottom + pad))
        except Exception:
            pass
        # Default center 75% workspace
        margin_x = int(screen_w * 0.12)
        margin_y = int(screen_h * 0.08)
        return (margin_x, margin_y, screen_w - margin_x, screen_h - margin_y)

    def _build_control_bar(self, screen_w):
        bar_w = 480
        bar_h = 42
        pos_x = (screen_w - bar_w) // 2
        pos_y = 10

        self.control_bar = tk.Toplevel(self.window)
        self.control_bar.title("Điều khiển Rạp chiếu phim")
        self.control_bar.geometry(f"{bar_w}x{bar_h}+{pos_x}+{pos_y}")
        self.control_bar.overrideredirect(True)
        self.control_bar.attributes('-topmost', True)
        self.control_bar.configure(bg="#0f172a")

        container = tk.Frame(
            self.control_bar,
            bg="#1e293b",
            padx=10,
            pady=4,
            highlightthickness=1,
            highlightbackground="#38bdf8"
        )
        container.pack(fill="both", expand=True)

        lbl = tk.Label(
            container,
            text="🔦 Rạp chiếu phim",
            font=("Segoe UI", 9, "bold"),
            fg="#38bdf8",
            bg="#1e293b"
        )
        lbl.pack(side="left", padx=(4, 10))

        btn_auto = tk.Button(
            container,
            text="🎯 Bắt cửa sổ này",
            font=("Segoe UI", 8),
            fg="#e2e8f0",
            bg="#334155",
            activebackground="#475569",
            activeforeground="#ffffff",
            relief="flat",
            padx=8,
            pady=2,
            cursor="hand2",
            command=self.snap_to_active_window
        )
        btn_auto.pack(side="left", padx=3)

        btn_dim = tk.Button(
            container,
            text=f"Mờ {int(self.dim_alpha * 100)}%",
            font=("Segoe UI", 8),
            fg="#cbd5e1",
            bg="#334155",
            relief="flat",
            padx=8,
            pady=2,
            cursor="hand2",
            command=self.cycle_dim_level
        )
        btn_dim.pack(side="left", padx=3)
        self.btn_dim_lbl = btn_dim

        hint = tk.Label(
            container,
            text="(Kéo chuột để chọn vùng)",
            font=("Segoe UI", 8),
            fg="#64748b",
            bg="#1e293b"
        )
        hint.pack(side="left", padx=4)

        btn_close = tk.Button(
            container,
            text="✕ Tắt (F9)",
            font=("Segoe UI", 8, "bold"),
            fg="#fca5a5",
            bg="#450a0a",
            activebackground="#7f1d1d",
            activeforeground="#ffffff",
            relief="flat",
            padx=8,
            pady=2,
            cursor="hand2",
            command=self.hide
        )
        btn_close.pack(side="right")

    def snap_to_active_window(self):
        """Temporarily lower spotlight to detect the window user wants to spotlight."""
        self.control_bar.withdraw()
        self.window.withdraw()
        self.window.after(250, self._do_snap)

    def _do_snap(self):
        screen_w = user32.GetSystemMetrics(0)
        screen_h = user32.GetSystemMetrics(1)
        auto_rect = self._get_active_or_center_rect(screen_w, screen_h)
        self.current_box = auto_rect
        
        self.window.deiconify()
        self.window.attributes('-fullscreen', True)
        self.window.attributes('-topmost', True)
        
        x1, y1, x2, y2 = self.current_box
        self.canvas.coords(self.cutout_rect, x1, y1, x2, y2)
        self.control_bar.deiconify()
        self.control_bar.attributes('-topmost', True)

    def cycle_dim_level(self):
        levels = [0.45, 0.68, 0.85]
        cur_idx = 0
        for i, lvl in enumerate(levels):
            if abs(lvl - self.dim_alpha) < 0.05:
                cur_idx = i
                break
        next_idx = (cur_idx + 1) % len(levels)
        self.dim_alpha = levels[next_idx]
        if self.window:
            self.window.attributes('-alpha', self.dim_alpha)
        if hasattr(self, 'btn_dim_lbl'):
            self.btn_dim_lbl.config(text=f"Mờ {int(self.dim_alpha * 100)}%")

    def _on_canvas_press(self, event):
        self.is_selecting = True
        self.start_x = event.x
        self.start_y = event.y

    def _on_canvas_drag(self, event):
        if self.is_selecting and self.cutout_rect:
            x1 = min(self.start_x, event.x)
            y1 = min(self.start_y, event.y)
            x2 = max(self.start_x, event.x)
            y2 = max(self.start_y, event.y)
            self.canvas.coords(self.cutout_rect, x1, y1, x2, y2)

    def _on_canvas_release(self, event):
        if self.is_selecting:
            self.is_selecting = False
            x1 = min(self.start_x, event.x)
            y1 = min(self.start_y, event.y)
            x2 = max(self.start_x, event.x)
            y2 = max(self.start_y, event.y)
            if x2 - x1 > 40 and y2 - y1 > 40:
                self.current_box = (x1, y1, x2, y2)

    def hide(self):
        self.is_active = False
        if self.control_bar:
            try:
                self.control_bar.destroy()
            except Exception:
                pass
            self.control_bar = None
        if self.window:
            try:
                self.window.destroy()
            except Exception:
                pass
            self.window = None
        if self.on_close_callback:
            self.on_close_callback()
