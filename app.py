"""
app.py
-------
Flask web layer ONLY. This file knows nothing about GPIO, stepper
sequences, or pin numbers — it just exposes hardware.py's functions
over HTTP. All device logic lives in hardware.py.
"""

from flask import Flask, render_template, jsonify
import hardware

app = Flask(__name__)


@app.route("/")
def index():
    devices = hardware.list_devices()
    states = hardware.get_all_states()
    return render_template("index.html", devices=devices, states=states)


@app.route("/api/status")
def status():
    return jsonify(hardware.get_all_states())


@app.route("/api/toggle/<device_key>", methods=["POST"])
def toggle_device(device_key):
    try:
        new_state = hardware.toggle(device_key)
    except KeyError:
        return jsonify({"error": "unknown device"}), 404
    return jsonify({device_key: new_state})


@app.route("/api/set/<device_key>/<state>", methods=["POST"])
def set_device(device_key, state):
    if state not in ("on", "off"):
        return jsonify({"error": "state must be 'on' or 'off'"}), 400
    try:
        new_state = hardware.set_state(device_key, state == "on")
    except KeyError:
        return jsonify({"error": "unknown device"}), 404
    return jsonify({device_key: new_state})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)