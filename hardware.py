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
import threading
import requests

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
GAS_SENSOR_PIN = 24
NTFY_URL = "http://ntfy.sh/on_button_press_prince"

# ----------------------------------------------------------------------
# HARDWARE SETUP
# ----------------------------------------------------------------------
if not SIMULATE:
    from gpiozero import LED, InputDevice
    import RPi.GPIO as GPIO

    # Set up RPi.GPIO mode
    GPIO.setmode(GPIO.BCM)

    # Initialize all switches with their configured active_high state
    _switches = {key: LED(cfg["pin"], active_high=cfg.get("active_high", True)) for key, cfg in SWITCH_DEVICES.items()}

    # Initialize the flame sensor using RPi.GPIO
    GPIO.setup(FLAME_SENSOR_PIN, GPIO.IN)

    # Initialize the gas sensor using gpiozero
    _gas_sensor = InputDevice(GAS_SENSOR_PIN, pull_up=True)
    _alarm_active = False
    _alarm_reason = ""

    def _poll_sensors():
        global _alarm_active, _alarm_reason
        last_flame = None
        last_gas = None
        while True:
            # .is_active correctly accounts for pull_up inversion:
            #   idle (physical HIGH) -> is_active = False
            #   triggered (physical LOW) -> is_active = True
            flame_state = GPIO.input(FLAME_SENSOR_PIN)
            gas_active = _gas_sensor.is_active

            # Debug print if the sensor state changes
            if flame_state != last_flame or gas_active != last_gas:
                print(f"[DEBUG SENSORS] Flame state = {'HIGH (No flame)' if flame_state == GPIO.HIGH else 'LOW (Flame)'} | Gas is_active = {gas_active}")
                last_flame = flame_state
                last_gas = gas_active

            flame_detected = (flame_state == GPIO.LOW)
            gas_detected = gas_active

            if (flame_detected or gas_detected) and not _alarm_active:
                _alarm_active = True
                _alarm_reason = "🔥 FLAME DETECTED" if flame_detected else "☁️ GAS DETECTED"
                
                print(f"\n🚨 [ALARM] {_alarm_reason}! Triggering sound system... 🚨\n")
                _switch_set("soundsystem", True)
                
                # Send IoT Push Notification
                try:
                    r = requests.post(
                        NTFY_URL, 
                        data=f"🚨 ALARM: {_alarm_reason} in the house! 🚨".encode('utf-8'),
                        headers={"Title": "Home Automation Alert", "Priority": "urgent", "Tags": "fire,warning"},
                        timeout=5
                    )
                    print(f"Sent ntfy push notification: {r.status_code}")
                except Exception as e:
                    print(f"Failed to send ntfy notification: {e}")

            time.sleep(0.1)

    _sensor_thread = threading.Thread(target=_poll_sensors, daemon=True)
    _sensor_thread.start()

    def _switch_set(key, state):
        global _alarm_active, _alarm_reason
        if key == "soundsystem" and not state:
            _alarm_active = False
            _alarm_reason = ""
        _switches[key].on() if state else _switches[key].off()

    def _switch_get(key):
        return _switches[key].value == 1

    def _cleanup():
        for sw in _switches.values():
            sw.close()
        _gas_sensor.close()
        # No need to explicitly close flame since RPi.GPIO cleanup is usually handled by atexit on the script level,
        # but we can optionally reset it.

    atexit.register(_cleanup)

else:
    _switch_state = {key: False for key in SWITCH_DEVICES}
    _alarm_active = False
    _alarm_reason = ""
    
    # Simulate a fake background thread to occasionally "detect" a gas leak for testing
    def _sim_sensors():
        global _alarm_active, _alarm_reason
        time.sleep(20)  # Wait 20 seconds, then simulate gas
        _alarm_active = True
        _alarm_reason = "☁️ GAS DETECTED"
        print(f"\n🚨 [SIMULATE] {_alarm_reason}! Triggering sound system... 🚨\n")
        _switch_set("soundsystem", True)
        
        # Send IoT Push Notification
        try:
            r = requests.post(
                NTFY_URL, 
                data=f"🚨 ALARM (SIMULATED): {_alarm_reason} in the house! 🚨".encode('utf-8'),
                headers={"Title": "Home Automation Alert", "Priority": "urgent", "Tags": "fire,warning"},
                timeout=5
            )
            print(f"Sent ntfy push notification: {r.status_code}")
        except Exception as e:
            print(f"Failed to send ntfy notification: {e}")
        
    _sim_thread = threading.Thread(target=_sim_sensors, daemon=True)
    _sim_thread.start()

    def _switch_set(key, state):
        global _alarm_active, _alarm_reason
        if key == "soundsystem" and not state:
            _alarm_active = False
            _alarm_reason = ""
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
    states["alarm_active"] = _alarm_active
    states["alarm_reason"] = _alarm_reason
    return states


def toggle(key):
    """Flip a device's state. Raises KeyError if key is unknown."""
    return _set(key, not _get(key))


def set_state(key, state: bool):
    """Explicitly set a device on/off. Raises KeyError if key is unknown."""
    return _set(key, state)


def dismiss_alarm():
    """Clear the global alarm state and turn off the sound system."""
    global _alarm_active, _alarm_reason
    _alarm_active = False
    _alarm_reason = ""
    if "soundsystem" in SWITCH_DEVICES:
        _switch_set("soundsystem", False)
    return {"status": "dismissed"}