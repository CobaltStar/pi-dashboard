# Pi Dashboard

A Flask web UI for your Raspberry Pi: live system stats (CPU %, temp, memory,
disk, uptime) plus a **Projects** section where each project (Pi-hole toggle,
Wake-on-LAN, GPIO control, whatever you build next) is a self-contained
plugin. Runs in Docker. GitHub is the source of truth — the Pi pulls from it
automatically, so day-to-day deploys are just `git push origin main`.

## Architecture

```
pi-dashboard/
  app.py                # core: stats API + plugin loader + auth
  plugins/
    _example.py          # template — copy this to start a new project
    pihole.py
    wol.py
    gpio.py
  templates/index.html   # renders stats + auto-generated project cards
  Dockerfile
  docker-compose.yml
  .env.example            # copy to .env on the Pi, fill in real credentials
  deploy/
    setup-on-pi.sh         # one-time: clones from GitHub + installs cron job
    pull-deploy.sh           # run every minute by cron: pulls + rebuilds on change
```

### Adding a new project

1. Copy `plugins/_example.py` to `plugins/your_project.py`.
2. Fill in `register_routes(app)` (your API routes), `CARD_HTML` (the UI
   card), and `SCRIPT` (its JS).
3. `git push origin main` — the Pi picks it up within a minute.

Nothing else needs editing — the loader in `app.py` auto-discovers every
file in `plugins/` and stitches its card into the dashboard.

## First-time setup

### 1. On the Pi: install Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# log out and back in for the group change to take effect
```

### 2. Push this repo to GitHub

Turn this project into a git repo if it isn't already, create an empty repo
on GitHub, then:
```bash
git remote add origin git@github.com:<you>/pi-dashboard.git
git push -u origin main
```

### 3. On the Pi: clone it and set up the polling deploy

```bash
ssh pi@<pi-ip>
git clone git@github.com:<you>/pi-dashboard.git ~/deploy-setup-tmp
bash ~/deploy-setup-tmp/deploy/setup-on-pi.sh git@github.com:<you>/pi-dashboard.git
rm -rf ~/deploy-setup-tmp
```

This clones the repo to `~/pi-dashboard` and installs a cron job that runs
`deploy/pull-deploy.sh` every minute. That script fetches `origin/main`, and
only if there's a new commit does it reset to it, create `.env` from
`.env.example` on first run (edit it with real credentials afterward!), and
run `docker compose up -d --build`. Logs land in `deploy/pull-deploy.log`.

From then on, every `git push origin main` from your dev machine gets picked
up by the Pi within a minute — no manual steps on the Pi side.

### 4. Set real credentials

```bash
ssh pi@<pi-ip>
nano ~/pi-dashboard/.env      # set DASH_USER / DASH_PASSWORD
cd ~/pi-dashboard && docker compose up -d --build
```

Visit `http://<pi-ip>:5000` — you'll get a browser login prompt (HTTP Basic
Auth). This is required for every route in the app, since you'll eventually
expose this beyond your LAN.

## Plugin-specific setup

**Pi-hole** (`plugins/pihole.py`) shells out to the `pihole` CLI on the host.
Since the dashboard runs with `network_mode: host`, it can reach the CLI if
it's installed directly on the Pi. Add a sudoers rule so it can run without a
password prompt:
```bash
echo "pi ALL=(ALL) NOPASSWD: $(which pihole)" | sudo tee /etc/sudoers.d/pihole-dashboard
```
If your Pi-hole is *also* running in Docker, it's actually simpler: swap the
`subprocess` calls for calls to Pi-hole's HTTP API instead (no sudoers rule
needed) — happy to write that version if that's your setup.

**Wake-on-LAN** (`plugins/wol.py`): set `TARGET_MAC` to your desktop's MAC
address. Host networking is required for the broadcast packet to reach your
LAN — this is why `docker-compose.yml` uses `network_mode: host` rather than
the default bridge network.

**GPIO** (`plugins/gpio.py`): edit `GPIO_PINS` to match your wiring (BCM
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

Whichever you pick, make sure `.env` has a strong, unique `DASH_PASSWORD` —
right now it's the only thing standing between the internet and your GPIO
pins / Wake-on-LAN / Pi-hole.

## Local development / testing without Docker

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
DASH_USER=admin DASH_PASSWORD=test python3 app.py
```
Runs in mock mode for GPIO if `gpiozero` can't access real hardware (e.g. on
a non-Pi machine), so you can iterate on plugins without needing to deploy
every time.
