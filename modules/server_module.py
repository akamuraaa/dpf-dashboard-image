import requests
import subprocess
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib import font_manager
import urllib.request
from datetime import datetime
from PIL import Image
import io, os, sys

# ── Farben (Farb-Modus) ───────────────────────────────────────────────────────
C = {
    "bg":    "#0D1B2A",
    "blue":  "#4A90D9",
    "blue_a":"#60A5FA",
    "text1": "#E8EDF2",
    "text2": "#7BA3C4",
    "text3": "#4A6A8A",
    "text4": "#1A2E42",
    "green": "#4ADE80",
    "orange":"#FB923C",
    "red":   "#F87171",
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

# ── SSH Hilfsfunktion ─────────────────────────────────────────────────────────
def ssh_run(config, command):
    """Führt einen Befehl per SSH auf dem Server aus."""
    host   = config.get("ssh_host", "")
    user   = config.get("ssh_user", "")
    target = f"{user}@{host}" if user else host
    result = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", target, command],
        capture_output=True, text=True, timeout=10
    )
    return result.stdout.strip()

# ── Ping ──────────────────────────────────────────────────────────────────────
def check_ping(host="1.1.1.1"):
    """Pingt einen Host und gibt Latenz in ms zurück, oder None bei Fehler."""
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "3", host],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if "time=" in line:
                    ms = float(line.split("time=")[1].split()[0])
                    return round(ms, 1)
    except Exception:
        pass
    return None

# ── Docker via SSH ────────────────────────────────────────────────────────────
def check_docker(config, whitelist):
    """
    Fragt Docker-Status per SSH ab.
    Gibt {name: True/False/None} zurück.
    True  = läuft
    False = gestoppt / nicht vorhanden
    None  = SSH-Fehler
    """
    results = {name: None for name in whitelist}
    if not whitelist:
        return results
    if not config.get("ssh_host"):
        print("[Server] Docker: SSH_HOST nicht gesetzt – bitte in .env eintragen")
        return results
    try:
        out = ssh_run(config, "sudo docker ps -a --format '{{.Names}}:{{.Status}}'")
        found = {}
        for line in out.splitlines():
            if ":" not in line:
                continue
            name, status = line.split(":", 1)
            found[name.strip()] = status.strip().lower().startswith("up")
        for name in whitelist:
            # None wenn Container überhaupt nicht existiert, sonst True/False
            results[name] = found.get(name, False)
    except Exception as e:
        print(f"[Server] Docker SSH-Fehler: {e}")
    return results

# ── systemd via SSH ───────────────────────────────────────────────────────────
def check_systemd(config, whitelist):
    """
    Prüft systemd Services per SSH mit einem einzigen Kommando.
    Gibt {name: True/False/None} zurück.
    """
    results = {name: None for name in whitelist}
    if not whitelist:
        return results
    if not config.get("ssh_host"):
        print("[Server] systemd: SSH_HOST nicht gesetzt – bitte in .env eintragen")
        return results
    try:
        # Alle Services auf einmal abfragen
        names = " ".join(f"{s}.service" for s in whitelist)
        out   = ssh_run(config, f"systemctl is-active {names}")
        stati = out.splitlines()
        for i, svc in enumerate(whitelist):
            if i < len(stati):
                results[svc] = stati[i].strip() == "active"
    except Exception as e:
        print(f"[Server] systemd SSH-Fehler: {e}")
    return results

# ── Glances API ───────────────────────────────────────────────────────────────
def glances(host, endpoint):
    r = requests.get(f"{host}/api/4/{endpoint}", timeout=5)
    r.raise_for_status()
    return r.json()

