# Raspberry Pi Light & Fan Controller (Breadboard Prototype)

Web app to remotely control a breadboard prototype:
- **Lights** = 2 LEDs wired directly to GPIO
- **Fan** = 28BYJ-48 stepper motor via a ULN2003 driver board

This is a prototype stage before wiring real mains-powered lights/fans
through relays — once this works, swap the LEDs for a relay module
switching real AC lights, and reuse the same Flask app structure.

## 0. File structure

```
pi-light-fan-control/
├── app.py          ← Flask routes ONLY (no GPIO code at all)
├── hardware.py      ← All GPIO / stepper / LED logic (no Flask code at all)
├── templates/
│   └── index.html
├── static/
│   ├── style.css
│   └── app.js
└── requirements.txt
```

`hardware.py` exposes a small public API — `list_devices()`,
`get_state()`, `set_state()`, `toggle()`, `get_all_states()` — and
`app.py` just calls into it. This means:
- You can test/run `hardware.py` on its own (e.g. a quick script that
  imports it and blinks an LED) without starting Flask at all.
- You can swap in different hardware later (real relays, different
  pins, a different motor) by only editing `hardware.py` — the Flask
  routes never change.
- If you ever want a different frontend (CLI, Telegram bot, etc.) it
  can reuse `hardware.py` directly instead of going through HTTP.

## 1. Wiring

**LEDs (lights):**

| Raspberry Pi | LED |
|---|---|
| GPIO17 (via 220–330Ω resistor) | Light 1 anode (long leg) |
| GPIO27 (via 220–330Ω resistor) | Light 2 anode (long leg) |
| GND | Both LED cathodes (short leg) |

**Stepper motor (fan) — via ULN2003 driver board:**

| Raspberry Pi | ULN2003 board |
|---|---|
| 5V | VCC |
| GND | GND |
| GPIO5  | IN1 |
| GPIO6  | IN2 |
| GPIO13 | IN3 |
| GPIO19 | IN4 |

The stepper motor itself plugs into the ULN2003 board via its white
5-pin connector — you don't wire the motor to the Pi directly. The
Pi only talks to the driver board, which supplies the current the
motor needs.

⚠️ **Important:** the pin numbers above are what the code expects —
double check they match how you actually wired your breadboard (from
your photo I can see jumpers going into the Pi's GPIO header, but
can't confirm the exact pin numbers). If your wiring differs, just
update `LED_DEVICES` and `STEPPER_PINS` at the top of `app.py` to
match.

**Later, moving to real appliances:** when you're ready to switch real
mains-powered lights/fans, replace the LEDs with a relay module (see
the earlier version of this guide) — the GPIO/Flask logic stays
almost identical, you're just switching what's on the other end of
the pin.

## 2. Install (on the Raspberry Pi)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Clone/copy this project onto the Pi, then:
cd pi-light-fan-control

# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 3. Run

```bash
python3 app.py
```

Find your Pi's IP address with `hostname -I`, then from any phone/laptop
on the same WiFi network, visit:

```
http://<raspberry-pi-ip>:5000
```

You'll see toggle switches for each device.

## 4. Testing without a Pi

If you want to build/test the Flask app on your laptop before deploying
to the Pi, open `app.py` and set:

```python
SIMULATE = True
```

This skips GPIO entirely and just logs actions to the console, so you
can develop the web UI first and wire the hardware later.

## 5. Run automatically on boot (optional)

Create a systemd service so the app starts whenever the Pi powers on:

```bash
sudo nano /etc/systemd/system/light-fan-control.service
```

```ini
[Unit]
Description=Light and Fan Control Flask App
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/pi-light-fan-control
ExecStart=/home/pi/pi-light-fan-control/venv/bin/python3 app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable light-fan-control
sudo systemctl start light-fan-control
```

## 6. Adding more devices

To add another LED, extend `LED_DEVICES` in `app.py`:

```python
LED_DEVICES = {
    "light1": {"pin": 17, "name": "Red LED (Light 1)"},
    "light2": {"pin": 27, "name": "Green LED (Light 2)"},
    "light3": {"pin": 22, "name": "Blue LED (Light 3)"},
}
```

The routes and frontend loop over devices automatically — no other
code changes needed. There's only one stepper motor in this setup, so
`STEPPER_PINS` doesn't need a dict — just update the 4 pin numbers if
you rewire it.

## 7. Ideas for extending this project

- **Authentication**: add a login page (Flask-Login) so only you can
  control the switches, especially if exposing this beyond your home network.
- **Scheduling**: add cron-like scheduled on/off times (e.g. `APScheduler`).
- **HTTPS + remote access**: use a reverse proxy (nginx) + dynamic DNS,
  or a service like Tailscale, to control devices securely from outside
  your home network — avoid exposing Flask's dev server directly to the internet.
- **Voice control**: integrate with Google Assistant/Alexa via a
  smart-home skill bridge.
- **Physical override switch**: wire a physical push button to a GPIO
  input pin so the light can also be toggled manually; sync state with
  the app on each button press.
- **Sensors**: add a PIR motion sensor or LDR (light sensor) for
  automatic control, in addition to manual override from the app.
