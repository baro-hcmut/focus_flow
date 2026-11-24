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
    "javascript", "typescript", "c++", "react", "docker", "sql", "github", "stackoverflow",
    "leetcode", "hackerrank", "codeforces", "mdn", "w3schools",
    "lecture", "tutorial", "khoá học", "khoa hoc", "khóa học", "course",
    "ôn thi", "on thi", "giáo trình", "giao trinh", "tài liệu", "tai lieu",
    "vi phân", "vi phan", "tích phân", "tich phan", "đạo hàm", "dao ham",
    "ma trận", "ma tran", "đại số", "dai so", "xác suất", "xac suat",
    "thống kê", "thong ke", "giải tích", "giai tich", "giải thuật", "giai thuat",
    "cấu trúc dữ liệu", "cau truc du lieu", "mạch điện", "mach dien",
    "giải đề", "giai de", "chữa đề", "chua de", "chương ", "chuong ",
    "cs50", "3blue1brown", "khan academy", "freecodecamp", "28tech",
    "hocmai", "học mãi", "tuyensinh247", "organic chemistry tutor", "mit opencourseware",
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

BROWSER_SUFFIXES = (
    " - google chrome", " - brave", " - microsoft edge", " - mozilla firefox",
    " - cốc cốc", " - opera", " - vivaldi"
)

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
    Tracks productive study and off-task usage both per-session and daily.
    Distinguishes deep work, online study (YouTube/FB lectures), and entertainment.
    """
    def __init__(self, brain_dump_manager=None, on_barrier_trigger=None):
        self.brain_dump_manager = brain_dump_manager
        self.on_barrier_trigger = on_barrier_trigger

        self.is_monitoring = False
        self.barrier_enabled = True
        self.allow_youtube_fb_study = False      # Global UI toggle: YouTube/FB study mode
        self.session_youtube_study_temp = False  # Per-session playlist unlock (auto-resets after session)
        self.custom_study_keywords = []          # User-defined channel/topic keywords

        self._thread = None
        self._data_lock = threading.Lock()

        # Daily tracking dictionaries
        self.usage_records = {}
        self.distraction_events = []
        self.total_tracked_seconds = 0
        self.completed_sessions_today = []

        # Current-session-only tracking dictionaries
        self.session_records = {}
        self.session_events = []
        self.session_total_seconds = 0
        self.session_start_time = time.strftime("%H:%M")

        # Per-video / per-window allowlists
        self.allowed_hwnds = set()
        self.allowed_video_titles = set()
        self.snoozed_hwnds = {}
        self.last_distraction_time = 0
        self.in_distraction = False
        self.current_distracted_hwnd = None
        self.last_distracted_key = None
        self.last_distracted_title = ""
        self._yt_homepage_since = 0.0
        self.last_save_time = time.time()
        self.current_date = time.strftime("%Y-%m-%d")

        self._load_today_persisted_stats()

    def on_date_changed(self, new_date_str):
        """Called when system clock rolls over past midnight."""
        try:
            self.save_daily_stats(date_key=self.current_date)
            with self._data_lock:
                self.current_date = new_date_str
                self.usage_records = {}
                self.total_tracked_seconds = 0
                self.distraction_events = []
                self.completed_sessions_today = []
                self._reset_session_unlocked()
            self._load_today_persisted_stats()
        except Exception:
            pass

    def _reset_session_unlocked(self):
        self.session_records = {}
        self.session_events = []
        self.session_total_seconds = 0
        self.session_start_time = time.strftime("%H:%M")
        self.session_youtube_study_temp = False
        self.in_distraction = False
        self.last_distracted_key = None
        self.last_distracted_title = ""
        self._yt_homepage_since = 0.0
        self.allowed_hwnds.clear()
        self.snoozed_hwnds.clear()

    def start_monitoring(self):
        with self._data_lock:
            if self.session_total_seconds == 0:
                self.session_start_time = time.strftime("%H:%M")
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
        """Resets only the active uncompleted session without wiping daily history."""
        with self._data_lock:
            self._reset_session_unlocked()

    def reset_current_session(self):
        """Alias used after archiving a completed session."""
        self.reset_stats()

    def set_custom_study_keywords(self, keywords):
        if isinstance(keywords, str):
            parsed = [k.strip().lower() for k in keywords.split(",") if k.strip()]
        elif isinstance(keywords, (list, tuple)):
            parsed = [str(k).strip().lower() for k in keywords if str(k).strip()]
        else:
            parsed = []
        with self._data_lock:
            self.custom_study_keywords = parsed

    def allow_current_video_as_study(self):
        """Allows ONLY the specific video/page title that triggered the barrier."""
        clean_title = ""
        with self._data_lock:
            clean_title = (self.last_distracted_title or "").strip().lower()
            if clean_title and clean_title != "youtube":
                self.allowed_video_titles.add(clean_title)
            elif self.current_distracted_hwnd:
                self.allowed_hwnds.add(self.current_distracted_hwnd)
            self.in_distraction = False
        return clean_title

    def allow_session_youtube_study(self):
        """Allows YouTube/FB for the remainder of the current focus session only."""
        with self._data_lock:
            self.session_youtube_study_temp = True
            self.in_distraction = False

    def snooze_hwnd(self, hwnd, duration_seconds=120):
        """Temporarily allow entertainment on this window for duration_seconds (e.g. 2 minutes)."""
        if hwnd:
            self.snoozed_hwnds[hwnd] = time.time() + duration_seconds
            self.in_distraction = False

    def _migrate_legacy_records(self, records):
        """Splits legacy 'youtube' key into 'youtube_study' or 'youtube_ent' cleanly."""
        if not isinstance(records, dict):
            return {}
        if "youtube" in records:
            old = records.pop("youtube")
            cat = old.get("category", "entertainment")
            new_key = "youtube_study" if cat in ("online_study", "deep_work") else "youtube_ent"
            new_name = "YouTube • Học tập" if new_key == "youtube_study" else "YouTube • Giải trí"
            if new_key not in records:
                old["key"] = new_key
                old["name"] = new_name
                records[new_key] = old
            else:
                records[new_key]["seconds"] = records[new_key].get("seconds", 0) + old.get("seconds", 0)
        return records

    def _load_today_persisted_stats(self):
        """Loads today's accumulated tracking records and session snapshots from config.json."""
        try:
            from config_manager import load_config
            cfg = load_config()
            self.set_custom_study_keywords(cfg.get("custom_study_keywords", []))
            today_key = time.strftime("%Y-%m-%d")
            daily_usage = cfg.get("daily_usage", {}).get(today_key, {})
            if daily_usage:
                records = self._migrate_legacy_records(daily_usage.get("records", {}))
                with self._data_lock:
                    self.usage_records = records
                    self.total_tracked_seconds = daily_usage.get("total_seconds", sum(r.get("seconds", 0) for r in records.values()))
                    self.distraction_events = daily_usage.get("events", [])
                    self.completed_sessions_today = daily_usage.get("sessions_detail", [])
        except Exception:
            pass

    def save_daily_stats(self, date_key=None):
        """Flushes today's accumulated web/app tracking records and per-session snapshots to config.json."""
        try:
            from config_manager import load_config, save_config
            with self._data_lock:
                today_key = date_key or self.current_date or time.strftime("%Y-%m-%d")
                records_copy = {k: dict(v) for k, v in self.usage_records.items()}
                total_sec = self.total_tracked_seconds
                events_copy = list(self.distraction_events[-30:])
                sessions_copy = list(self.completed_sessions_today)
            cfg = load_config()
            daily_usage = cfg.setdefault("daily_usage", {})
            daily_usage[today_key] = {
                "records": records_copy,
                "total_seconds": total_sec,
                "events": events_copy,
                "sessions_detail": sessions_copy
            }
            save_config(cfg)
        except Exception:
            pass

    def archive_completed_session(self, session_num, actual_minutes, goal_text=""):
        """Snapshots the just-finished session into today's sessions_detail and resets session counters."""
        end_time_str = time.strftime("%H:%M")
        report = self.get_session_purity_stats(max(1, actual_minutes))
        snapshot = {
            "session": int(session_num),
            "start_time": self.session_start_time,
            "end_time": end_time_str,
            "minutes": int(actual_minutes),
            "goal": str(goal_text or "").strip(),
            "purity_percent": report["purity_percent"],
            "deep_work_seconds": report["deep_work_seconds"],
            "deep_work_str": report["deep_work_str"],
            "online_study_seconds": report["online_study_seconds"],
            "online_study_str": report["online_study_str"],
            "distracted_seconds": report["distracted_seconds"],
            "distracted_str": report["distracted_str"],
            "total_tracked_seconds": report["total_tracked_seconds"],
            "total_tracked_str": report["total_tracked_str"],
            "breakdown": report["breakdown"],
        }
        with self._data_lock:
            self.completed_sessions_today.append(snapshot)
            self._reset_session_unlocked()
        self.save_daily_stats()
        return snapshot

    def set_youtube_fb_study_mode(self, enabled: bool):
        """Allows YouTube / Facebook to be counted as online study tools."""
        self.allow_youtube_fb_study = bool(enabled)

    def reclassify_item(self, app_key: str, new_category: str, scope: str = "daily", session_num=None):
        """Changes an app's category in daily, current session, or a specific completed session."""
        updated = False
        with self._data_lock:
            if scope in ("daily", "current"):
                for store in (self.usage_records, self.session_records):
                    if app_key in store:
                        store[app_key]["category"] = new_category
                        store[app_key]["manual"] = new_category
                        updated = True
            if scope == "session" and session_num is not None:
                for sess in self.completed_sessions_today:
                    if sess.get("session") == int(session_num):
                        deep_s = 0
                        online_s = 0
                        dist_s = 0
                        for item in sess.get("breakdown", []):
                            if item.get("key") == app_key:
                                item["category"] = new_category
                                updated = True
                            sec = item.get("seconds", 0)
                            if item.get("category") == "deep_work":
                                deep_s += sec
                            elif item.get("category") == "online_study":
                                online_s += sec
                            else:
                                dist_s += sec
                        if updated:
                            total_s = deep_s + online_s + dist_s
                            prod_s = deep_s + online_s
                            sess["deep_work_seconds"] = deep_s
                            sess["online_study_seconds"] = online_s
                            sess["distracted_seconds"] = dist_s
                            sess["deep_work_str"] = self._fmt_time(deep_s)
                            sess["online_study_str"] = self._fmt_time(online_s)
                            sess["distracted_str"] = self._fmt_time(dist_s)
                            sess["purity_percent"] = max(0, min(100, int((prod_s / total_s) * 100))) if total_s > 0 else 100
                        break
        if updated:
            self.save_daily_stats()

    def _worker_loop(self):
        while self.is_monitoring:
            self._process_active_window()
            if time.time() - self.last_save_time > 15:
                self.last_save_time = time.time()
                self.save_daily_stats()
            time.sleep(1)

    @staticmethod
    def _extract_clean_title(raw_title: str) -> str:
        t = (raw_title or "").strip()
        lower = t.lower()
        for suf in BROWSER_SUFFIXES:
            if lower.endswith(suf):
                t = t[:len(t) - len(suf)].strip()
                lower = t.lower()
                break
        if lower.endswith(" - youtube"):
            t = t[:-10].strip()
        return t

    @staticmethod
    def _is_youtube_homepage(raw_title: str) -> bool:
        t = (raw_title or "").strip().lower()
        for suf in BROWSER_SUFFIXES:
            if t.endswith(suf):
                t = t[:len(t) - len(suf)].strip()
                break
        return t in ("youtube", "youtube.com", "")

    def _has_study_signal(self, title_lower: str) -> bool:
        if any(skw in title_lower for skw in STUDY_KEYWORDS):
            return True
        if any(ckw in title_lower for ckw in self.custom_study_keywords):
            return True
        return False

    def _classify_window(self, raw_title: str, proc_name: str):
        """
        Classifies active window into ("deep_work", "online_study", "entertainment").
        Returns (app_key, display_name, category, clean_title).
        """
        title_lower = raw_title.lower()
        full_text = f"{title_lower} {proc_name}"
        clean_title = self._extract_clean_title(raw_title)
        clean_lower = clean_title.lower()
        has_study_kw = self._has_study_signal(title_lower)

        # 1. Explicit entertainment check (skip 'game' false-positive if study keywords present)
        for kw in ENTERTAINMENT_KEYWORDS:
            if kw in full_text:
                if kw == "game" and has_study_kw:
                    continue
                display_name = kw.capitalize()
                if kw in ("truyen", "manga", "manhwa", "comic", "webtruyen", "truyenfull", "nettruyen", "truyenqq"):
                    display_name = "Đọc Truyện / Manga"
                elif kw in ("steam", "genshin", "dota", "league of legends", "valorant", "csgo", "roblox", "game"):
                    display_name = "Game / Trò chơi"
                elif kw in ("shopee", "lazada", "tiki"):
                    display_name = "Mua sắm Online"
                elif kw == "shorts":
                    display_name = "YouTube Shorts" if "youtube" in full_text else "Video ngắn"
                elif kw == "tiktok":
                    display_name = "TikTok"
                return kw, display_name, "entertainment", clean_title

        # 2. Flexible dual-use platforms (split into distinct _study vs _ent keys!)
        for plat in FLEXIBLE_PLATFORMS:
            if plat in full_text:
                plat_name = "YouTube" if "youtube" in plat else ("Facebook" if "facebook" in plat or "fb.com" in plat else plat.capitalize())
                plat_id = "facebook" if plat == "fb.com" else ("x" if plat == "x.com" else plat)
                is_video_approved = bool(clean_lower and clean_lower in self.allowed_video_titles)
                is_study = self.allow_youtube_fb_study or self.session_youtube_study_temp or has_study_kw or is_video_approved

                if is_study:
                    return f"{plat_id}_study", f"{plat_name} • Học tập", "online_study", clean_title
                else:
                    return f"{plat_id}_ent", f"{plat_name} • Giải trí", "entertainment", clean_title

        # 3. Browsers
        is_browser = proc_name in ("chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "opera.exe", "coccoc.exe")
        if is_browser:
            if has_study_kw:
                return "browser_study", "Tài liệu học Online", "online_study", clean_title
            short_name = clean_title[:28] if clean_title else "Trình duyệt Web"
            return "browser_general", short_name, "deep_work", clean_title

        # 4. Local Desktop Apps
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
            app_name = "Đọc tài liệu PDF"
        elif "notepad" in proc_name:
            app_name = "Notepad"

        return proc_name, app_name, "deep_work", clean_title

    @staticmethod
    def _record_tick(store, app_key, display_name, category, raw_title):
        if app_key not in store:
            store[app_key] = {
                "key": app_key,
                "name": display_name,
                "category": category,
                "seconds": 0,
                "last_title": raw_title[:80],
                "manual": None
            }
        store[app_key]["seconds"] += 1
        store[app_key]["name"] = display_name
        store[app_key]["last_title"] = raw_title[:80]

    def _process_active_window(self):
        try:
            raw_title, proc_name, hwnd = get_active_window_info()
            if not hwnd or not proc_name:
                return

            app_key, display_name, category, clean_title = self._classify_window(raw_title, proc_name)
            is_yt_home = ("youtube" in raw_title.lower()) and self._is_youtube_homepage(raw_title)

            with self._data_lock:
                self.total_tracked_seconds += 1
                self.session_total_seconds += 1

                # Respect explicit manual override only for non-dual-use apps, OR per-key override
                if app_key in self.usage_records and self.usage_records[app_key].get("manual"):
                    category = self.usage_records[app_key]["manual"]

                self._record_tick(self.usage_records, app_key, display_name, category, clean_title or raw_title)
                self._record_tick(self.session_records, app_key, display_name, category, clean_title or raw_title)

                now = time.time()
                expired_hwnds = [h for h, exp in list(self.snoozed_hwnds.items()) if now >= exp]
                for h in expired_hwnds:
                    del self.snoozed_hwnds[h]

                if is_yt_home:
                    if self._yt_homepage_since == 0.0:
                        self._yt_homepage_since = now
                else:
                    self._yt_homepage_since = 0.0

                is_snoozed = (hwnd in self.snoozed_hwnds)
                is_distracted = (category == "entertainment")
                trigger_barrier = False
                title_snippet = clean_title[:55] if clean_title else (raw_title[:50] or display_name)

                if is_distracted and (hwnd not in self.allowed_hwnds) and not is_snoozed:
                    # 12s homepage search grace period so user can type and open a lecture video
                    if is_yt_home and (now - self._yt_homepage_since < 12.0):
                        self.in_distraction = False
                    else:
                        self.current_distracted_hwnd = hwnd
                        self.last_distracted_key = app_key
                        self.last_distracted_title = clean_title or raw_title
                        if not self.in_distraction:
                            self.in_distraction = True
                            now_str = time.strftime("%H:%M:%S")
                            event = {
                                "app": display_name,
                                "title": title_snippet,
                                "time": now_str,
                                "duration": 1
                            }
                            self.distraction_events.append(dict(event))
                            self.session_events.append(dict(event))
                            if self.barrier_enabled and (now - self.last_distraction_time > 8):
                                self.last_distraction_time = now
                                trigger_barrier = True
                        else:
                            if self.distraction_events:
                                self.distraction_events[-1]["duration"] += 1
                            if self.session_events:
                                self.session_events[-1]["duration"] += 1
                else:
                    self.in_distraction = False

            if trigger_barrier and self.on_barrier_trigger:
                self.on_barrier_trigger(title_snippet, hwnd)

        except Exception:
            pass

    @staticmethod
    def _fmt_time(sec):
        mins = sec // 60
        rem_s = sec % 60
        if mins > 0 and rem_s > 0:
            return f"{mins} phút {rem_s} giây"
        elif mins > 0:
            return f"{mins} phút"
        return f"{rem_s} giây"

    def _build_purity_report(self, records_snapshot, tracked_snapshot, events_snapshot, fallback_logged_sec=0):
        sum_usage = sum(d.get("seconds", 0) for _, d in records_snapshot)
        actual_tracked = max(1, max(tracked_snapshot, sum_usage))

        deep_work_sec = 0
        online_study_sec = 0
        entertainment_sec = 0

        breakdown = []
        for key, data in sorted(records_snapshot, key=lambda x: x[1]["seconds"], reverse=True):
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

            breakdown.append({
                "key": key,
                "name": data["name"],
                "category": cat,
                "seconds": sec,
                "time_str": time_str,
                "percent": 0,
                "title": data.get("last_title", "")
            })

        if fallback_logged_sec > 0 and (deep_work_sec + online_study_sec) < fallback_logged_sec:
            diff = fallback_logged_sec - (deep_work_sec + online_study_sec)
            deep_work_sec += diff
            actual_tracked += diff
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
                    "name": "Focus Flow • Học Tập",
                    "category": "deep_work",
                    "seconds": deep_work_sec,
                    "time_str": f"{m}p {s}s" if m > 0 else f"{s}s",
                    "percent": 100,
                    "title": "Thời gian các ca học đã hoàn thành"
                })

        for b in breakdown:
            b["percent"] = min(100, max(0, int((b["seconds"] / max(1, actual_tracked)) * 100)))

        productive_sec = deep_work_sec + online_study_sec
        total_recorded = deep_work_sec + online_study_sec + entertainment_sec
        purity_percent = max(0, min(100, int((productive_sec / total_recorded) * 100))) if total_recorded > 0 else 100

        return {
            "purity_percent": purity_percent,
            "deep_work_seconds": deep_work_sec,
            "deep_work_str": self._fmt_time(deep_work_sec),
            "online_study_seconds": online_study_sec,
            "online_study_str": self._fmt_time(online_study_sec),
            "distracted_seconds": entertainment_sec,
            "distracted_str": self._fmt_time(entertainment_sec),
            "productive_str": self._fmt_time(productive_sec),
            "pure_str": self._fmt_time(productive_sec),
            "total_tracked_seconds": actual_tracked,
            "total_tracked_str": self._fmt_time(actual_tracked),
            "incident_count": len(events_snapshot),
            "allow_youtube_fb_study": self.allow_youtube_fb_study,
            "breakdown": breakdown,
            "events": events_snapshot
        }

    def get_session_purity_stats(self, total_focus_minutes=50):
        """Returns purity report for ONLY the active/current session."""
        with self._data_lock:
            records_snapshot = [(k, dict(v)) for k, v in self.session_records.items()]
            tracked_snapshot = self.session_total_seconds
            events_snapshot = [dict(e) for e in self.session_events]
        return self._build_purity_report(records_snapshot, tracked_snapshot, events_snapshot, fallback_logged_sec=0)

    def get_purity_stats(self, total_focus_minutes=50):
        """Returns accumulated daily purity report."""
        with self._data_lock:
            records_snapshot = [(k, dict(v)) for k, v in self.usage_records.items()]
            tracked_snapshot = self.total_tracked_seconds
            events_snapshot = [dict(e) for e in self.distraction_events]

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

        return self._build_purity_report(records_snapshot, tracked_snapshot, events_snapshot, fallback_logged_sec=today_logged_sec)

    def get_analytics_bundle(self, session_num=1, is_focus_active=False, total_focus_minutes=50):
        """Returns current session report, archived sessions list, and daily summary for Tab 3."""
        current_report = self.get_session_purity_stats(total_focus_minutes)
        current_report["session"] = int(session_num)
        current_report["start_time"] = self.session_start_time
        current_report["is_active"] = bool(is_focus_active)

        daily_report = self.get_purity_stats(total_focus_minutes)
        with self._data_lock:
            sessions_copy = [dict(s) for s in self.completed_sessions_today]

        return {
            "current_session": current_report,
            "sessions": sessions_copy,
            "daily": daily_report
        }
