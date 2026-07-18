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
