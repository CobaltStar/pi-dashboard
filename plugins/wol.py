"""
Wake-on-LAN plugin — send a magic packet to wake your desktop PC.

Setup:
  1. Enable Wake-on-LAN in your desktop's BIOS/UEFI and OS network adapter settings.
  2. Set TARGET_MAC below to your desktop's MAC address (`ipconfig /all` on
     Windows, `ip link` on Linux).
  3. The Pi and desktop need to be on the same local network/broadcast domain.
"""

import socket
from flask import jsonify

PLUGIN_ID = "wol"

# EDIT ME: your desktop's MAC address
TARGET_MAC = "AA:BB:CC:DD:EE:FF"


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
        try:
            send_magic_packet(TARGET_MAC)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        return jsonify({"ok": True})


CARD_HTML = """
<div class="proj-card" id="card-wol">
  <div class="proj-title">🖥️ Desktop PC</div>
  <div class="proj-body">
    <button class="btn" onclick="wakeDesktop()">Wake on LAN</button>
    <span id="wol-msg" class="status-pill"></span>
  </div>
</div>
"""

SCRIPT = """
async function wakeDesktop() {
  const msg = document.getElementById('wol-msg');
  msg.textContent = 'Sending…';
  try {
    await fetch('/api/wol/wake', { method: 'POST' });
    msg.textContent = 'Packet sent ✓';
  } catch (e) {
    msg.textContent = 'Failed';
  }
  setTimeout(() => msg.textContent = '', 3000);
}
"""
