import ctypes
from ctypes import wintypes
import time
import threading

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Study keywords in titles
STUDY_KEYWORDS = [
    "bài giảng", "bai giang", "toán", "toan", "vật lý", "vat ly", "hóa học", "hoa hoc",
    "tiếng anh", "tieng anh", "ielts", "toeic", "lập trình", "lap trinh", "python",
    "javascript", "c++", "lecture", "tutorial", "khoá học", "khoa hoc", "course",
    "ôn thi", "on thi", "giáo trình", "giao trinh", "tài liệu", "tai lieu",
    "nhóm học", "classroom", "meet", "zoom", "teams", "drive", "docs", "sheets",
    "slides", "word", "excel", "powerpoint", "pdf", "acrobat", "foxit", "sumatra",
    "obsidian", "notion", "anki", "chatgpt", "gemini", "claude", "coursera", "edx", "udemy"
]

# Explicit entertainment keywords
ENTERTAINMENT_KEYWORDS = [
    "tiktok", "shorts", "reels", "truyen", "manga", "manhwa", "comic", "anime",
    "steam", "genshin", "dota", "league of legends", "valorant", "csgo", "roblox",
    "game", "shopee", "lazada", "tiki", "netflix", "twitch", "bilibili", "weibo",
    "webtruyen", "truyenfull", "nettruyen", "truyenqq", "vuighe", "animehay"
]

# Dual-use platforms (can be study or entertainment)
FLEXIBLE_PLATFORMS = [
    "youtube", "facebook", "fb.com", "reddit", "twitter", "x.com"
]

def get_active_window_info():
    """
    Safely retrieves (raw_title, proc_name, hwnd) of the foreground window without blocking.
    Guaranteed not to hang even if a foreign application is frozen or unresponsive.
    """
    try:
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return "", "", None

        # 1. Skip immediately if the target window is hung to prevent freezing
        if user32.IsHungAppWindow(hwnd):
            return "", "", hwnd

        # 2. Retrieve window title safely without cross-thread deadlock
        raw_title = ""
        buff = ctypes.create_unicode_buffer(512)
        # InternalGetWindowText reads directly from OS window info without sending messages
        n = user32.InternalGetWindowText(hwnd, buff, 512)
        if n > 0:
            raw_title = buff.value.strip()
        else:
            # Fallback to SendMessageTimeoutW with 60ms timeout and abort if hung
            SMTO_ABORTIFHUNG = 0x0002
            SMTO_BLOCK = 0x0001
            WM_GETTEXT = 0x000D
            res = wintypes.DWORD()
            user32.SendMessageTimeoutW(hwnd, WM_GETTEXT, 512, buff, SMTO_ABORTIFHUNG | SMTO_BLOCK, 60, ctypes.byref(res))
            raw_title = buff.value.strip()

        # 3. Retrieve process name safely
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if not pid.value:
            return raw_title, "", hwnd

        proc_name = ""
        h_proc = kernel32.OpenProcess(0x1000, False, pid.value) # PROCESS_QUERY_LIMITED_INFORMATION
        if h_proc:
            try:
                name_buff = ctypes.create_unicode_buffer(1024)
                size = wintypes.DWORD(1024)
                if kernel32.QueryFullProcessImageNameW(h_proc, 0, name_buff, ctypes.byref(size)):
                    proc_name = name_buff.value.split('\\')[-1].lower()
            finally:
                kernel32.CloseHandle(h_proc)

        return raw_title, proc_name, hwnd
    except Exception:
        return "", "", None


