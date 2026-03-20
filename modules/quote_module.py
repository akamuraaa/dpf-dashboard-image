import requests
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib import font_manager
import urllib.request
import textwrap
import json
import os
from datetime import datetime
from PIL import Image
import io

from i18n import t, get_lang

# ── Colors ────────────────────────────────────────────────────────────────────
C = {
    "bg":    "#0D1B2A",
    "blue":  "#4A90D9",
    "blue_a":"#60A5FA",
    "text1": "#E8EDF2",
    "text2": "#7BA3C4",
    "text3": "#4A6A8A",
    "text4": "#1A2E42",
    "gold":  "#FCD34D",
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

# ── Cache ─────────────────────────────────────────────────────────────────────
def _cache_path(config):
    cache_dir = config.get("cache_dir", "/tmp")
    return os.path.join(cache_dir, "quote_cache.json")

def _load_cache(config):
    try:
        with open(_cache_path(config), encoding="utf-8") as f:
            data = json.load(f)
        today = datetime.now().strftime("%Y-%m-%d")
        lang  = get_lang()
        if data.get("date") == today and data.get("lang") == lang:
            return data
    except Exception:
        pass
    return None

def _save_cache(config, quote, author):
    try:
        with open(_cache_path(config), "w", encoding="utf-8") as f:
            json.dump({
                "date":   datetime.now().strftime("%Y-%m-%d"),
                "quote":  quote,
                "author": author,
            }, f, ensure_ascii=False)
    except Exception as e:
        print(f"[Quote] Cache-Error: {e}")

# ── translation via MyMemory ──────────────────────────────────────────────────
MYMEMORY_LANGS = {"de": "de-DE", "es": "es-ES", "en": "en-US"}
 
def translate_quote(quote, author):
    lang = get_lang()
    if lang == "en":
        return quote, author
 
    target = MYMEMORY_LANGS.get(lang, lang)
    try:
        r = requests.get(
            "https://api.mymemory.translated.net/get",
            params={"q": quote, "langpair": f"en-US|{target}"},
            timeout=8,
        )
        r.raise_for_status()
        data        = r.json()
        translated  = data["responseData"]["translatedText"]

        if data["responseStatus"] != 200 or translated.upper() == quote.upper():
            raise ValueError(f"MyMemory: {data.get('responseDetails', 'no translation')}")
        print(f"[Quote] translated via MyMemory ({target}).")
        return translated, author
    except Exception as e:
        print(f"[Quote] translation-error: {e} – show original")
        return quote, author

# ── API ───────────────────────────────────────────────────────────────────────
FALLBACK_QUOTES = [
    ("The only way to do great work is to love what you do.", "Steve Jobs"),
    ("In the middle of difficulty lies opportunity.", "Albert Einstein"),
    ("It does not matter how slowly you go as long as you do not stop.", "Confucius"),
    ("Life is what happens when you're busy making other plans.", "John Lennon"),
    ("The future belongs to those who believe in the beauty of their dreams.", "Eleanor Roosevelt"),
]

def fetch_quote(config):
    cached = _load_cache(config)
    if cached:
        print("[Quote] loaded from cache.")
        return cached["quote"], cached["author"]

    quote_en, author = None, None

    try:
        r = requests.get("https://zenquotes.io/api/today", timeout=8)
        r.raise_for_status()
        data = r.json()[0]
        q = data.get("q", "").strip()
        a = data.get("a", "").strip()
        if q and a:
            quote_en, author = q, a
            print("[Quote] loaded from API.")
        else:
            raise ValueError("empty answer from ZenQuotes")
    except Exception as e:
        print(f"[Quote] API-Error: {e} – use Fallback")

    if not quote_en:
        day_index = datetime.now().timetuple().tm_yday % len(FALLBACK_QUOTES)
        quote_en, author = FALLBACK_QUOTES[day_index]

    quote, author = translate_quote(quote_en, author)

    _save_cache(config, quote, author)
    return quote, author

# ── Render ────────────────────────────────────────────────────────────────────
def render(quote, author, cfg):
    eink  = cfg.get("eink", False)
    W, H, DPI = cfg["width"], cfg["height"], cfg["dpi"]

    from eink_style import EINK
    bg    = EINK["bg"]     if eink else C["bg"]
    col1  = EINK["black"]  if eink else C["text1"]
    col2  = EINK["dark"]   if eink else C["text2"]
    col3  = EINK["mid"]    if eink else C["text3"]
    col4  = EINK["vlight"] if eink else C["text4"]
    colbl = EINK["black"]  if eink else C["blue"]
    colgo = EINK["black"]  if eink else C["gold"]

    now = datetime.now()
    weekday = t("date.weekdays")[now.weekday()]
    month   = t("date.months")[now.month - 1]
    date_s  = t("date.date_display", day=now.day, month=month, year=now.year)

    import numpy as np
    import random as _random
    day_seed = now.timetuple().tm_yday
    rng = _random.Random(day_seed)

    fig = plt.figure(figsize=(W/DPI, H/DPI), dpi=DPI, facecolor=bg)
    ax  = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W); ax.set_ylim(0, H)
    ax.axis('off'); ax.set_facecolor(bg)

    # ── backgroundelements ─────────────────────────────────
    if not eink:
        shape = day_seed % 3
        cx = rng.uniform(W*0.55, W*0.85)
        cy = rng.uniform(H*0.25, H*0.55)
 
        if shape == 0:
            for radius, alpha in [(160, 0.04), (110, 0.05), (65, 0.06)]:
                ax.add_patch(plt.Circle((cx, cy), radius,
                    color=C["blue"], alpha=alpha, zorder=1, linewidth=0))
        elif shape == 1:
            size = rng.uniform(90, 130)
            pts  = [(cx, cy+size), (cx+size*0.6, cy),
                    (cx, cy-size), (cx-size*0.6, cy), (cx, cy+size)]
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            ax.plot(xs, ys, color=C["blue"], alpha=0.07, lw=1.2, zorder=1)
            ax.plot(xs, ys, color=C["blue_a"], alpha=0.04,
                    lw=40, solid_joinstyle='round', zorder=1)
        else:
            for radius, alpha in [(180, 0.04), (130, 0.05), (80, 0.06)]:
                theta = np.linspace(np.pi, 1.5*np.pi, 60)
                ax.plot(cx + radius*np.cos(theta),
                        cy + radius*np.sin(theta),
                        color=C["blue"], alpha=alpha, lw=18,
                        solid_capstyle='round', zorder=1)

    ax.plot([60, W-60], [H-4, H-4], color=colbl, lw=2, alpha=0.7, zorder=4)
    ax.plot([60, W-60], [4,   4],   color=colbl, lw=2, alpha=0.7, zorder=4)

    # ── Header ────────────────────────────────────────────────────────────────
    ax.text(W/2, H*0.93, t("modules.quote.title").upper(),
            color=colbl, fontsize=11, fontweight='bold',
            va='center', ha='center', zorder=5)

    ax.text(W/2, H*0.84, f"{weekday}, {date_s}",
            color=col3, fontsize=13, va='center', ha='center', zorder=5)

    ax.plot([W*0.1, W*0.9], [H*0.78, H*0.78], color=col4, lw=0.8, zorder=4)

    # ── decorations ─────────────────────────────────────────
    ax.text(W*0.08, H*0.72, "\u201c",
            color=colgo, fontsize=72, fontweight='bold',
            va='top', ha='left', alpha=0.4, zorder=4)

    # ── Text ────────────────────────────
    # dynamic size
    char_count = len(quote)
    if char_count < 80:
        fontsize, wrap_at = 22, 42
    elif char_count < 140:
        fontsize, wrap_at = 19, 50
    else:
        fontsize, wrap_at = 16, 58

    lines = textwrap.wrap(quote, width=wrap_at)
    line_h = fontsize * 1.55
    block_h = len(lines) * line_h
    start_y = H * 0.62 + block_h / 2

    for i, line in enumerate(lines):
        ax.text(W/2, start_y - i * line_h,
                line, color=col1, fontsize=fontsize,
                va='center', ha='center', zorder=5)


    # ── ornamental dash ────────────────────────────────────────────────
    dy = H * 0.26
    ax.plot([W*0.15, W*0.38], [dy, dy], color=col4, lw=0.8, zorder=4)
    ax.plot([W*0.62, W*0.85], [dy, dy], color=col4, lw=0.8, zorder=4)

    diamond_x = [W/2,       W/2+8,  W/2,    W/2-8,  W/2]
    diamond_y = [dy+6,      dy,     dy-6,   dy,     dy+6]
    ax.plot(diamond_x, diamond_y, color=colgo, lw=1.2, alpha=0.7, zorder=5)
    ax.add_patch(plt.Polygon(
        list(zip(diamond_x[:-1], diamond_y[:-1])),
        color=colgo, alpha=0.25, zorder=4))

    for ox in [-22, 22]:
        ax.add_patch(plt.Circle((W/2 + ox, dy), 2,
            color=col3, alpha=0.6, zorder=4))

    # ── Autor ─────────────────────────────────────────────────────────────────
    ax.text(W/2, H*0.13,
            f"— {author}",
            color=col2, fontsize=16, fontweight='bold',
            va='center', ha='center', zorder=5)

    return fig

# ── Save ─────────────────────────────────────────────────────────────────
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
    print(f"[Quote] ✓ {path}")

# ── Entrypoint ────────────────────────────────────────────────────────────
def run(config):
    ensure_font()
    quote, author = fetch_quote(config)
    path = config["output_dir"] + "quote.jpg"
    fig  = render(quote, author, config)
    save(fig, path, config)

if __name__ == "__main__":
    import i18n
    i18n.load()
    run({
        "output_dir": "/mnt/usb/",
        "cache_dir":  "/tmp",
        "width": 800, "height": 480, "dpi": 100,
        "eink": False,
    })