"""
Wake-on-LAN plugin — send a magic packet to wake your desktop PC.

Setup:
  1. Enable Wake-on-LAN in your desktop's BIOS/UEFI and OS network adapter settings.
  2. Set WOL_TARGET_MAC in the Pi's env file (~/secrets/pi-dashboard.env) to
     your desktop's MAC address (`ipconfig /all` on Windows, `ip link` on Linux).
  3. The Pi and desktop need to be on the same local network/broadcast domain.
"""

import os
import socket
from flask import jsonify

PLUGIN_ID = "wol"

# Set in the env file, not here — MAC addresses don't belong in the repo
TARGET_MAC = os.environ.get("WOL_TARGET_MAC", "")


def send_magic_packet(mac: str):
    mac_bytes = bytes.fromhex(mac.replace(":", "").replace("-", ""))
    packet = b"\xff" * 6 + mac_bytes * 16
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.sendto(packet, ("255.255.255.255", 9))
    sock.close()


def register_routes(app):
    @app.route(f"/api/{PLUGIN_ID}/wake", methods=["POST"])
    def wake():
        if not TARGET_MAC:
            return jsonify({"error": "WOL_TARGET_MAC is not set in the env file"}), 500
        try:
            send_magic_packet(TARGET_MAC)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        return jsonify({"ok": True})


# UI lives in card.html and script.js in this folder
