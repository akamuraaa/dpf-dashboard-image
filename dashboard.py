from PIL import Image, ImageDraw, ImageFont
import datetime
import requests
import urllib.request
from dotenv import load_dotenv
import os

load_dotenv()

WIDTH    = int(os.getenv("WIDTH", 800))
HEIGHT   = int(os.getenv("HEIGHT", 480))
FONT_BIG  = os.getenv("FONT_BIG", "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf")
FONT_SMALL = os.getenv("FONT_SMALL", "/usr/share/fonts/truetype/freefont/FreeSans.ttf")
LOCATION  = os.getenv("LOCATION", "Berlin")
IMG_PATH  = os.getenv("IMG_PATH")
BG_COLOR = os.getenv("BG_COLOR", "#0F1216")
MODULES = os.getenv("MODULES", "time,weather").split(",")
MODULES = [m.strip() for m in MODULES]

def hex_to_rgb(color):
    color = color.strip()
    if color.startswith("#"):
        color = color.lstrip("#")
        return tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
    from PIL import ImageColor
    return ImageColor.getrgb(color)

def get_weather():
    try:
        url = f"https://wttr.in/{LOCATION}?format=j1"
        data = requests.get(url, timeout=5).json()
        temp = data["current_condition"][0]["temp_C"]
        desc = data["current_condition"][0]["weatherDesc"][0]["value"]
        return f"{temp}°C", desc
    except Exception:
        return "--°C", "No weather"

def draw_time(draw, fonts, y=0, height=HEIGHT):
    font_big = ImageFont.truetype(FONT_BIG, int(height * 0.5))
    font_small = ImageFont.truetype(FONT_SMALL, int(height * 0.15))

    now = datetime.datetime.now()
    draw.text((40, y + height * 0.05), now.strftime("%H:%M"), font=font_big, fill=(255,255,255))
    draw.text((50, y + height * 0.65), now.strftime("%A %d %B %Y"), font=font_small, fill=(200,200,200))

def draw_weather(draw, fonts, y=0, height=HEIGHT):
    font_big = ImageFont.truetype(FONT_BIG, int(height * 0.35))
    font_small = ImageFont.truetype(FONT_SMALL, int(height * 0.12))

    temp, desc = get_weather()
    draw.text((50, y + height * 0.05), temp, font=font_big, fill=(255,255,255))
    draw.text((50, y + height * 0.55), desc, font=font_small, fill=(200,200,200))

AVAILABLE_MODULES = {
    "time": draw_time,
    "weather": draw_weather,
}

def create_dashboard():
    img = Image.new("RGB", (WIDTH, HEIGHT), hex_to_rgb(BG_COLOR))
    draw = ImageDraw.Draw(img)

    active = [m for m in MODULES if m in AVAILABLE_MODULES]
    if not active:
        print("no modules activated")
        return

    module_height = HEIGHT // len(active)

    for i, module in enumerate(active):
        y = i * module_height
        AVAILABLE_MODULES[module](draw, None, y=y, height=module_height)

    img.save(IMG_PATH)

create_dashboard()
