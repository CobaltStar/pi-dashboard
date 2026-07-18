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
