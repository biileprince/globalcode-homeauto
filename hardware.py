"""
hardware.py
-----------
All GPIO / device logic lives here. app.py never touches pins directly —
it only calls the functions below.

Devices:
- "bluelight"   -> Room Light   (LED on GPIO, blue)
- "greenlight"  -> Hall Light   (LED on GPIO, green)
- "soundsystem" -> Sound System (relay/LED on GPIO)
- "fan"         -> DC Motor
"""

import time
import atexit

# ----------------------------------------------------------------------
# CONFIG — adjust pin numbers to match your actual wiring
# ----------------------------------------------------------------------
SIMULATE = False  # Set True to test on a laptop without a Pi / GPIO access

# type is used by the frontend to pick icon + animation style
SWITCH_DEVICES = {
    "bluelight":   {"pin": 17, "name": "Room Light",   "type": "light-blue", "active_high": True},
    "greenlight":  {"pin": 27, "name": "Hall Light",   "type": "light-green", "active_high": True},
    "soundsystem": {"pin": 22, "name": "Sound System", "type": "sound", "active_high": True},
    "fan":         {"pin": 12, "name": "Fan",          "type": "fan", "active_high": True},
}

# ----------------------------------------------------------------------
# SENSORS
# ----------------------------------------------------------------------
FLAME_SENSOR_PIN = 23

# ----------------------------------------------------------------------
# HARDWARE SETUP
# ----------------------------------------------------------------------
if not SIMULATE:
    from gpiozero import LED, DigitalInputDevice

    # Initialize all switches with their configured active_high state
    _switches = {key: LED(cfg["pin"], active_high=cfg.get("active_high", True)) for key, cfg in SWITCH_DEVICES.items()}

    # Initialize the flame sensor
    # Many LM393-based sensors output LOW when a flame is detected.
    _flame_sensor = DigitalInputDevice(FLAME_SENSOR_PIN, pull_up=True)
    _flame_alert = False

    def _flame_detected_handler():
        global _flame_alert
        # If pull_up=True, is_active is True when the pin is pulled LOW (flame detected)
        if _flame_sensor.is_active:
            _flame_alert = True
            print("\n🚨 [ALARM] Flame detected! Triggering sound system... 🚨\n")
            _switch_set("soundsystem", True)

    _flame_sensor.when_activated = _flame_detected_handler
    _flame_sensor.when_deactivated = _flame_detected_handler

    def _switch_set(key, state):
        global _flame_alert
        if key == "soundsystem" and not state:
            _flame_alert = False
        _switches[key].on() if state else _switches[key].off()

    def _switch_get(key):
        return _switches[key].value == 1

    def _cleanup():
        for sw in _switches.values():
            sw.close()
        _flame_sensor.close()

    atexit.register(_cleanup)

else:
    _switch_state = {key: False for key in SWITCH_DEVICES}
    _flame_alert = False
    
    # Simulate a fake background thread to occasionally "detect" a flame for testing
    def _sim_flame():
        global _flame_alert
        time.sleep(20)  # Wait 20 seconds, then simulate a flame
        _flame_alert = True
        print("\n🚨 [SIMULATE] Flame detected! Triggering sound system... 🚨\n")
        _switch_set("soundsystem", True)
        
    _sim_thread = threading.Thread(target=_sim_flame, daemon=True)
    _sim_thread.start()

    def _switch_set(key, state):
        global _flame_alert
        if key == "soundsystem" and not state:
            _flame_alert = False
        _switch_state[key] = state
        print(f"[SIMULATE] {SWITCH_DEVICES[key]['name']} -> {'ON' if state else 'OFF'}")

    def _switch_get(key):
        return _switch_state[key]


# ----------------------------------------------------------------------
# PUBLIC API — this is what app.py calls
# ----------------------------------------------------------------------

def list_devices():
    """Return {device_key: {"name": str, "type": str}} for every device."""
    devices = {
        key: {"name": cfg["name"], "type": cfg["type"]}
        for key, cfg in SWITCH_DEVICES.items()
    }
    return devices


def _get(key):
    if key in SWITCH_DEVICES:
        return _switch_get(key)
    raise KeyError(key)


def _set(key, state):
    if key in SWITCH_DEVICES:
        _switch_set(key, state)
    else:
        raise KeyError(key)
    return _get(key)


def get_all_states():
    """Return {device_key: bool} for every device."""
    states = {key: _get(key) for key in list_devices()}
    states["flame_alert"] = _flame_alert
    return states


def toggle(key):
    """Flip a device's state. Raises KeyError if key is unknown."""
    return _set(key, not _get(key))


def set_state(key, state: bool):
    """Explicitly set a device on/off. Raises KeyError if key is unknown."""
    return _set(key, state)