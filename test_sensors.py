import RPi.GPIO as GPIO
import time

FLAME_PIN = 23
GAS_PIN = 24

GPIO.setmode(GPIO.BCM)
GPIO.setup(FLAME_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(GAS_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

print("Starting sensor test... Press CTRL+C to quit.")
print("Printing values every second...\n")

try:
    while True:
        flame_val = GPIO.input(FLAME_PIN)
        gas_val = GPIO.input(GAS_PIN)
        print(f"[{time.strftime('%H:%M:%S')}] Flame = {'HIGH (1)' if flame_val else 'LOW (0)'}  | Gas = {'HIGH (1)' if gas_val else 'LOW (0)'}")
        time.sleep(1)
except KeyboardInterrupt:
    GPIO.cleanup()
    print("Done.")
