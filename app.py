"""
Raspberry Pi Web Dashboard - Core App
--------------------------------------
Serves:
  - Live system monitoring (CPU %, temp, memory, disk, uptime)
  - A "Projects" section built dynamically from plugins/ — each plugin
    contributes its own API routes + a UI card, so adding a new project
    never requires touching this file.

To add a new project: drop a new .py file in plugins/ following the
pattern in plugins/_example.py, then git push. That's it.

Run with:
    python3 app.py
Then visit:
    http://<pi-ip-address>:5000
"""

import importlib
import os
import pkgutil
import subprocess
import time

from flask import Flask, jsonify, render_template
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import check_password_hash, generate_password_hash
import psutil

import plugins

app = Flask(__name__)
auth = HTTPBasicAuth()

# ---------------------------------------------------------------------------
# AUTH
# ---------------------------------------------------------------------------
# Credentials come from environment variables (set in .env, never committed).
# Every route in this app is protected — required once this is reachable
# from outside your home network.
DASH_USER = os.environ.get("DASH_USER", "admin")
DASH_PASSWORD_HASH = generate_password_hash(os.environ.get("DASH_PASSWORD", "changeme"))


@auth.verify_password
def verify_password(username, password):
    if username == DASH_USER and check_password_hash(DASH_PASSWORD_HASH, password):
        return username
    return None


loaded_plugins = []


def load_plugins():
    """Import every module in plugins/ and let it register its own routes."""
    for _, modname, _ in pkgutil.iter_modules(plugins.__path__):
        if modname.startswith("_"):
            continue  # skip _example.py, __init__.py, etc.
        try:
            module = importlib.import_module(f"plugins.{modname}")
            if hasattr(module, "register_routes"):
                module.register_routes(app)
            loaded_plugins.append(module)
            print(f"[plugins] loaded: {modname}")
        except Exception as e:
            print(f"[plugins] FAILED to load {modname}: {e}")


load_plugins()


@app.before_request
@auth.login_required
def require_auth():
    """Protect every route in the app, including plugin routes registered by
    load_plugins() above — plugins never need to know auth exists."""
    pass


# ---------------------------------------------------------------------------
# CORE SYSTEM STATS (always available, not a plugin)
# ---------------------------------------------------------------------------
def get_cpu_temp():
    try:
        out = subprocess.check_output(["vcgencmd", "measure_temp"]).decode()
        return float(out.split("=")[1].split("'")[0])
    except Exception:
        try:
            with open("/sys/class/thermal/thermal_zone0/temp") as f:
                return round(int(f.read().strip()) / 1000, 1)
        except Exception:
            return None


@app.route("/api/stats")
def api_stats():
    cpu_percent = psutil.cpu_percent(interval=0.3)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    uptime_seconds = time.time() - psutil.boot_time()

    return jsonify({
        "cpu_percent": cpu_percent,
        "cpu_temp": get_cpu_temp(),
        "mem_percent": mem.percent,
        "mem_used_gb": round(mem.used / (1024 ** 3), 2),
        "mem_total_gb": round(mem.total / (1024 ** 3), 2),
        "disk_percent": disk.percent,
        "disk_used_gb": round(disk.used / (1024 ** 3), 2),
        "disk_total_gb": round(disk.total / (1024 ** 3), 2),
        "uptime_hours": round(uptime_seconds / 3600, 1),
    })


@app.route("/")
def index():
    cards = "".join(getattr(m, "CARD_HTML", "") for m in loaded_plugins)
    scripts = "".join(getattr(m, "SCRIPT", "") for m in loaded_plugins)
    return render_template("index.html", project_cards=cards, project_scripts=scripts)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
