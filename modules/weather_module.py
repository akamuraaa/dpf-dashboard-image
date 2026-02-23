import requests
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
from matplotlib import font_manager
import urllib.request
import numpy as np
from datetime import datetime, timedelta
from PIL import Image
import io, os

# ── Farben (Farb-Modus) ───────────────────────────────────────────────────────
C = {
    "bg":    "#0D1B2A",
    "blue":  "#4A90D9",
    "blue_a":"#60A5FA",
    "text1": "#E8EDF2",
    "text2": "#7BA3C4",
    "text3": "#4A6A8A",
    "text4": "#1A2E42",
    "gold":  "#FCD34D",
    "orange":"#FB923C",
    "green": "#4ADE80",
    "red":   "#F87171",
}

WEEKDAYS = ["Mo","Di","Mi","Do","Fr","Sa","So"]
WMO = {
    0:"Klar", 1:"Meist klar", 2:"Teilw. bewölkt", 3:"Bedeckt",
    45:"Nebel", 51:"Leichter Niesel", 53:"Nieselregen",
    61:"Leichter Regen", 63:"Regen", 65:"Starker Regen",
    71:"Leichter Schnee", 73:"Schnee", 75:"Starker Schnee",
    80:"Schauer", 81:"Starke Schauer", 95:"Gewitter", 99:"Heftiges Gewitter",
}
WMO_SHORT = {
    0:"☀", 1:"🌤", 2:"⛅", 3:"☁",
    45:"🌫", 51:"🌦", 53:"🌦", 61:"🌧", 63:"🌧", 65:"🌧",
    71:"🌨", 73:"❄", 75:"❄", 80:"🌦", 81:"🌦", 95:"⛈", 99:"⛈",
}

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
def fetch_weather(lat, lon):
    r = requests.get("https://api.open-meteo.com/v1/forecast", params={
        "latitude": lat, "longitude": lon,
        "current": ["temperature_2m","apparent_temperature","relative_humidity_2m",
                    "windspeed_10m","weathercode","precipitation_probability"],
        "daily":   ["temperature_2m_max","temperature_2m_min","weathercode",
                    "sunrise","sunset","precipitation_probability_max"],
        "timezone": "Europe/Berlin", "forecast_days": 6,
    }, timeout=10)
    r.raise_for_status()
    return r.json()

def parse(data):
    cur   = data["current"]
    daily = data["daily"]
    sr    = datetime.strptime(daily["sunrise"][0].split("T")[1][:5], "%H:%M")
    ss    = datetime.strptime(daily["sunset"][0].split("T")[1][:5],  "%H:%M")
    dl    = int((ss - sr).total_seconds() / 60)
    return {
        "temp":    round(cur["temperature_2m"]),
        "feels":   round(cur["apparent_temperature"]),
        "hum":     cur["relative_humidity_2m"],
        "wind":    cur["windspeed_10m"],
        "wcode":   cur["weathercode"],
        "precip":  cur.get("precipitation_probability") or 0,
        "desc":    WMO.get(cur["weathercode"], ""),
        "sunrise": daily["sunrise"][0].split("T")[1][:5],
        "sunset":  daily["sunset"][0].split("T")[1][:5],
        "daylight":f"{dl//60}h {dl%60}m",
        "daily":   daily,
    }

