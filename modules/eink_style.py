from matplotlib.patches import FancyBboxPatch
import matplotlib.pyplot as plt

# ── E-Ink Farben ──────────────────────────────────────────────────────────────
EINK = {
    "bg":       "#FFFFFF",   # Hintergrund
    "black":    "#000000",   # Haupttext, Linien
    "dark":     "#222222",   # Sekundärtext
    "mid":      "#555555",   # Labels, Beschreibungen
    "light":    "#AAAAAA",   # Dezente Elemente
    "vlight":   "#DDDDDD",   # Trennlinien, Balkenhintergrund
}

# ── Status-Symbole (statt Farben) ─────────────────────────────────────────────
# E-Ink hat keine Farben → Status über Symbole + Schwarz/Weiß
STATUS_OK    = "●"   # gefüllter Kreis  = OK
STATUS_ERR   = "✕"   # Kreuz            = Fehler
STATUS_UNK   = "○"   # leerer Kreis     = unbekannt

# ── Hilfsfunktionen ───────────────────────────────────────────────────────────

def draw_bar_eink(ax, x, y, w, h, pct, warn=70, crit=90):
    """Fortschrittsbalken für E-Ink: schwarz/weiß, mit Umrandung."""
    # Hintergrund
    ax.add_patch(FancyBboxPatch((x, y), w, h,
        boxstyle="round,pad=0", linewidth=0.8,
        edgecolor=EINK["light"], facecolor=EINK["vlight"], zorder=3))
    # Füllung: schwarz wenn ok, schraffiert wenn hoch
    fill_w = max((pct / 100) * w, 3)
    fill_col = EINK["black"] if pct < warn else EINK["dark"]
    ax.add_patch(FancyBboxPatch((x, y), fill_w, h,
        boxstyle="round,pad=0", linewidth=0,
        facecolor=fill_col, zorder=4))
    # Kritisch: Muster andeuten mit extra Linie
    if pct >= crit:
        ax.plot([x, x + fill_w], [y + h/2, y + h/2],
                color=EINK["bg"], lw=1.5, linestyle="--", zorder=5)


def draw_status_row_eink(ax, x, y, name, ok, row_w=240):
    """
    Status-Zeile für E-Ink.
    ok=True: ● OK | ok=False: ✕ FEHLER | ok=None: ○ ?
    """
    if ok is True:
        sym   = STATUS_OK
        label = "OK"
        bg    = EINK["bg"]
        edge  = EINK["light"]
        sym_col = EINK["dark"]
    elif ok is False:
        sym   = STATUS_ERR
        label = "FEHLER"
        bg    = EINK["vlight"]   # grauer Hintergrund für Fehler
        edge  = EINK["dark"]
        sym_col = EINK["black"]
    else:
        sym   = STATUS_UNK
        label = "?"
        bg    = EINK["bg"]
        edge  = EINK["vlight"]
        sym_col = EINK["light"]

    # Hintergrund-Box
    ax.add_patch(FancyBboxPatch((x, y - 22), row_w, 20,
        boxstyle="round,pad=2", linewidth=0.8,
        edgecolor=edge, facecolor=bg, zorder=3))

    # Status-Symbol
    ax.text(x + 12, y - 4, sym, color=sym_col, fontsize=11,
            va='top', ha='center', zorder=6)

    # Name
    ax.text(x + 24, y - 4, name, color=EINK["black"], fontsize=12,
            fontweight='bold', va='top', ha='left',
            fontfamily='monospace', zorder=6)

    # Label rechts
    weight = 'bold' if ok is False else 'normal'
    ax.text(x + row_w - 6, y - 4, label, color=EINK["black"],
            fontsize=10, fontweight=weight, va='top', ha='right', zorder=6)


def section_label_eink(ax, x, y, text):
    """Abschnitts-Überschrift mit Unterstrich."""
    ax.text(x, y, text, color=EINK["mid"], fontsize=8,
            fontweight='bold', va='top', ha='left', zorder=5)