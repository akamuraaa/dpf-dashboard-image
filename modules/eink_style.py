from matplotlib.patches import FancyBboxPatch
import matplotlib.pyplot as plt

# ── E-Ink Colors ──────────────────────────────────────────────────────────────
EINK = {
    "bg":       "#FFFFFF",   # Background
    "black":    "#000000",   # Main text, lines
    "dark":     "#222222",   # Secondary text
    "mid":      "#555555",   # Labels, descriptions
    "light":    "#AAAAAA",   # Subtle elements
    "vlight":   "#DDDDDD",   # Dividing lines, solid-color background
}

# ── Status-Symbols (insteat of colors) ─────────────────────────────────────────────
STATUS_OK    = "●"
STATUS_ERR   = "✕"
STATUS_UNK   = "○"

# ── helpers ───────────────────────────────────────────────────────────

def draw_bar_eink(ax, x, y, w, h, pct, warn=70, crit=90):
    # background
    ax.add_patch(FancyBboxPatch((x, y), w, h,
        boxstyle="round,pad=0", linewidth=0.8,
        edgecolor=EINK["light"], facecolor=EINK["vlight"], zorder=3))
    # filling
    fill_w = max((pct / 100) * w, 3)
    fill_col = EINK["black"] if pct < warn else EINK["dark"]
    ax.add_patch(FancyBboxPatch((x, y), fill_w, h,
        boxstyle="round,pad=0", linewidth=0,
        facecolor=fill_col, zorder=4))
    # crit
    if pct >= crit:
        ax.plot([x, x + fill_w], [y + h/2, y + h/2],
                color=EINK["bg"], lw=1.5, linestyle="--", zorder=5)


def draw_status_row_eink(ax, x, y, name, ok, row_w=240):
    if ok is True:
        sym   = STATUS_OK
        label = "OK"
        bg    = EINK["bg"]
        edge  = EINK["light"]
        sym_col = EINK["dark"]
    elif ok is False:
        sym   = STATUS_ERR
        label = "ERROR"
        bg    = EINK["vlight"]
        edge  = EINK["dark"]
        sym_col = EINK["black"]
    else:
        sym   = STATUS_UNK
        label = "?"
        bg    = EINK["bg"]
        edge  = EINK["vlight"]
        sym_col = EINK["light"]

    # background box
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

    # Label right
    weight = 'bold' if ok is False else 'normal'
    ax.text(x + row_w - 6, y - 4, label, color=EINK["black"],
            fontsize=10, fontweight=weight, va='top', ha='right', zorder=6)


def section_label_eink(ax, x, y, text):
    ax.text(x, y, text, color=EINK["mid"], fontsize=8,
            fontweight='bold', va='top', ha='left', zorder=5)