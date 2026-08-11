from gpiozero import InputDevice
import time

FLAME_PIN = 23
GAS_PIN = 24

flame = InputDevice(FLAME_PIN, pull_up=True)
gas = InputDevice(GAS_PIN, pull_up=True)

print("Starting sensor test (using gpiozero)... Press CTRL+C to quit.")
print("is_active = True means TRIGGERED, False means IDLE\n")

try:
    while True:
        print(f"[{time.strftime('%H:%M:%S')}] Flame is_active = {flame.is_active}  | Gas is_active = {gas.is_active}")
        time.sleep(1)
except KeyboardInterrupt:
    flame.close()
    gas.close()
    print("Done.")
