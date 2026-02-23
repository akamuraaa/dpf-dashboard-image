import os
import sys
import importlib
import traceback
import datetime
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "modules"))

# load .env config
load_dotenv()

# map .env
CONFIG = {
    "width":   int(os.getenv("WIDTH",  800)),
    "height":  int(os.getenv("HEIGHT", 480)),
    "dpi":     int(os.getenv("DPI",    100)),

    "output_dir": os.getenv("OUTPUT_DIR", "/mnt/usb/"),

    "location":  os.getenv("LOCATION",  "Berlin"),
    "city":      os.getenv("CITY",      "Berlin · DE"),
    "latitude":  float(os.getenv("LATITUDE",  "52.52")),
    "longitude": float(os.getenv("LONGITUDE", "13.41")),
    "timezone":  os.getenv("TIMEZONE",  "Europe/Berlin"),

    "eink": os.getenv("EINK", "false").lower() == "true",

    "glances_host": os.getenv("GLANCES_HOST", "http://localhost:61208"),
    "server_name":  os.getenv("SERVER_NAME",  "homelab-01"),
    
    # Whitelists (kommagetrennt in .env)
    "docker_whitelist":  [x.strip() for x in os.getenv("DOCKER_WHITELIST",  "").split(",") if x.strip()],
    "systemd_whitelist": [x.strip() for x in os.getenv("SYSTEMD_WHITELIST", "").split(",") if x.strip()],
 
    # SSH für Docker + systemd Checks
    # SSH_HOST = Hostname wie in ~/.ssh/config oder /etc/hosts
    # SSH_USER = leer lassen wenn gleicher User wie auf dem Pi
    "ssh_host": os.getenv("SSH_HOST", ""),
    "ssh_user": os.getenv("SSH_USER", ""),

    # Ping-Ziel (Internetverbindung prüfen)
    "ping_host": os.getenv("PING_HOST", "1.1.1.1"),
}

# get activated modules
MODULES = [m.strip() for m in os.getenv("MODULES", "clock,weather,server").split(",") if m.strip()]

# main image generator
def main():
    if not MODULES:
        print("[Dashboard] no modules activated")
        return

    mode = "E-Ink" if CONFIG["eink"] else "Farbe"
    print(f"[Dashboard] start – {datetime.datetime.now().strftime('%H:%M:%S')}  |  mode: {mode}")
    print(f"[Dashboard] module: {', '.join(MODULES)}\n")

    for name in MODULES:
        try:
            mod = importlib.import_module(f"{name}_module")
            if not hasattr(mod, "run"):
                print(f"[{name}] ✗ no 'run(config)' found – skipping")
                continue
            mod.run(CONFIG)
        except ModuleNotFoundError:
            print(f"[{name}] ✗ '{name}_module.py' not found – skipping")
        except Exception:
            print(f"[{name}] ✗ Error:")
            traceback.print_exc()

    print(f"\n[Dashboard] finished – {datetime.datetime.now().strftime('%H:%M:%S')}")


if __name__ == "__main__":
    main()