import json
import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(ROOT_DIR, 'config.json')

DEFAULT_CONFIG = {
    "focus_minutes": 50,
    "break_minutes": 10,
    "enforcement_mode": "overlay",  # "overlay", "screen_off", "lock"
    "sound_enabled": True,
    "hardcore_mode": True,          # Strict anti-cheat (cannot exit during 7' break)
    "split_break_enabled": True,    # 7 mins strict lock + 3 mins prep mode
    "prep_minutes": 3,
    "auto_loop": True,              # Auto start next focus session without manual click
    "target_sessions": 3,           # Target number of pomodoro sessions in one study sitting
    "friction_barrier_enabled": True, # Idea 1: 3-Second Friction Barrier on distractions
    "purity_report_enabled": True,   # Idea 2: Honest Distraction Log & Purity Report
    "spotlight_enabled": False,      # Idea 3: Cinema Dimmer Mode (F9 to toggle)
    "completed_sessions": 0,
    "total_focus_minutes": 0
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            merged = DEFAULT_CONFIG.copy()
            merged.update(data)
            return merged
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(cfg):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving config: {e}")
