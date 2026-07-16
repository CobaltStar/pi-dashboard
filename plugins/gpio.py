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


_pin_rows = "".join(f"""
    <div class="pin-row">
      <span>{name}</span>
      <label class="switch">
        <input type="checkbox" data-pin="{name}" onchange="gpioToggle(this)">
        <span class="slider"></span>
      </label>
    </div>
""" for name in GPIO_PINS)

CARD_HTML = f"""
<div class="proj-card" id="card-gpio">
  <div class="proj-title">🔌 GPIO Pins</div>
  <div class="proj-body" style="flex-direction:column; align-items:stretch; gap:8px;">
    {_pin_rows}
  </div>
</div>
"""

SCRIPT = """
async function gpioRefresh() {
  try {
    const res = await fetch('/api/gpio/state');
    const states = await res.json();
    document.querySelectorAll('#card-gpio input[type=checkbox]').forEach(box => {
      const pin = box.getAttribute('data-pin');
      if (pin in states) box.checked = states[pin];
    });
  } catch (e) { console.error(e); }
}
async function gpioToggle(box) {
  const pin = box.getAttribute('data-pin');
  const action = box.checked ? 'on' : 'off';
  try {
    await fetch(`/api/gpio/${encodeURIComponent(pin)}/${action}`, { method: 'POST' });
  } catch (e) {
    box.checked = !box.checked;
  }
}
gpioRefresh();
"""
