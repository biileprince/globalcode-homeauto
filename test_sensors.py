import RPi.GPIO as GPIO
import time

# Test a range of GPIO pins to find where the flame sensor signal actually is
TEST_PINS = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27]

# These pins are already used by our devices - mark them
USED_PINS = {17: "bluelight", 27: "greenlight", 22: "soundsystem", 12: "fan", 24: "gas_sensor"}

GPIO.setmode(GPIO.BCM)

active_pins = []
for pin in TEST_PINS:
    try:
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        active_pins.append(pin)
    except Exception as e:
        pass

print(f"Scanning {len(active_pins)} GPIO pins... Press CTRL+C to quit.")
print("Showing pins that read LOW (0) - potential flame sensor signal\n")

try:
    while True:
        low_pins = []
        for pin in active_pins:
            val = GPIO.input(pin)
            if val == 0:
                label = USED_PINS.get(pin, "")
                low_pins.append(f"GPIO{pin}{'(' + label + ')' if label else ''}")
        
        if low_pins:
            print(f"[{time.strftime('%H:%M:%S')}] LOW pins: {', '.join(low_pins)}")
        else:
            print(f"[{time.strftime('%H:%M:%S')}] All pins HIGH")
        time.sleep(1)
except KeyboardInterrupt:
    GPIO.cleanup()
    print("Done.")
