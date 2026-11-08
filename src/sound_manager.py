import os
import wave
import struct
import math
import winsound

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOUNDS_DIR = os.path.join(ROOT_DIR, 'sounds')

def ensure_sounds():
    os.makedirs(SOUNDS_DIR, exist_ok=True)
    break_file = os.path.join(SOUNDS_DIR, 'break_start.wav')
    focus_file = os.path.join(SOUNDS_DIR, 'focus_start.wav')
    
    if not os.path.exists(break_file):
        _generate_sound(break_file, [
            (698.46, 0.0, 0.7, 0.35),  # F5
            (587.33, 0.22, 0.8, 0.35), # D5
            (440.00, 0.45, 1.2, 0.40)  # A4 (Calm, resting tone)
        ], duration=1.7)
        
    if not os.path.exists(focus_file):
        _generate_sound(focus_file, [
            (523.25, 0.0, 0.5, 0.3),   # C5
            (659.25, 0.16, 0.5, 0.3),  # E5
            (783.99, 0.32, 0.6, 0.35), # G5
            (1046.50, 0.48, 1.1, 0.4)  # C6 (Energizing chord)
        ], duration=1.7)

def _generate_sound(filepath, notes, duration=1.7, sample_rate=44100):
    num_samples = int(duration * sample_rate)
    with wave.open(filepath, 'w') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        frames = bytearray()
        
        for i in range(num_samples):
            t = float(i) / sample_rate
            sample_val = 0.0
            for freq, start_t, note_dur, amp in notes:
                if start_t <= t < start_t + note_dur:
                    rel_t = t - start_t
                    envelope = math.sin(math.pi * min(1.0, rel_t / 0.04)) * math.exp(-3.5 * rel_t / note_dur)
                    sample_val += math.sin(2.0 * math.pi * freq * rel_t) * envelope * amp
            
            sample_val = max(-1.0, min(1.0, sample_val))
            sample_int = int(sample_val * 32767.0)
            frames.extend(struct.pack('<h', sample_int))
        wav.writeframes(frames)

import threading
import ctypes

def set_sound_volume(vol_pct):
    """Sets system waveOut volume (0-100%) for notification sounds."""
    try:
        pct = max(0, min(100, int(vol_pct)))
        vol_16 = int(65535 * (pct / 100.0))
        dw_volume = (vol_16 << 16) | (vol_16 & 0xFFFF)
        ctypes.windll.winmm.waveOutSetVolume(0, dw_volume)
    except Exception:
        pass

def play_break_sound():
    def _run():
        ensure_sounds()
        path = os.path.join(SOUNDS_DIR, 'break_start.wav')
        try:
            winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception:
            try:
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            except Exception:
                pass
    threading.Thread(target=_run, daemon=True).start()

def play_focus_sound():
    def _run():
        ensure_sounds()
        path = os.path.join(SOUNDS_DIR, 'focus_start.wav')
        try:
            winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception:
            try:
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            except Exception:
                pass
    threading.Thread(target=_run, daemon=True).start()