def fetch_metrics(config):
    host  = config["glances_host"]
    cpu   = glances(host, "cpu")
    mem   = glances(host, "mem")
    disk  = glances(host, "fs")
    net   = glances(host, "network")
    sens  = glances(host, "sensors")
    uptime= glances(host, "uptime")

    # CPU-Temp
    cpu_temp = None
    for s in sens:
        if "package" in s.get("label","").lower():
            cpu_temp = s.get("value"); break
    if cpu_temp is None:
        for s in sens:
            if s.get("type") == "temperature_core":
                cpu_temp = s.get("value"); break

    # Netzwerk
    up_bps = down_bps = 0
    for iface in net:
        if iface.get("interface_name","") != "lo":
            up_bps   += iface.get("tx",0)
            down_bps += iface.get("rx",0)

    def fmt(b):
        if b >= 1_000_000: return f"{b/1_000_000:.1f} MB/s"
        if b >= 1_000:     return f"{b/1_000:.0f} KB/s"
        return f"{b} B/s"

    # Uptime
    up_s = str(uptime).strip().strip('"')
    if "days" in up_s:
        p = up_s.split(",")
        h = p[1].strip().split(":")[0] if len(p)>1 else "0"
        up_s = f"{p[0].strip()} {h}h"
    else:
        p = up_s.split(":")
        up_s = f"{p[0]}h {p[1]}m" if len(p)>=2 else up_s

    return {
        "cpu_pct":   round(cpu.get("total",0)),
        "mem_pct":   round(mem.get("percent",0)),
        "mem_used":  round(mem.get("used",0)/1_073_741_824, 1),
        "mem_total": round(mem.get("total",0)/1_073_741_824, 1),
        "cpu_temp":  round(cpu_temp) if cpu_temp else None,
        "upload":    fmt(up_bps),
        "download":  fmt(down_bps),
        "uptime":    up_s,
        "disks":     [{"name":d["mnt_point"],
                       "pct":d["percent"],
                       "used":round(d["used"]/1_073_741_824,1),
                       "total":round(d["size"]/1_073_741_824,1)} for d in disk],
    }

# ── Hilfsfunktionen ───────────────────────────────────────────────────────────
def scol(v, eink=False):
    if eink: return "#000000"
    return C["red"] if v >= 90 else C["orange"] if v >= 70 else C["green"]

def draw_bar(ax, x, y, w, h, pct, eink=False):
    if eink:
        from eink_style import draw_bar_eink
        draw_bar_eink(ax, x, y, w, h, pct)
    else:
        ax.add_patch(FancyBboxPatch((x, y), w, h,
            boxstyle="round,pad=0", linewidth=0, facecolor=C["text4"], zorder=3))
        ax.add_patch(FancyBboxPatch((x, y), max((pct/100)*w, 4), h,
            boxstyle="round,pad=0", linewidth=0, facecolor=scol(pct), zorder=4))

def draw_status(ax, x, y, name, ok, row_w, eink=False):
    if eink:
        from eink_style import draw_status_row_eink
        draw_status_row_eink(ax, x, y, name, ok, row_w)
        return
    col   = C["green"] if ok is True else C["red"] if ok is False else C["text3"]
    label = "OK"       if ok is True else "FEHLER" if ok is False else "?"
    bg    = "#0A1E10"  if ok is True else "#1E0A0A" if ok is False else "#0F1820"
    ax.add_patch(FancyBboxPatch((x, y-22), row_w, 20,
        boxstyle="round,pad=2", linewidth=0, facecolor=bg, alpha=0.8, zorder=3))
    ax.add_patch(FancyBboxPatch((x, y-22), 3, 20,
        boxstyle="round,pad=0", linewidth=0, facecolor=col, zorder=5))
    ax.add_patch(plt.Circle((x+14, y-12), 5, color=col, zorder=6))
    if ok is False:
        ax.add_patch(plt.Circle((x+14, y-12), 9, color=C["red"], alpha=0.25, zorder=5))
    ax.text(x+26,       y-4, name,  color=C["text1"], fontsize=13, fontweight='bold',
            va='top', ha='left', fontfamily='monospace', zorder=6)
    ax.text(x+row_w-6,  y-4, label, color=col, fontsize=11,
            va='top', ha='right', zorder=6)

