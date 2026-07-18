"""
Template for a new dashboard plugin.

A plugin is one self-contained folder under plugins/:
    plugins/your_project/
        __init__.py   — routes + logic (this file)
        card.html     — the card shown in the Projects grid (Jinja template)
        script.js     — the card's JavaScript (optional)

Copy this whole folder, rename it (drop the leading underscore), and fill
in the three files. The dashboard auto-discovers and wires it up — no
other file needs editing.

If your card needs dynamic values, define card_context() returning a
dict; it becomes the Jinja context for card.html (see the gpio plugin).

Naming: folders starting with "_" are ignored by the loader (like this
one), so this plugin is never actually loaded itself. It's just a reference.
"""

from flask import jsonify

PLUGIN_ID = "example"  # used to namespace your API routes, e.g. /api/example/...


def register_routes(app):
    """Attach whatever Flask routes your project needs."""

    @app.route(f"/api/{PLUGIN_ID}/status")
    def example_status():
        return jsonify({"status": "ok"})

    @app.route(f"/api/{PLUGIN_ID}/do-thing", methods=["POST"])
    def example_do_thing():
        # ... do the thing ...
        return jsonify({"ok": True})
