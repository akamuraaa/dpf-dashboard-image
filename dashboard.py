from PIL import Image, ImageDraw, ImageFont
import datetime
import requests
import urllib.request

WIDTH = 800
HEIGHT = 480

FONT_BIG = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_SMALL = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def get_weather():
    try:
        url = "https://wttr.in/Berlin?format=j1"
        data = requests.get(url, timeout=5).json()
        temp = data["current_condition"][0]["temp_C"]
        desc = data["current_condition"][0]["weatherDesc"][0]["value"]
        return f"{temp}°C", desc
    except Exception:
        return "--°C", "No weather"

def create_dashboard():
    img = Image.new("RGB", (WIDTH, HEIGHT), (15, 18, 22))
    draw = ImageDraw.Draw(img)

    font_big = ImageFont.truetype(FONT_BIG, 120)
    font_small = ImageFont.truetype(FONT_SMALL, 40)

    # Uhrzeit
    now = datetime.datetime.now()
    time_str = now.strftime("%H:%M")
    date_str = now.strftime("%A %d %B %Y")

    draw.text((40, 30), time_str, font=font_big, fill=(255,255,255))
    draw.text((50, 170), date_str, font=font_small, fill=(200,200,200))

    # Wetter
    temp, desc = get_weather()
    draw.text((50, 260), f"Wetter: {temp}", font=font_small, fill=(255,255,255))
    draw.text((50, 320), desc, font=font_small, fill=(200,200,200))

    img.save("/media/pi/FRAME/dashboard/dashboard.jpg")

create_dashboard()
