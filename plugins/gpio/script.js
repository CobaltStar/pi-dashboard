async function gpioRefresh() {
  try {
    const res = await fetch('/api/gpio/state');
    const states = await res.json();
    document.querySelectorAll('#card-gpio input[type=checkbox]').forEach(box => {
      const pin = box.getAttribute('data-pin');
      if (pin in states) box.checked = states[pin];
    });
  } catch (e) { console.error(e); }
}
async function gpioToggle(box) {
  const pin = box.getAttribute('data-pin');
  const action = box.checked ? 'on' : 'off';
  try {
    await fetch(`/api/gpio/${encodeURIComponent(pin)}/${action}`, { method: 'POST' });
  } catch (e) {
    box.checked = !box.checked;
  }
}
gpioRefresh();