# ── Icon ──────────────────────────────────────────────────────────────────────
# cx, cy = Mittelpunkt des Icons in Pixel-Koordinaten
# r      = Basisradius in Pixeln (z.B. 30 für großes Icon, 12 für kleines)
def draw_icon(ax, cx, cy, code, r=30, eink=False):
    sun_c   = C["gold"]   if not eink else "#444444"
    cloud_c = "#5A7A9A"   if not eink else "#AAAAAA"
    cloud_d = "#3A5A7A"   if not eink else "#888888"
    rain_c  = C["blue_a"] if not eink else "#444444"
    snow_c  = "#E2E8F0"   if not eink else "#CCCCCC"

    def sun(alpha=1.0):
        ax.add_patch(plt.Circle((cx, cy), r*0.55, color=sun_c, zorder=5, alpha=alpha))
        for deg in range(0, 360, 45):
            rad = np.radians(deg)
            x1, y1 = cx + r*0.72*np.cos(rad), cy + r*0.72*np.sin(rad)
            x2, y2 = cx + r*1.05*np.cos(rad), cy + r*1.05*np.sin(rad)
            ax.plot([x1,x2],[y1,y2], color=sun_c, lw=max(r*0.12,1.5),
                    solid_capstyle='round', zorder=5, alpha=alpha)

    def cloud(ox=0, oy=0, col=cloud_c, z=4):
        ec = "#444444" if eink else "none"
        lw = 0.5 if eink else 0
        for dx, dy, fr in [(-0.35,0.15,0.40),(0.20,0.45,0.55),(0.75,0.15,0.40),(0.0,-0.10,0.40)]:
            ax.add_patch(plt.Circle(
                (cx+ox+dx*r, cy+oy+dy*r), fr*r,
                color=col, zorder=z, ec=ec, linewidth=lw))

    def rain_drops(oy=0):
        for dx in [-0.5,-0.1,0.3,0.65]:
            ax.plot([cx+(dx+0.15)*r, cx+dx*r],
                    [cy+oy-0.6*r,    cy+oy-1.2*r],
                    color=rain_c, lw=max(r*0.10,1.5),
                    solid_capstyle='round', zorder=6)

    def snow_dots(oy=0):
        for dx in [-0.45, 0.0, 0.45]:
            ax.add_patch(plt.Circle(
                (cx+dx*r, cy+oy-0.9*r), r*0.12,
                color=snow_c, zorder=6))

    if code in [0, 1]:
        sun()
    elif code == 2:
        sun(alpha=0.85)
        cloud(ox=0.3*r, oy=-0.35*r, col=cloud_d, z=6)
    elif code in [3, 45]:
        cloud(col=cloud_d)
    elif code in [51, 53, 61, 63, 65, 80, 81]:
        cloud(col=cloud_d)
        rain_drops()
    elif code in [71, 73, 75]:
        cloud(col="#7A9AB4" if not eink else "#BBBBBB")
        snow_dots()
    elif code in [95, 99]:
        cloud(col="#2A3A4A" if not eink else "#888888")
        # Blitz
        bx = [cx-0.15*r, cx+0.20*r, cx+0.05*r, cx+0.35*r]
        by = [cy-0.25*r, cy-0.55*r, cy-0.55*r, cy-1.15*r]
        ax.plot(bx, by, color=C["gold"] if not eink else "#333333",
                lw=max(r*0.12,2), solid_capstyle='round', zorder=6)
    else:
        cloud()

def draw_bar(ax, x, y, w, h, pct, col, eink=False):
    if eink:
        from eink_style import draw_bar_eink
        draw_bar_eink(ax, x, y, w, h, pct)
    else:
        ax.add_patch(FancyBboxPatch((x,y), w, h,
            boxstyle="round,pad=0", linewidth=0, facecolor=C["text4"], zorder=3))
        ax.add_patch(FancyBboxPatch((x,y), max((pct/100)*w,4), h,
            boxstyle="round,pad=0", linewidth=0, facecolor=col, zorder=4))

