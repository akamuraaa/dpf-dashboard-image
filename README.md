# 🖼️ Pi Dashboard

A configurable image dashboard for the Raspberry Pi. It automatically generates a JPG with selectable modules (time, weather, …) and saves it to a defined path – e.g. for a photo frame or e-ink display.

---

## Requirements

**Install Python packages:**
```bash
pip install pillow requests python-dotenv
```

**Fonts** – FreeSans fonts are used by default and come pre-installed on Raspberry Pi OS. Alternatively DejaVu:
```bash
sudo apt install fonts-dejavu
```

---

## Configuration

All settings are defined in a `.env` file in the same directory as the script:

```env
WIDTH=800
HEIGHT=480
FONT_BIG=/usr/share/fonts/truetype/freefont/FreeSansBold.ttf
FONT_SMALL=/usr/share/fonts/truetype/freefont/FreeSans.ttf
LOCATION=Berlin
IMG_PATH=/media/pi/FRAME/dashboard/dashboard.jpg
BG_COLOR=#0F1216
MODULES=time,weather
```

### All options at a glance

| Variable | Description | Example |
|---|---|---|
| `WIDTH` | Image width in pixels | `800` |
| `HEIGHT` | Image height in pixels | `480` |
| `FONT_BIG` | Path to the large font | `/usr/share/fonts/truetype/freefont/FreeSansBold.ttf` |
| `FONT_SMALL` | Path to the small font | `/usr/share/fonts/truetype/freefont/FreeSans.ttf` |
| `LOCATION` | City for the weather query | `Berlin` |
| `IMG_PATH` | Output path for the generated image | `/media/pi/FRAME/dashboard/dashboard.jpg` |
| `BG_COLOR` | Background color (hex or CSS name) | `#0F1216` or `black` |
| `MODULES` | Active modules, comma-separated | `time,weather` |

---

## Modules

Active modules are listed comma-separated in `MODULES`. The order determines the layout from top to bottom. The available height is automatically split equally between all active modules.

### Available modules

| Module | Description |
|---|---|
| `time` | Current time and date |
| `weather` | Current temperature and weather description |

### Examples

Time only, full screen:
```env
MODULES=time
```

Time on top, weather on bottom (50% height each):
```env
MODULES=time,weather
```

---

## Usage

```bash
python dashboard.py
```

### Run automatically via cron job (e.g. every minute)

```bash
crontab -e
```
```
* * * * * python3 /home/pi/dashboard/dashboard.py
```

---

## Adding new modules

1. Write a new function with the signature `draw_xyz(draw, fonts, y, height)`
2. Register it in `AVAILABLE_MODULES`
3. Add it to `MODULES` in your `.env`

```python
def draw_news(draw, fonts, y, height):
    # your logic here
    ...

AVAILABLE_MODULES = {
    "time": draw_time,
    "weather": draw_weather,
    "news": draw_news,  # new
}
```

---

## Project structure

```
dashboard/
├── dashboard.py   # Main script
├── .env           # Configuration (do not commit!)
└── .env.example   # Template for configuration
```

> ⚠️ The `.env` file may contain personal paths and should **not** be committed to a Git repository. Instead, provide a `.env.example` with empty values as a template.
