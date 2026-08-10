"""
hardware.py
-----------
All GPIO / device logic lives here. app.py never touches pins directly —
it only calls the functions below.

Devices:
- "bluelight"   -> Room Light   (LED on GPIO, blue)
- "greenlight"  -> Hall Light   (LED on GPIO, green)
- "soundsystem" -> Sound System (TonalBuzzer on GPIO)
- "fan"         -> DC Motor
"""

import threading
import time
import atexit

# ----------------------------------------------------------------------
# CONFIG — adjust pin numbers to match your actual wiring
# ----------------------------------------------------------------------
SIMULATE = False  # Set True to test on a laptop without a Pi / GPIO access

# type is used by the frontend to pick icon + animation style
SWITCH_DEVICES = {
    "bluelight":   {"pin": 17, "name": "Room Light",   "type": "light-blue"},
    "greenlight":  {"pin": 27, "name": "Hall Light",   "type": "light-green"},
    "soundsystem": {"pin": 18, "name": "Sound System", "type": "sound"},
}

# DC motor pin (via relay or transistor)
DC_MOTOR_PIN = 12
FAN_NAME = "Fan"
FAN_TYPE = "fan"

# Mario Theme (Note, Duration in seconds)
MARIO_THEME = [
    ("E5", 0.15), ("E5", 0.15), (None, 0.15), ("E5", 0.15), (None, 0.15),
    ("C5", 0.15), ("E5", 0.15), (None, 0.15), ("G5", 0.3), (None, 0.3),
    ("G4", 0.3), (None, 0.3)
]

# ----------------------------------------------------------------------
# HARDWARE SETUP
# ----------------------------------------------------------------------
if not SIMULATE:
    from gpiozero import LED, OutputDevice, TonalBuzzer
    from gpiozero.tones import Tone

    _switches = {}
    for key, cfg in SWITCH_DEVICES.items():
        if key == "soundsystem":
            _switches[key] = TonalBuzzer(cfg["pin"])
        else:
            _switches[key] = LED(cfg["pin"])

    _fan_output = OutputDevice(DC_MOTOR_PIN)

    _jingle_thread = None
    _jingle_running = threading.Event()
    _jingle_state = False

    def _play_jingle():
        global _jingle_state
        buzzer = _switches["soundsystem"]
        for note, duration in MARIO_THEME:
            if not _jingle_running.is_set():
                break
            if note:
                buzzer.play(Tone(note))
            else:
                buzzer.stop()
            time.sleep(duration)
        buzzer.stop()
        _jingle_running.clear()
        _jingle_state = False

    def _switch_set(key, state):
        global _jingle_thread, _jingle_state
        if key == "soundsystem":
            if state and not _jingle_running.is_set():
                _jingle_state = True
                _jingle_running.set()
                _jingle_thread = threading.Thread(target=_play_jingle, daemon=True)
                _jingle_thread.start()
            elif not state and _jingle_running.is_set():
                _jingle_state = False
                _jingle_running.clear()
                if _jingle_thread:
                    _jingle_thread.join(timeout=1)
                _switches[key].stop()
        else:
            _switches[key].on() if state else _switches[key].off()

    def _switch_get(key):
        if key == "soundsystem":
            return _jingle_state
        return _switches[key].value == 1

    def _fan_set(state):
        _fan_output.on() if state else _fan_output.off()

    def _fan_get():
        return _fan_output.value == 1

    def _cleanup():
        _fan_set(False)
        _jingle_running.clear()
        if _jingle_thread:
            _jingle_thread.join(timeout=1)
        for sw in _switches.values():
            if hasattr(sw, 'stop'):
                sw.stop()
            sw.close()
        _fan_output.close()

    atexit.register(_cleanup)

else:
    _switch_state = {key: False for key in SWITCH_DEVICES}
    _fan_state = False
    
    _jingle_thread = None
    _jingle_running = threading.Event()

    def _sim_play_jingle():
        for note, duration in MARIO_THEME:
            if not _jingle_running.is_set():
                break
            time.sleep(duration)
        _jingle_running.clear()
        _switch_state["soundsystem"] = False
        print("[SIMULATE] Sound System -> FINISHED JINGLE")

    def _switch_set(key, state):
        global _jingle_thread
        _switch_state[key] = state
        print(f"[SIMULATE] {SWITCH_DEVICES[key]['name']} -> {'ON' if state else 'OFF'}")
        if key == "soundsystem":
            if state:
                _jingle_running.set()
                _jingle_thread = threading.Thread(target=_sim_play_jingle, daemon=True)
                _jingle_thread.start()
            else:
                _jingle_running.clear()

    def _switch_get(key):
        return _switch_state[key]

    def _fan_set(state):
        global _fan_state
        _fan_state = state
        print(f"[SIMULATE] {FAN_NAME} -> {'ON' if state else 'OFF'}")

    def _fan_get():
        return _fan_state


# ----------------------------------------------------------------------
# PUBLIC API — this is what app.py calls
# ----------------------------------------------------------------------

def list_devices():
    """Return {device_key: {"name": str, "type": str}} for every device."""
    devices = {
        key: {"name": cfg["name"], "type": cfg["type"]}
        for key, cfg in SWITCH_DEVICES.items()
    }
    devices["fan"] = {"name": FAN_NAME, "type": FAN_TYPE}
    return devices


def _get(key):
    if key == "fan":
        return _fan_get()
    if key in SWITCH_DEVICES:
        return _switch_get(key)
    raise KeyError(key)


def _set(key, state):
    if key == "fan":
        _fan_set(state)
    elif key in SWITCH_DEVICES:
        _switch_set(key, state)
    else:
        raise KeyError(key)
    return _get(key)


def get_all_states():
    """Return {device_key: bool} for every device."""
    return {key: _get(key) for key in list_devices()}


def toggle(key):
    """Flip a device's state. Raises KeyError if key is unknown."""
    return _set(key, not _get(key))


def set_state(key, state: bool):
    """Explicitly set a device on/off. Raises KeyError if key is unknown."""
    return _set(key, state)