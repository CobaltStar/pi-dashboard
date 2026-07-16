"""
Template for a new dashboard plugin.

Copy this file to plugins/your_project.py (drop the leading underscore),
fill in register_routes(), CARD_HTML, and SCRIPT, then deploy.
The dashboard auto-discovers and wires it up — no other file needs editing.

Naming: files starting with "_" are ignored by the loader (like this one),
so this file is never actually loaded itself. It's just a reference.
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


# HTML injected into the "Projects" grid on the dashboard.
# Keep it a self-contained <div class="proj-card">...</div> block.
CARD_HTML = """
<div class="proj-card" id="card-example">
  <div class="proj-title">🔧 Example Project</div>
  <div class="proj-body">
    <button class="btn" onclick="exampleDoThing()">Do Thing</button>
    <span id="example-msg" class="status-pill"></span>
  </div>
</div>
"""

# JS injected once at the bottom of the page. Prefix function/element names
# with your plugin name to avoid collisions with other plugins.
SCRIPT = """
async function exampleDoThing() {
  const msg = document.getElementById('example-msg');
  msg.textContent = 'Working…';
  try {
    await fetch('/api/example/do-thing', { method: 'POST' });
    msg.textContent = 'Done ✓';
  } catch (e) {
    msg.textContent = 'Failed';
  }
  setTimeout(() => msg.textContent = '', 3000);
}
"""
