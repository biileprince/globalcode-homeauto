import RPi.GPIO as GPIO
import time

FLAME_PIN = 23
GAS_PIN = 24

GPIO.setmode(GPIO.BCM)
GPIO.setup(FLAME_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(GAS_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

print("Starting sensor test... Press CTRL+C to quit.")
print("Waiting for changes...")

last_flame = None
last_gas = None

try:
    while True:
        flame_val = GPIO.input(FLAME_PIN)
        gas_val = GPIO.input(GAS_PIN)
        
        if flame_val != last_flame or gas_val != last_gas:
            print(f"[{time.strftime('%H:%M:%S')}] Flame Pin = {'HIGH (1)' if flame_val else 'LOW (0)'} | Gas Pin = {'HIGH (1)' if gas_val else 'LOW (0)'}")
            last_flame = flame_val
            last_gas = gas_val
            
        time.sleep(0.1)
except KeyboardInterrupt:
    GPIO.cleanup()
    print("Done.")
