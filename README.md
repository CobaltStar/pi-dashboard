# Pi Dashboard

A Flask web UI for your Raspberry Pi: live system stats (CPU %, temp, memory,
disk, uptime) plus a **Projects** section where each project (Pi-hole toggle,
Wake-on-LAN, GPIO control, whatever you build next) is a self-contained
plugin. Runs in Docker. GitHub is the source of truth — a self-hosted GitHub
Actions runner on the Pi rebuilds and redeploys on every push, so day-to-day
deploys are just `git push origin main`.

## Architecture

```
pi-dashboard/
  app.py                  # core: stats API + plugin loader + auth
  plugins/                # one folder per project — drop a folder in, git push
    _example/             # reference plugin — copy this folder to start
      __init__.py         #   routes + logic
      card.html           #   UI card (Jinja template)
      script.js           #   card JS (optional)
    gpio/
    pihole/
    wol/
  templates/index.html    # stats page; stitches in project cards + script tags
  Dockerfile
  docker-compose.yml
  .env.example            # template for the Pi's real env file (see setup)
  .github/workflows/deploy.yml  # runs on the Pi's runner on every push to main
```

### Adding a new project

1. Copy `plugins/_example/` to `plugins/your_project/`.
2. Fill in the three files: `__init__.py` (API routes in
   `register_routes(app)`, plus an optional `card_context()` returning the
   dict your template needs), `card.html` (the UI card, a Jinja template),
   and `script.js` (its JS, optional).
3. `git push origin main` — the runner redeploys automatically.

Nothing else needs editing — the loader in `app.py` auto-discovers every
folder in `plugins/`, stitches its card into the dashboard, and serves its
script at `/plugins/<name>/script.js`. Folders starting with `_` are skipped.

## First-time setup

### 1. On the Pi: install Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# log out and back in for the group change to take effect
```

### 2. Push this repo to GitHub

Create an empty repo on GitHub, then:
```bash
git remote add origin git@github.com:<you>/pi-dashboard.git
git push -u origin main
```

### 3. On the Pi: set up the GitHub Actions runner

On GitHub: repo → **Settings → Actions → Runners → New self-hosted runner**,
pick **Linux**, and follow the download/config commands it shows. Two
Pi-specific gotchas:

- **Pick the ARM download, not ARM64**, if you're on 32-bit Raspberry Pi OS.
  `uname -m` saying `aarch64` is misleading — that's the kernel; the userland
  is 32-bit (check with `getconf LONG_BIT`). The arm64 runner fails with
  `cannot execute: required file not found`.
- When `./config.sh` asks for labels, add `raspberry-pi` — the workflow
  targets `runs-on: [self-hosted, raspberry-pi]`.

Then install it as a service so it survives reboots:
```bash
cd ~/actions-runner
sudo ./svc.sh install
sudo ./svc.sh start
```

The runner should now show as "Idle" on the repo's Runners page.

### 4. On the Pi: create the secrets file

Real credentials live only on the Pi, outside the repo and outside the
runner's workspace. The deploy workflow copies this file into the checkout
as `.env` before `docker compose` runs:

```bash
mkdir -p ~/secrets && chmod 700 ~/secrets
# create ~/secrets/pi-dashboard.env with the contents of .env.example,
# then set a real DASH_USER / DASH_PASSWORD
chmod 600 ~/secrets/pi-dashboard.env
```

### 5. Deploy

`git push origin main` (or re-run the workflow from the Actions tab). The
runner checks out the code, copies the secrets file in, builds the image,
and starts the container. Visit `http://<pi-ip>:5000` — you'll get a browser
login prompt (HTTP Basic Auth). Auth covers every route in the app, since
you'll eventually expose this beyond your LAN.

Changed a credential later? Edit `~/secrets/pi-dashboard.env`, then re-run
the deploy workflow (its `--force-recreate` restarts the container with the
new values).

## Plugin-specific setup

**Pi-hole** (`plugins/pihole/`) shells out to the `pihole` CLI on the host.
Since the dashboard runs with `network_mode: host`, it can reach the CLI if
it's installed directly on the Pi. Add a sudoers rule so it can run without a
password prompt:
```bash
echo "pi ALL=(ALL) NOPASSWD: $(which pihole)" | sudo tee /etc/sudoers.d/pihole-dashboard
```
If your Pi-hole is *also* running in Docker, it's actually simpler: swap the
`subprocess` calls for calls to Pi-hole's HTTP API instead (no sudoers rule
needed).

**Wake-on-LAN** (`plugins/wol/`): set `WOL_TARGET_MAC` in
`~/secrets/pi-dashboard.env` to your desktop's MAC address (keep it out of
the repo). Host networking is required for the broadcast packet to reach your
LAN — this is why `docker-compose.yml` uses `network_mode: host` rather than
the default bridge network.

**GPIO** (`plugins/gpio/`): edit `GPIO_PINS` to match your wiring (BCM
numbering). The compose file passes through `/dev/gpiomem` so the container
can control pins without needing `--privileged`.

## Accessing this from outside your home network

Since you'll want that eventually, here are your realistic options, roughly
best-to-most-work for a personal setup like this:

1. **Tailscale (recommended)** — installs as an app on the Pi and on your
   phone/laptop, creates a private encrypted network between your devices.
   No port forwarding, no public exposure at all — you just visit
   `http://<pi-tailscale-name>:5000` from anywhere as if you were on your
   home LAN. Auth in this app becomes a second layer of defense rather than
   your only one. This is what I'd set up first.

2. **Cloudflare Tunnel** — if you want a real public URL (e.g. to share with
   someone else), Cloudflare's `cloudflared` daemon runs on the Pi and
   exposes it through Cloudflare without opening any ports on your router.
   Keep the Basic Auth in place, and consider adding Cloudflare Access in
   front of it for a second login layer.

3. **Port forwarding + reverse proxy** — the traditional way: forward a
   router port to the Pi, put Caddy or nginx in front of the dashboard for
   free HTTPS (Caddy gets you this with almost no config), and keep Basic
   Auth on. Works, but it's the option with the most exposure and the most
   things that can be misconfigured — I'd only reach for this if 1 and 2
   don't fit your situation.

Whichever you pick, make sure the secrets file has a strong, unique
`DASH_PASSWORD` — it's the only thing standing between the internet and your
GPIO pins / Wake-on-LAN / Pi-hole.

## Local development / testing without Docker

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install flask flask-httpauth psutil gpiozero
DASH_USER=admin DASH_PASSWORD=test flask --app app run --port 5001
```

Install the packages individually rather than from `requirements.txt` —
`lgpio` is Linux-only and fails to build elsewhere. GPIO runs in mock mode
when real hardware isn't available, so you can iterate on plugins without
deploying every time. (Port 5001 because macOS's AirPlay Receiver squats on
5000.)
