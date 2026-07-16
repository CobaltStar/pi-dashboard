"""
Pi-hole plugin — toggle ad-blocking on/off from the dashboard.

Requires:
  - Pi-hole installed on this same Pi (uses the `pihole` CLI)
  - A sudoers rule allowing the dashboard's user to run `pihole` without a
    password prompt (see README.md "Pi-hole plugin setup" section), e.g.:

      pi ALL=(ALL) NOPASSWD: /usr/local/bin/pihole

    Run `which pihole` to confirm the exact path on your system.
"""

import subprocess
from flask import jsonify

PLUGIN_ID = "pihole"


def register_routes(app):
    @app.route(f"/api/{PLUGIN_ID}/status")
    def pihole_status():
        try:
            out = subprocess.check_output(
                ["pihole", "status"], stderr=subprocess.STDOUT
            ).decode().lower()
            enabled = "disabled" not in out
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        return jsonify({"enabled": enabled})

    @app.route(f"/api/{PLUGIN_ID}/<action>", methods=["POST"])
    def pihole_toggle(action):
        if action not in ("enable", "disable"):
            return jsonify({"error": "invalid action"}), 400
        try:
            subprocess.check_call(["sudo", "pihole", action])
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        return jsonify({"ok": True, "action": action})


CARD_HTML = """
<div class="proj-card" id="card-pihole">
  <div class="proj-title">🕳️ Pi-hole</div>
  <div class="proj-body">
    <span id="pihole-status" class="status-pill">checking…</span>
    <label class="switch">
      <input type="checkbox" id="pihole-toggle" onchange="piholeToggle(this)">
      <span class="slider"></span>
    </label>
  </div>
</div>
"""

SCRIPT = """
async function piholeRefresh() {
  try {
    const res = await fetch('/api/pihole/status');
    const d = await res.json();
    document.getElementById('pihole-toggle').checked = d.enabled;
    document.getElementById('pihole-status').textContent = d.enabled ? 'Active' : 'Blocking paused';
  } catch (e) { console.error(e); }
}
async function piholeToggle(box) {
  const action = box.checked ? 'enable' : 'disable';
  await fetch(`/api/pihole/${action}`, { method: 'POST' });
  piholeRefresh();
}
piholeRefresh();
setInterval(piholeRefresh, 5000);
"""
