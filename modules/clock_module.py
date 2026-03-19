import requests
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
from matplotlib import font_manager
import urllib.request
from datetime import datetime
from PIL import Image
import io, os
from i18n import t

# ── Colors in Color-Mode ───────────────────────────────────────────────────────
C = {
    "bg":    "#0D1B2A",
    "blue":  "#4A90D9",
    "text1": "#E8EDF2",
    "text2": "#7BA3C4",
    "text3": "#4A6A8A",
    "text4": "#1A2E42",
    "cold":  "#93C5FD",
    "warm":  "#FB923C",
    "hot":   "#F87171",
}

def temp_color(t, eink=False):
    if eink: return "#000000"
    if t <= 0:  return C["cold"]
    if t >= 30: return C["hot"]
    if t >= 22: return C["warm"]
    return C["text1"]

# ── Font ──────────────────────────────────────────────────────────────────────
FONT_DIR  = os.path.expanduser("~/.local/share/fonts/")
FONT_PATH = os.path.join(FONT_DIR, "AtkinsonHyperlegible-Regular.ttf")
FONT_BOLD = os.path.join(FONT_DIR, "AtkinsonHyperlegible-Bold.ttf")

def ensure_font():
    os.makedirs(FONT_DIR, exist_ok=True)
    urls = {
        FONT_PATH: "https://github.com/googlefonts/atkinson-hyperlegible/raw/main/fonts/ttf/AtkinsonHyperlegible-Regular.ttf",
        FONT_BOLD: "https://github.com/googlefonts/atkinson-hyperlegible/raw/main/fonts/ttf/AtkinsonHyperlegible-Bold.ttf",
    }
    for path, url in urls.items():
        if not os.path.exists(path):
            print(f"[Font] Lade {os.path.basename(path)}...")
            urllib.request.urlretrieve(url, path)
    font_manager.fontManager.addfont(FONT_PATH)
    font_manager.fontManager.addfont(FONT_BOLD)
    plt.rcParams["font.family"] = "Atkinson Hyperlegible"

# ── API ───────────────────────────────────────────────────────────────────────
def fetch_temp(lat, lon):
    r = requests.get("https://api.open-meteo.com/v1/forecast", params={
        "latitude": lat, "longitude": lon,
        "current": ["temperature_2m","apparent_temperature","weathercode"],
        "timezone": "Europe/Berlin",
    }, timeout=10)
    r.raise_for_status()
    cur = r.json()["current"]

    wmo_key = str(cur["weathercode"])
    desc = t(f"wmo.{wmo_key}")

    if desc.startswith("["):
        desc = f"Code {wmo_key}"
    return {
        "temp":  round(cur["temperature_2m"]),
        "feels": round(cur["apparent_temperature"]),
        "desc":  desc,
    }

