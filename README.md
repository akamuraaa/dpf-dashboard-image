# 🖼️ dpf-dashboard

A configurable image dashboard generator for (mainly) Raspberry Pi. It automatically generates a JPG with selectable modules (time, weather, …) and saves it to a defined path – e.g. for a photo frame or e-ink display.

> just to clarify: this project is near fully written by ai! i just given the idea and looked over the code and tested it. i'm not good in python, but i will try to maintain this project.

---

## Requirements

**Install Python packages:**
```bash
sudo apt install python3-pil python3-dotenv python3-matplotlib python3-numpy
```
```bash
sudo dnf install python3-pil python3-dotenv python3-matplotlib python3-numpy
```
```bash
sudo visudo -f /etc/sudoers.d/pi-docker
```
and add
`pi ALL=(ALL) NOPASSWD: /usr/bin/docker`

---

## Configuration

All settings are defined in a `.env` file in the same directory as the script:

### All options at a glance

| Variable | Description | Default |
|---|---|---|
| `WIDTH` | Image/Screen width in pixels | `800` |
| `HEIGHT` | Image/Screen height in pixels | `480` |
| `DPI` | Zoom Factor | `100` |
| `LOCATION` | City for the weather query | `Berlin` |
| `CITY` | City for the weather query | `Berlin · DE` |
| `LATITUDE` | latitude for your city | `52.52` |
| `LONGITUDE` | longitude for your city | `13.41` |
| `TIMEZONE` | location timezone | `Europe/Berlin` |
| `GLANCES_HOST` | location timezone | `http://localhost:61208` |
| `SERVER_NAME` | The Name you want to display | `homelab-01` |
| `DOCKER_WHITELIST` | Docker Containers you want to display |  |
| `SYSTEMD_WHITELIST` | SystemD Services you want to display |  |
| `SSH_HOST` | your server hostname or ip | `example.name` |
| `SSH_USER` | your server user name |  |
| `PING_HOST` | The Server you want to Ping | `1.1.1.1` |
| `MODULES` | Active modules, comma-separated | `clock,weather,server` |

---

## Modules

Active modules are listed comma-separated in `MODULES`. The order determines the layout from top to bottom. The available height is automatically split equally between all active modules. (More modules will be added)

### Available modules

| Module | Description |
|---|---|
| `clock` | Current time and date |
| `weather` | Current temperature and weather description |
| `server` | Some Server Stats |

---

## Usage

```bash
python3 dashboard.py
```

### Run automatically via cron job (e.g. every minute)

```bash
crontab -e
```
```plain
* * * * * python3 /home/pi/dashboard/dashboard.py
```

---

## Contributing

I'm new to this. New Modules ideas or Integrations are welcome. Also bug fixes.