# ── Gemeinsame Layout-Funktion ────────────────────────────────────────────────
def render(d, cfg, eink=False):
    from eink_style import EINK
    W, H, DPI = cfg["width"], cfg["height"], cfg["dpi"]
    bg = EINK["bg"] if eink else C["bg"]

    all_ok  = all(v is True  for v in {**d["docker"], **d["systemd"]}.values())
    any_err = any(v is False for v in {**d["docker"], **d["systemd"]}.values())
    dot_col = C["green"] if all_ok else C["red"] if any_err else C["orange"]

    fig = plt.figure(figsize=(W/DPI, H/DPI), dpi=DPI, facecolor=bg)
    ax  = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W); ax.set_ylim(0, H)
    ax.axis('off'); ax.set_facecolor(bg)

    lc  = EINK["vlight"] if eink else C["text4"]  # Linienfarbe
    tc1 = EINK["mid"]    if eink else C["text3"]  # Labels
    tc2 = EINK["dark"]   if eink else C["text2"]  # Beschriftungen
    tc3 = EINK["black"]  if eink else C["text1"]  # Hauptwerte

    # ── HEADER (H-8 bis H-44) ─────────────────────────────────────────────────
    HDR_LINE = H - 44   # = 436

    ax.plot([0, W], [HDR_LINE, HDR_LINE], color=lc, lw=0.8)

    # Status-Dot
    if not eink:
        ax.add_patch(plt.Circle((18, H-19), 7, color=dot_col, zorder=6))
        if any_err:
            ax.add_patch(plt.Circle((18, H-19), 13, color=C["red"], alpha=0.2, zorder=5))

    name_col = EINK["black"] if eink else C["blue"]
    ax.text(34, H-6,  f"SERVER  ·  {cfg.get('server_name','').upper()}",
            color=name_col, fontsize=13, fontweight='bold', va='top', ha='left', zorder=5)
    ax.text(34, H-24, f"Uptime: {d['uptime']}",
            color=tc1, fontsize=11, va='top', ha='left', zorder=5)
    ax.text(W-12, H-4, datetime.now().strftime("%H:%M"),
            color=tc3, fontsize=38, fontweight='bold', va='top', ha='right', zorder=5)

    # Ping – Mitte Header
    ping_ms   = d.get("ping_ms")
    ping_host = d.get("ping_host", "1.1.1.1")
    if ping_ms is not None:
        ping_col = C["green"] if ping_ms < 50 else C["orange"] if ping_ms < 150 else C["red"]
        ping_lbl = f"{ping_ms} ms"
    else:
        ping_col = C["red"] if not eink else EINK["black"]
        ping_lbl = "Offline"
    if eink:
        ping_col = EINK["black"]
    ax.text(W/2, H-6,  ping_host, color=tc1, fontsize=10,
            va='top', ha='center', zorder=5)
    ax.text(W/2, H-22, ping_lbl,  color=ping_col, fontsize=16, fontweight='bold',
            va='top', ha='center', zorder=5)

    # ── BODY: 3 Spalten ───────────────────────────────────────────────────────
    BODY_TOP = HDR_LINE - 6    # 430 – wo Inhalte beginnen
    BODY_BOT = 8               # unterer Rand

    ax.plot([262, 262], [BODY_BOT, HDR_LINE], color=lc, lw=0.8)
    ax.plot([534, 534], [BODY_BOT, HDR_LINE], color=lc, lw=0.8)

    # ── SPALTE 1: System ──────────────────────────────────────────────────────
    # Alles von oben nach unten mit festen Abständen
    y = BODY_TOP  # Startpunkt, geht nach unten

    ax.text(16, y, "SYSTEM", color=tc1, fontsize=8, fontweight='bold',
            va='top', ha='left', zorder=5)
    y -= 22

    # CPU
    ax.text(16,  y,    "CPU", color=tc2, fontsize=12, va='top', ha='left', zorder=5)
    ax.text(248, y+2,  f"{d['cpu_pct']}%", color=scol(d['cpu_pct'], eink),
            fontsize=20, fontweight='bold', va='top', ha='right', zorder=5)
    y -= 22
    draw_bar(ax, 16, y, 228, 7, d["cpu_pct"], eink=eink)
    y -= 18

    # RAM
    ax.text(16,  y,    "RAM", color=tc2, fontsize=12, va='top', ha='left', zorder=5)
    ax.text(248, y+2,  f"{d['mem_pct']}%", color=scol(d['mem_pct'], eink),
            fontsize=20, fontweight='bold', va='top', ha='right', zorder=5)
    y -= 22
    draw_bar(ax, 16, y, 228, 7, d["mem_pct"], eink=eink)
    y -= 14
    ax.text(16, y, f"{d['mem_used']} GB / {d['mem_total']} GB",
            color=tc1, fontsize=9, va='top', ha='left', zorder=5)
    y -= 22

    # CPU Temp
    if d["cpu_temp"] is not None:
        tc_col = scol(d["cpu_temp"], eink) if not eink else EINK["black"]
        if not eink:
            tc_col = C["red"] if d["cpu_temp"] >= 80 else C["orange"] if d["cpu_temp"] >= 65 else C["green"]
        ax.text(16, y, "CPU Temp", color=tc2, fontsize=12, va='top', ha='left', zorder=5)
        ax.text(16, y-20, f"{d['cpu_temp']}C", color=tc_col, fontsize=26,
                fontweight='bold', va='top', ha='left', zorder=5)
        y -= 52

    # Netzwerk
    ax.plot([16, 248], [y+4, y+4], color=lc, lw=0.6)
    y -= 6
    up_c   = EINK["dark"] if eink else C["blue_a"]
    down_c = EINK["dark"] if eink else C["green"]
    ax.text(16, y, f"Auf: {d['upload']}",   color=up_c,   fontsize=11,
            fontweight='bold', va='top', ha='left', zorder=5)
    y -= 18
    ax.text(16, y, f"Ab:  {d['download']}", color=down_c, fontsize=11,
            fontweight='bold', va='top', ha='left', zorder=5)
    y -= 22

    # Festplatten
    ax.plot([16, 248], [y+4, y+4], color=lc, lw=0.6)
    y -= 6
    for disk in d["disks"][:3]:
        ns = disk["name"][-12:] if len(disk["name"]) > 12 else disk["name"]
        ts = f"{disk['total']:.0f}G" if disk['total'] < 1000 else f"{disk['total']/1000:.1f}T"
        dp_c = scol(disk["pct"], eink)
        ax.text(16,  y,   ns, color=tc2, fontsize=10, va='top', ha='left',
                fontfamily='monospace', zorder=5)
        ax.text(248, y+2, f"{disk['pct']}%", color=dp_c, fontsize=11,
                fontweight='bold', va='top', ha='right', zorder=5)
        y -= 18
        draw_bar(ax, 16, y, 228, 6, disk["pct"], eink=eink)
        y -= 12
        ax.text(16, y, f"{disk['used']:.0f} / {ts} GB",
                color=tc1, fontsize=9, va='top', ha='left', zorder=5)
        y -= 20

    # ── SPALTE 2: Docker ──────────────────────────────────────────────────────
    ax.text(278, BODY_TOP, "DOCKER", color=tc1, fontsize=8,
            fontweight='bold', va='top', ha='left', zorder=5)

    row_y = BODY_TOP - 22
    for name in cfg.get("docker_whitelist", []):
        draw_status(ax, 278, row_y, name, d["docker"].get(name), 240, eink=eink)
        row_y -= 30

    # ── SPALTE 3: systemd ─────────────────────────────────────────────────────
    ax.text(550, BODY_TOP, "SYSTEMD", color=tc1, fontsize=8,
            fontweight='bold', va='top', ha='left', zorder=5)

    row_y = BODY_TOP - 22
    for name in cfg.get("systemd_whitelist", []):
        draw_status(ax, 550, row_y, name, d["systemd"].get(name), 222, eink=eink)
        row_y -= 30

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
    print(f"[Server] ✓ {path}")

