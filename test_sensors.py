from gpiozero import InputDevice
import time

FLAME_PIN = 23
GAS_PIN = 24

# Flame: NO pull_up (per SunFounder docs). is_active=True -> NO flame, False -> FLAME!
# Gas: pull_up=True. is_active=True -> GAS DETECTED
flame = InputDevice(FLAME_PIN)
gas = InputDevice(GAS_PIN, pull_up=True)

print("Starting sensor test (using gpiozero)... Press CTRL+C to quit.")
print("Flame: is_active=True means SAFE, False means FLAME DETECTED")
print("Gas:   is_active=True means GAS DETECTED, False means SAFE\n")

try:
    while True:
        f = flame.is_active
        g = gas.is_active
        flame_status = "🔥 FLAME!" if not f else "Safe"
        gas_status = "☁️ GAS!" if g else "Safe"
        print(f"[{time.strftime('%H:%M:%S')}] Flame: {flame_status} (is_active={f})  | Gas: {gas_status} (is_active={g})")
        time.sleep(1)
except KeyboardInterrupt:
    flame.close()
    gas.close()
    print("Done.")
