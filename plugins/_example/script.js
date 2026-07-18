// Loaded once at the bottom of the page. Prefix function/element names with
// your plugin name to avoid collisions with other plugins.
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
