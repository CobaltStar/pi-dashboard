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


# UI lives in card.html and script.js in this folder
