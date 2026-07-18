"""
GPIO control plugin — on/off toggles for output pins (relays, LEDs, etc).

Edit GPIO_PINS below to match your wiring (BCM numbering). If gpiozero
isn't available (e.g. testing off-Pi), this runs in a mock mode so the UI
still works without throwing errors.
"""

from flask import jsonify

PLUGIN_ID = "gpio"

GPIO_PINS = {
    "Relay 1": 17,
    "Relay 2": 27,
    "LED": 22,
}

try:
    from gpiozero import OutputDevice
    devices = {name: OutputDevice(pin) for name, pin in GPIO_PINS.items()}
except Exception as e:
    print(f"[gpio plugin] gpiozero not available, running in mock mode: {e}")

    class FakeDevice:
        def __init__(self):
            self.value = 0

        def on(self):
            self.value = 1

        def off(self):
            self.value = 0

    devices = {name: FakeDevice() for name in GPIO_PINS}


def register_routes(app):
    @app.route(f"/api/{PLUGIN_ID}/state")
    def gpio_state():
        return jsonify({name: bool(dev.value) for name, dev in devices.items()})

    @app.route(f"/api/{PLUGIN_ID}/<name>/<action>", methods=["POST"])
    def gpio_control(name, action):
        if name not in devices:
            return jsonify({"error": "unknown pin"}), 404
        if action not in ("on", "off", "toggle"):
            return jsonify({"error": "invalid action"}), 400
        dev = devices[name]
        if action == "on":
            dev.on()
        elif action == "off":
            dev.off()
        elif action == "toggle":
            dev.off() if dev.value else dev.on()
        return jsonify({"name": name, "state": bool(dev.value)})


def card_context():
    """Values available inside this plugin's card.html."""
    return {"pins": list(GPIO_PINS)}