# ── Einstiegspunkt ────────────────────────────────────────────────────────────
def run(config):
    ensure_font()
    try:
        d = fetch_metrics(config)
    except requests.exceptions.ConnectionError:
        print(f"[Server] ✗ Glances nicht erreichbar: {config.get('glances_host')}")
        return

    d["docker"]  = check_docker(config,  config.get("docker_whitelist",  []))
    d["systemd"] = check_systemd(config, config.get("systemd_whitelist", []))
    d["ping_ms"] = check_ping(config.get("ping_host", "1.1.1.1"))
    d["ping_host"] = config.get("ping_host", "1.1.1.1")


    path = config["output_dir"] + "server.png"
    fig  = render(d, config, eink=config.get("eink", False))
    save(fig, path, config)


if __name__ == "__main__":
    run({
        "glances_host": "http://192.168.1.100:61208",
        "server_name":  "homelab-01",
        "output_dir":   "/mnt/usb/",
        "width": 800, "height": 480, "dpi": 100,
        "docker_whitelist":  ["deluge","nginx","portainer","vaultwarden"],
        "systemd_whitelist": ["https","fail2ban","sshd","ufw"],
        "ssh_host":     "lars-server",
        "ssh_user":     "",
        "eink": False,   # ← hier umschalten zum Testen
    })