# ── Render ──────────────────────────────────────────────────────────────
def render(weather, cfg):
    eink = cfg.get("eink", False)
    W, H, DPI = cfg["width"], cfg["height"], cfg["dpi"]

    from eink_style import EINK
    bg    = EINK["bg"]    if eink else C["bg"]
    col1  = EINK["black"] if eink else C["text1"]
    col2  = EINK["dark"]  if eink else C["text2"]
    col3  = EINK["mid"]   if eink else C["text3"]
    col4  = EINK["vlight"]if eink else C["text4"]
    colbl = EINK["black"] if eink else C["blue"]

    now    = datetime.now()
    hh     = now.strftime("%H")
    mm     = now.strftime("%M")

    day    = t("date.weekdays")[now.weekday()]
    month  = t("date.months")[now.month - 1]
    date_s = t("date.date_display", day=now.day, month=month, year=now.year)

    CX     = W / 2

    fig = plt.figure(figsize=(W/DPI, H/DPI), dpi=DPI, facecolor=bg)
    ax  = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W); ax.set_ylim(0, H)
    ax.axis('off'); ax.set_facecolor(bg)

    # accent lines
    ax.plot([60, W-60], [H-4,  H-4],  color=colbl, lw=2, alpha=0.7, zorder=4)
    ax.plot([60, W-60], [4,    4],    color=colbl, lw=2, alpha=0.7, zorder=4)

    # weekday
    ax.text(CX, H*0.88, day.upper(), color=colbl, fontsize=28, fontweight='bold',
            va='center', ha='center', zorder=5)

    # date
    ax.text(CX, H*0.76, date_s, color=col3, fontsize=17,
            va='center', ha='center', zorder=5)

    # dash
    ax.plot([W*0.2, W*0.8], [H*0.69, H*0.69], color=col4, lw=0.8, zorder=4)

    # clock
    ax.text(CX, H*0.46, f"{hh}:{mm}", color=col1, fontsize=142, fontweight='bold',
            va='center', ha='center', zorder=5)

    # dash
    ax.plot([W*0.2, W*0.8], [H*0.19, H*0.19], color=col4, lw=0.8, zorder=4)

    # temperature
    TY = H * 0.10

    # outside
    ax.text(W*0.22, TY+14, t("modules.clock.label_outside"), color=col3, fontsize=9,
            fontweight='bold', va='center', ha='center', zorder=5)
    ax.text(W*0.22, TY-8,  f"{weather['temp']}  C", color=temp_color(weather['temp'], eink),
            fontsize=38, fontweight='bold', va='center', ha='center', zorder=5)
    ax.text(W*0.22 + 52, TY+2, "o", color=temp_color(weather['temp'], eink),
            fontsize=18, fontweight='bold', va='center', ha='left', zorder=5)

    # dash
    ax.plot([W*0.38, W*0.38], [TY-22, TY+22], color=col4, lw=0.8, zorder=4)

    # feelt temperature
    ax.text(W*0.50, TY+14, t("modules.clock.label_feels"), color=col3, fontsize=9,
            fontweight='bold', va='center', ha='center', zorder=5)
    ax.text(W*0.50, TY-8,  f"{weather['feels']}  C", color=col2,
            fontsize=38, fontweight='bold', va='center', ha='center', zorder=5)
    ax.text(W*0.50 + 52, TY+2, "o", color=col2,
            fontsize=18, fontweight='bold', va='center', ha='left', zorder=5)

    # dash
    ax.plot([W*0.64, W*0.64], [TY-22, TY+22], color=col4, lw=0.8, zorder=4)

    # weather
    ax.text(W*0.80, TY+14, t("modules.clock.label_weather"), color=col3, fontsize=9,
            fontweight='bold', va='center', ha='center', zorder=5)
    ax.text(W*0.80, TY-8,  weather["desc"], color=col2, fontsize=16,
            fontweight='bold', va='center', ha='center', zorder=5)

    return fig

# ── save ─────────────────────────────────────────────────────────────────
def save(fig, path, cfg):
    from eink_style import EINK
    bg  = EINK["bg"] if cfg.get("eink") else C["bg"]
    W, H, DPI = cfg["width"], cfg["height"], cfg["dpi"]
    buf = io.BytesIO()
    fig.savefig(buf, format='jpeg', pil_kwargs={'quality': 92}, dpi=DPI, facecolor=bg,
                bbox_inches='tight', pad_inches=0)
    plt.close(fig)
    buf.seek(0)
    img = Image.open(buf).convert("RGB").resize((W, H), Image.LANCZOS)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    print(f"[Clock] ✓ {path}")

# ── entrypoint ────────────────────────────────────────────────────────────
def run(config):
    ensure_font()
    weather = fetch_temp(config["latitude"], config["longitude"])
    path    = config["output_dir"] + "clock.jpg"
    fig     = render(weather, config)
    save(fig, path, config)

if __name__ == "__main__":
    run({
        "latitude": 52.52, "longitude": 13.41,
        "output_dir": "/mnt/usb/",
        "width": 800, "height": 480, "dpi": 100,
        "eink": False,
    })