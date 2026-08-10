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
    "soundsystem": {"pin": 22, "name": "Sound System", "type": "sound"},
}

# DC motor pin (via relay or transistor)
DC_MOTOR_PIN = 12
FAN_NAME = "Fan"
FAN_TYPE = "fan"

# ----------------------------------------------------------------------
# HARDWARE SETUP
# ----------------------------------------------------------------------
if not SIMULATE:
    from gpiozero import LED, OutputDevice

    _switches = {key: LED(cfg["pin"]) for key, cfg in SWITCH_DEVICES.items()}

    _fan_output = OutputDevice(DC_MOTOR_PIN)

    def _switch_set(key, state):
        _switches[key].on() if state else _switches[key].off()

    def _switch_get(key):
        return _switches[key].value == 1

    def _fan_set(state):
        _fan_output.on() if state else _fan_output.off()

    def _fan_get():
        return _fan_output.value == 1

    def _cleanup():
        _fan_set(False)
        for sw in _switches.values():
            sw.close()
        _fan_output.close()

    atexit.register(_cleanup)

else:
    _switch_state = {key: False for key in SWITCH_DEVICES}
    _fan_state = False

    def _switch_set(key, state):
        _switch_state[key] = state
        print(f"[SIMULATE] {SWITCH_DEVICES[key]['name']} -> {'ON' if state else 'OFF'}")

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