# ── Render Farbe ──────────────────────────────────────────────────────────────
def render_color(d, cfg):
    W, H, DPI = cfg["width"], cfg["height"], cfg["dpi"]
    now    = datetime.now()
    time_s = now.strftime("%H:%M")
    date_s = now.strftime("%A, %-d. %B")

    fig = plt.figure(figsize=(W/DPI, H/DPI), dpi=DPI, facecolor=C["bg"])
    ax  = fig.add_axes([0,0,1,1])
    ax.set_xlim(0,W); ax.set_ylim(0,H); ax.axis('off'); ax.set_facecolor(C["bg"])

    # ── Header ────────────────────────────────────────────────────────────────
    ax.text(28, H-10, cfg.get("city","").upper(), color=C["blue"], fontsize=13,
            fontweight='bold', va='top', ha='left', zorder=5)
    ax.text(28, H-28, date_s, color=C["text3"], fontsize=13, va='top', ha='left', zorder=5)
    ax.text(W-28, H-8, time_s, color=C["text1"], fontsize=38, fontweight='bold',
            va='top', ha='right', zorder=5)

    # ── Haupt-Icon + Temperatur ───────────────────────────────────────────────
    # Icon links, Temperatur daneben – in der oberen Hälfte
    icon_cx, icon_cy = 90, H - 140
    draw_icon(ax, cx=icon_cx, cy=icon_cy, code=d["wcode"], r=55)

    ax.text(180, H-70, str(d["temp"]), color=C["text1"], fontsize=96,
            fontweight='bold', va='top', ha='left', zorder=5)
    ax.text(180 + len(str(d["temp"]))*54, H-66, "C", color=C["text2"], fontsize=32,
            va='top', ha='left', zorder=5)
    # Grad-Zeichen
    ax.text(180 + len(str(d["temp"]))*54 - 10, H-60, "o", color=C["text2"], fontsize=16,
            va='top', ha='left', zorder=5)
    ax.text(180, H-175, d["desc"], color=C["text2"], fontsize=17, va='top', ha='left', zorder=5)

    # ── Detail-Kacheln ────────────────────────────────────────────────────────
    details = [("Gefühlt", f"{d['feels']} C"), ("Wind", f"{d['wind']:.0f} km/h"),
               ("Luftf.",  f"{d['hum']}%"),    ("Regen", f"{d['precip']}%")]
    gx, gy = 460, H-60
    for i, (lbl, val) in enumerate(details):
        x = gx + (i % 2) * 160
        y = gy - (i // 2) * 52
        ax.plot([x, x+140],[y-28, y-28], color=C["text4"], lw=0.8)
        ax.text(x,     y, lbl, color=C["text3"], fontsize=13, va='top', ha='left', zorder=5)
        ax.text(x+140, y, val, color=C["text1"], fontsize=18, fontweight='bold',
                va='top', ha='right', zorder=5)

    # ── Sonne (ohne Emoji) ────────────────────────────────────────────────────
    ax.text(460, H-175, f"Auf:  {d['sunrise']}", color=C["gold"],   fontsize=16,
            fontweight='bold', va='top', ha='left', zorder=5)
    ax.text(600, H-175, f"Unt: {d['sunset']}",  color=C["orange"], fontsize=16,
            fontweight='bold', va='top', ha='left', zorder=5)
    ax.text(460, H-198, d["daylight"], color=C["text3"], fontsize=11, va='top', ha='left', zorder=5)

    # ── Trennlinie ────────────────────────────────────────────────────────────
    divider_y = H - 232
    ax.plot([32, W-32], [divider_y, divider_y], color=C["text4"], lw=0.8)

    # ── 5-Tage-Vorschau ───────────────────────────────────────────────────────
    col_w = (W - 64) / 5
    daily = d["daily"]
    for i in range(5):
        xc = 32 + col_w*i + col_w/2
        xl = 32 + col_w*i
        # Heute-Highlight
        if i == 0:
            ax.add_patch(FancyBboxPatch((xl+4, 4), col_w-8, divider_y-12,
                boxstyle="round,pad=4", linewidth=0,
                facecolor=C["blue_a"], alpha=0.10, zorder=2))
        # Wochentag
        day_n = now + timedelta(days=i)
        lbl   = "Heute" if i == 0 else WEEKDAYS[day_n.weekday()]
        ax.text(xc, divider_y-14, lbl.upper(),
                color=C["blue"] if i==0 else C["text3"],
                fontsize=12, fontweight='bold', va='top', ha='center', zorder=5)
        # Icon – kleinere Basisgröße
        draw_icon(ax, cx=xc, cy=divider_y-80, code=daily["weathercode"][i], r=22)
        # Temperaturen
        hi = round(daily["temperature_2m_max"][i])
        lo = round(daily["temperature_2m_min"][i])
        ax.text(xc-6,  divider_y-122, f"{hi} C", color=C["text1"], fontsize=18,
                fontweight='bold', va='top', ha='right', zorder=5)
        ax.text(xc+6,  divider_y-120, f"{lo} C", color=C["text4"], fontsize=14,
                va='top', ha='left', zorder=5)
        # Regenwahrscheinlichkeit
        rain_p = daily["precipitation_probability_max"][i] or 0
        ax.text(xc, divider_y-148, f"{rain_p}%",
                color=C["blue_a"] if rain_p>50 else C["text3"],
                fontsize=12, va='top', ha='center', zorder=5)
        # Trennlinie
        if i > 0:
            ax.plot([xl+2, xl+2], [8, divider_y-8],
                    color=C["text4"], lw=0.6, zorder=3)

    return fig

# ── Render E-Ink ──────────────────────────────────────────────────────────────
def render_eink(d, cfg):
    from eink_style import EINK
    W, H, DPI = cfg["width"], cfg["height"], cfg["dpi"]
    now    = datetime.now()
    time_s = now.strftime("%H:%M")
    date_s = now.strftime("%A, %-d. %B")

    fig = plt.figure(figsize=(W/DPI, H/DPI), dpi=DPI, facecolor=EINK["bg"])
    ax  = fig.add_axes([0,0,1,1])
    ax.set_xlim(0,W); ax.set_ylim(0,H); ax.axis('off'); ax.set_facecolor(EINK["bg"])

    ax.text(28, H-10, cfg.get("city","").upper(), color=EINK["black"], fontsize=13,
            fontweight='bold', va='top', ha='left', zorder=5)
    ax.text(28, H-28, date_s, color=EINK["mid"], fontsize=13, va='top', ha='left', zorder=5)
    ax.text(W-28, H-8, time_s, color=EINK["black"], fontsize=38, fontweight='bold',
            va='top', ha='right', zorder=5)
    ax.plot([0,W],[H-44,H-44], color=EINK["vlight"], lw=0.8)

    draw_icon(ax, cx=90, cy=H-140, code=d["wcode"], r=55, eink=True)

    ax.text(180, H-70, str(d["temp"]), color=EINK["black"], fontsize=96,
            fontweight='bold', va='top', ha='left', zorder=5)
    ax.text(180+len(str(d["temp"]))*54, H-66, "C", color=EINK["mid"], fontsize=32,
            va='top', ha='left', zorder=5)
    ax.text(180, H-175, d["desc"], color=EINK["dark"], fontsize=17, va='top', ha='left', zorder=5)

    details = [("Gefühlt",f"{d['feels']} C"),("Wind",f"{d['wind']:.0f} km/h"),
               ("Luftf.",f"{d['hum']}%"),("Regen",f"{d['precip']}%")]
    gx, gy = 460, H-60
    for i,(lbl,val) in enumerate(details):
        x = gx+(i%2)*160; y = gy-(i//2)*52
        ax.plot([x,x+140],[y-28,y-28], color=EINK["vlight"], lw=0.8)
        ax.text(x,     y, lbl, color=EINK["mid"],   fontsize=13, va='top', ha='left', zorder=5)
        ax.text(x+140, y, val, color=EINK["black"],  fontsize=18, fontweight='bold',
                va='top', ha='right', zorder=5)

    ax.text(460, H-175, f"Auf: {d['sunrise']}", color=EINK["dark"], fontsize=16,
            fontweight='bold', va='top', ha='left', zorder=5)
    ax.text(600, H-175, f"Unt: {d['sunset']}", color=EINK["dark"], fontsize=16,
            fontweight='bold', va='top', ha='left', zorder=5)

    divider_y = H - 232
    ax.plot([32,W-32],[divider_y,divider_y], color=EINK["light"], lw=1)

    col_w = (W-64)/5
    daily = d["daily"]
    for i in range(5):
        xc = 32+col_w*i+col_w/2
        xl = 32+col_w*i
        if i==0:
            ax.add_patch(FancyBboxPatch((xl+4,4),col_w-8,divider_y-12,
                boxstyle="round,pad=4",linewidth=1.2,
                edgecolor=EINK["dark"],facecolor=EINK["vlight"],zorder=2))
        day_n = now+timedelta(days=i)
        lbl   = "Heute" if i==0 else WEEKDAYS[day_n.weekday()]
        ax.text(xc, divider_y-14, lbl.upper(), color=EINK["black"], fontsize=12,
                fontweight='bold', va='top', ha='center', zorder=5)
        draw_icon(ax, cx=xc, cy=divider_y-80, code=daily["weathercode"][i], r=22, eink=True)
        hi = round(daily["temperature_2m_max"][i])
        lo = round(daily["temperature_2m_min"][i])
        ax.text(xc-6,  divider_y-122, f"{hi} C", color=EINK["black"], fontsize=18,
                fontweight='bold', va='top', ha='right', zorder=5)
        ax.text(xc+6,  divider_y-120, f"{lo} C", color=EINK["light"], fontsize=14,
                va='top', ha='left', zorder=5)
        rain_p = daily["precipitation_probability_max"][i] or 0
        ax.text(xc, divider_y-148, f"{rain_p}%", color=EINK["mid"], fontsize=12,
                va='top', ha='center', zorder=5)
        if i>0:
            ax.plot([xl+2,xl+2],[8,divider_y-8],color=EINK["vlight"],lw=0.8,zorder=3)

    return fig

# ── Speichern ─────────────────────────────────────────────────────────────────
def save(fig, path, cfg):
    from eink_style import EINK
    bg  = EINK["bg"] if cfg.get("eink") else C["bg"]
    W, H, DPI = cfg["width"], cfg["height"], cfg["dpi"]
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=DPI, facecolor=bg,
                bbox_inches='tight', pad_inches=0)
    plt.close(fig)
    buf.seek(0)
    img = Image.open(buf).resize((W, H), Image.LANCZOS)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    print(f"[Wetter] ✓ {path}")

# ── Einstiegspunkt ────────────────────────────────────────────────────────────
def run(config):
    ensure_font()
    data = fetch_weather(config["latitude"], config["longitude"])
    d    = parse(data)
    d["city"] = config.get("city","")
    path = config["output_dir"] + "weather.png"
    fig  = render_eink(d, config) if config.get("eink") else render_color(d, config)
    save(fig, path, config)


if __name__ == "__main__":
    run({
        "latitude": 52.52, "longitude": 13.41,
        "city": "Berlin · DE",
        "output_dir": "/mnt/usb/",
        "width": 800, "height": 480, "dpi": 100,
        "eink": False,   # ← hier umschalten zum Testen
    })