class DistractionMonitor:
    """
    Intelligent monitor tracking both productive study and off-task usage.
    Distinguishes deep work, online study (YouTube/FB lectures), and entertainment.
    """
    def __init__(self, brain_dump_manager=None, on_barrier_trigger=None):
        self.brain_dump_manager = brain_dump_manager
        self.on_barrier_trigger = on_barrier_trigger
        
        self.is_monitoring = False
        self.barrier_enabled = True
        self.allow_youtube_fb_study = False # Toggle: allow YouTube/FB as study tools
        
        # Tracking dictionaries
        # key -> {"name": str, "category": "deep_work"|"online_study"|"entertainment", "seconds": int, "manual": str|None}
        self.usage_records = {}
        self.distraction_events = [] # list of {"app": str, "title": str, "time": str, "duration": int}
        self.allowed_hwnds = set()
        self.last_distraction_time = 0
        self.in_distraction = False
        self._thread = None
        self.current_distracted_hwnd = None
        self.total_tracked_seconds = 0
        self.last_save_time = time.time()

        # Load persisted daily stats for today if available
        self._load_today_persisted_stats()

    def start_monitoring(self):
        if self.is_monitoring:
            return
        self.is_monitoring = True
        self.allowed_hwnds.clear()
        self._thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._thread.start()

    def stop_monitoring(self):
        self.is_monitoring = False
        self.save_daily_stats()

    def reset_stats(self):
        # Do not wipe historical daily usage on timer adjustment!
        self.in_distraction = False
        self.allowed_hwnds.clear()

    def _load_today_persisted_stats(self):
        """Loads today's accumulated tracking records from config.json so they survive app restarts."""
        try:
            from config_manager import load_config
            cfg = load_config()
            today_key = time.strftime("%Y-%m-%d")
            daily_usage = cfg.get("daily_usage", {}).get(today_key, {})
            if daily_usage and "records" in daily_usage:
                self.usage_records = daily_usage.get("records", {})
                self.total_tracked_seconds = daily_usage.get("total_seconds", sum(r.get("seconds", 0) for r in self.usage_records.values()))
                self.distraction_events = daily_usage.get("events", [])
        except Exception:
            pass

    def save_daily_stats(self):
        """Flushes today's accumulated web/app tracking records to config.json."""
        try:
            from config_manager import load_config, save_config
            today_key = time.strftime("%Y-%m-%d")
            cfg = load_config()
            daily_usage = cfg.setdefault("daily_usage", {})
            daily_usage[today_key] = {
                "records": self.usage_records,
                "total_seconds": self.total_tracked_seconds,
                "events": self.distraction_events[-30:]
            }
            save_config(cfg)
        except Exception:
            pass

    def set_youtube_fb_study_mode(self, enabled: bool):
        """Allows YouTube / Facebook to be counted as online study tools."""
        self.allow_youtube_fb_study = bool(enabled)

    def reclassify_item(self, app_key: str, new_category: str):
        """Allows the user to manually change an app's category (e.g. from entertainment to study)."""
        if app_key in self.usage_records:
            self.usage_records[app_key]["category"] = new_category
            self.usage_records[app_key]["manual"] = new_category

    def _worker_loop(self):
        while self.is_monitoring:
            self._process_active_window()
            if time.time() - self.last_save_time > 15:
                self.last_save_time = time.time()
                self.save_daily_stats()
            time.sleep(1)

    def _classify_window(self, raw_title: str, proc_name: str):
        """
        Classifies active window into:
        - "deep_work": Local study software, editors, readers, office, or desktop tools.
        - "online_study": Online lecture videos, course materials, learning portals.
        - "entertainment": TikTok, Manga/truyen, Games, Shopping, Shorts/Reels, or off-task browsing.
        Returns (app_key, display_name, category)
        """
        title_lower = raw_title.lower()
        full_text = f"{title_lower} {proc_name}"

        # 1. Check if definitely entertainment
        for kw in ENTERTAINMENT_KEYWORDS:
            if kw in full_text:
                display_name = kw.capitalize()
                if kw in ("truyen", "manga", "manhwa", "comic", "webtruyen", "truyenfull", "nettruyen", "truyenqq"):
                    display_name = "Đọc Truyện / Manga"
                elif kw in ("steam", "genshin", "dota", "league of legends", "valorant", "csgo", "roblox", "game"):
                    display_name = "Game / Trò chơi"
                elif kw in ("shopee", "lazada", "tiki"):
                    display_name = "Mua sắm Online"
                return kw, display_name, "entertainment"

        # 2. Check flexible platforms (YouTube, Facebook, etc.)
        for plat in FLEXIBLE_PLATFORMS:
            if plat in full_text:
                plat_name = "YouTube" if "youtube" in plat else ("Facebook" if "facebook" in plat or "fb.com" in plat else plat.capitalize())
                # If explicit study keywords appear in title
                has_study_kw = any(skw in title_lower for skw in STUDY_KEYWORDS)
                
                if self.allow_youtube_fb_study or has_study_kw:
                    return plat, f"{plat_name} (Bài giảng / Học)", "online_study"
                else:
                    return plat, f"{plat_name} (Chưa gắn nhãn học)", "entertainment"

        # 3. Check browsers or study keywords
        is_browser = proc_name in ("chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "opera.exe", "coccoc.exe")
        if is_browser:
            # Browser tab
            has_study_kw = any(skw in title_lower for skw in STUDY_KEYWORDS)
            if has_study_kw:
                return "browser_study", "Tra cứu & Tài liệu học Online", "online_study"
            # General web browsing
            clean_name = raw_title[:30] if raw_title else "Trình duyệt Web"
            return "browser_general", clean_name, "deep_work"

        # 4. Local Desktop Apps (Default to Deep Work)
        app_name = proc_name.replace(".exe", "").capitalize()
        if "code" in proc_name or "devenv" in proc_name:
            app_name = "VS Code / IDE"
        elif "word" in proc_name or "winword" in proc_name:
            app_name = "Microsoft Word"
        elif "excel" in proc_name:
            app_name = "Microsoft Excel"
        elif "powerpnt" in proc_name:
            app_name = "PowerPoint"
        elif "acrobat" in proc_name or "foxit" in proc_name or "sumatra" in proc_name:
            app_name = "Đọc Sách / Tài liệu PDF"
        elif "notepad" in proc_name:
            app_name = "Notepad / Ghi chú"

        return proc_name, app_name, "deep_work"

    def _process_active_window(self):
        try:
            raw_title, proc_name, hwnd = get_active_window_info()
            if not hwnd or not proc_name:
                return

            self.total_tracked_seconds += 1
            app_key, display_name, category = self._classify_window(raw_title, proc_name)

            # Check if user has manual override
            if app_key in self.usage_records and self.usage_records[app_key].get("manual"):
                category = self.usage_records[app_key]["manual"]

            # Update records
            if app_key not in self.usage_records:
                self.usage_records[app_key] = {
                    "key": app_key,
                    "name": display_name,
                    "category": category,
                    "seconds": 0,
                    "last_title": raw_title[:80],
                    "manual": None
                }
            self.usage_records[app_key]["seconds"] += 1
            self.usage_records[app_key]["last_title"] = raw_title[:80]

            # Handle Distraction / Barrier
            is_distracted = (category == "entertainment")
            if is_distracted and hwnd not in self.allowed_hwnds:
                self.current_distracted_hwnd = hwnd
                if not self.in_distraction:
                    self.in_distraction = True
                    now_str = time.strftime("%H:%M:%S")
                    title_snippet = raw_title[:50] if raw_title else display_name
                    self.distraction_events.append({
                        "app": display_name,
                        "title": title_snippet,
                        "time": now_str,
                        "duration": 1
                    })
                    # NOTE: Do NOT add note to brain_dump_manager!
                    # Brain dump is reserved purely for user's own thoughts.

                    if self.barrier_enabled:
                        if time.time() - self.last_distraction_time > 8:
                            self.last_distraction_time = time.time()
                            if self.on_barrier_trigger:
                                self.on_barrier_trigger(title_snippet, hwnd)
                else:
                    if self.distraction_events:
                        self.distraction_events[-1]["duration"] += 1
            else:
                self.in_distraction = False

        except Exception:
            pass

    def get_purity_stats(self, total_focus_minutes=50):
        """
        Calculates exact seconds for Deep Work, Online Study, and Entertainment.
        Returns complete, structured honest tracking report for Tab 3 and Modals.
        """
        target_seconds = max(1, int(total_focus_minutes * 60))
        sum_usage = sum(d.get("seconds", 0) for d in self.usage_records.values())
        actual_tracked = max(1, max(self.total_tracked_seconds, sum_usage))

        deep_work_sec = 0
        online_study_sec = 0
        entertainment_sec = 0

        breakdown = []
        for key, data in sorted(self.usage_records.items(), key=lambda x: x[1]["seconds"], reverse=True):
            sec = data["seconds"]
            cat = data["category"]
            if cat == "deep_work":
                deep_work_sec += sec
            elif cat == "online_study":
                online_study_sec += sec
            else:
                entertainment_sec += sec

            m = sec // 60
            s = sec % 60
            time_str = f"{m}p {s}s" if m > 0 else f"{s}s"
            pct = min(100, max(0, int((sec / actual_tracked) * 100)))

            breakdown.append({
                "key": key,
                "name": data["name"],
                "category": cat,
                "seconds": sec,
                "time_str": time_str,
                "percent": pct,
                "title": data.get("last_title", "")
            })

        # Check today's logged focus time from daily_history if records are empty
        today_key = time.strftime("%Y-%m-%d")
        today_logged_sec = 0
        try:
            from config_manager import load_config
            cfg = load_config()
            today_entry = cfg.get("daily_history", {}).get(today_key, {})
            today_logged_mins = today_entry.get("minutes", 0)
            if today_logged_mins > 0:
                today_logged_sec = today_logged_mins * 60
        except Exception:
            pass

        # If zero seconds were captured by foreground hook but sessions were finished today:
        if (deep_work_sec + online_study_sec) < today_logged_sec:
            diff = today_logged_sec - (deep_work_sec + online_study_sec)
            deep_work_sec += diff
            actual_tracked += diff
            # Add or update default study entry in breakdown
            found_study = False
            for b in breakdown:
                if b["category"] == "deep_work":
                    b["seconds"] += diff
                    m = b["seconds"] // 60
                    s = b["seconds"] % 60
                    b["time_str"] = f"{m}p {s}s" if m > 0 else f"{s}s"
                    found_study = True
                    break
            if not found_study:
                m = deep_work_sec // 60
                s = deep_work_sec % 60
                breakdown.insert(0, {
                    "key": "focus_flow_study",
                    "name": "Focus Flow • Học Tập Sâu",
                    "category": "deep_work",
                    "seconds": deep_work_sec,
                    "time_str": f"{m}p {s}s" if m > 0 else f"{s}s",
                    "percent": 100,
                    "title": "Thời gian các ca học đã hoàn thành"
                })

        productive_sec = deep_work_sec + online_study_sec
        total_recorded = deep_work_sec + online_study_sec + entertainment_sec
        # Purity percent based on actual tracked activity
        if total_recorded > 0:
            purity_percent = max(0, min(100, int((productive_sec / total_recorded) * 100)))
        else:
            purity_percent = 100

        def fmt_time(sec):
            mins = sec // 60
            rem_s = sec % 60
            if mins > 0 and rem_s > 0:
                return f"{mins} phút {rem_s} giây"
            elif mins > 0:
                return f"{mins} phút"
            return f"{rem_s} giây"

        return {
            "purity_percent": purity_percent,
            "deep_work_seconds": deep_work_sec,
            "deep_work_str": fmt_time(deep_work_sec),
            "online_study_seconds": online_study_sec,
            "online_study_str": fmt_time(online_study_sec),
            "distracted_seconds": entertainment_sec,
            "distracted_str": fmt_time(entertainment_sec),
            "productive_str": fmt_time(productive_sec),
            "pure_str": fmt_time(productive_sec),
            "total_tracked_seconds": actual_tracked,
            "total_tracked_str": fmt_time(actual_tracked),
            "incident_count": len(self.distraction_events),
            "allow_youtube_fb_study": self.allow_youtube_fb_study,
            "breakdown": breakdown,
            "events": self.distraction_events
        }
