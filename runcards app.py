import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyArrowPatch, Circle, Rectangle
import matplotlib.patheffects as pe
import io
import zipfile
from collections import Counter

st.set_page_config(
    page_title="Run Card Generator — DefensiveIQ",
    page_icon="🏈",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700;800;900&family=Barlow:wght@400;500&display=swap');
html,body,[class*="css"]{font-family:'Barlow',sans-serif;background:#0a1628;color:#f0ede8;}
.stApp{background:#0a1628;}
.stButton>button{background:#c0392b!important;color:#f0ede8!important;border:none!important;font-family:'Barlow Condensed',sans-serif!important;font-weight:700!important;font-size:15px!important;letter-spacing:.1em!important;text-transform:uppercase!important;padding:12px 28px!important;border-radius:0!important;width:100%!important;}
.stDownloadButton>button{background:#0e7060!important;color:#f0ede8!important;border:none!important;font-family:'Barlow Condensed',sans-serif!important;font-weight:700!important;font-size:13px!important;border-radius:0!important;width:100%!important;}
</style>
""", unsafe_allow_html=True)

# ── Formation layouts ────────────────────────────────────────
# Each formation defines player positions relative to center
# Format: (x_offset, y_offset, label, role)
# Center is at (0,0), LOS is y=0
# Offensive backfield is negative y, receivers positive y

FORMATIONS = {
    # ── Pro / Base ───────────────────────────────────────────
    "PRO": {
        "strength": "R",
        "players": [
            (-2, 0, "LT", "OL"), (-1, 0, "LG", "OL"), (0, 0, "C", "OL"),
            (1, 0, "RG", "OL"), (2, 0, "RT", "OL"),
            (3, 0.2, "TE", "TE"),
            (-4.5, 0, "WR", "WR"),
            (4.5, 0, "WR", "WR"),
            (0, -1.5, "FB", "FB"),
            (0.5, -2.8, "RB", "RB"),
            (0, -1, "QB", "QB"),
        ]
    },
    "ACE": {
        "strength": "R",
        "players": [
            (-2, 0, "LT", "OL"), (-1, 0, "LG", "OL"), (0, 0, "C", "OL"),
            (1, 0, "RG", "OL"), (2, 0, "RT", "OL"),
            (3, 0.2, "TE", "TE"),
            (-4.5, 0, "WR", "WR"),
            (4.5, 0, "WR", "WR"),
            (0, -2.5, "RB", "RB"),
            (0, -1, "QB", "QB"),
        ]
    },
    # ── Trips ───────────────────────────────────────────────
    "TRIPS 1 OPEN": {
        "strength": "R",
        "players": [
            (-2, 0, "LT", "OL"), (-1, 0, "LG", "OL"), (0, 0, "C", "OL"),
            (1, 0, "RG", "OL"), (2, 0, "RT", "OL"),
            (3, 0.5, "WR", "WR"), (4.5, 0, "WR", "WR"), (5.8, 0, "WR", "WR"),
            (-4, 0, "WR", "WR"),
            (0, -2.5, "RB", "RB"),
            (0, -1, "QB", "QB"),
        ]
    },
    "TRIPS CLOSED": {
        "strength": "R",
        "players": [
            (-2, 0, "LT", "OL"), (-1, 0, "LG", "OL"), (0, 0, "C", "OL"),
            (1, 0, "RG", "OL"), (2, 0, "RT", "OL"),
            (3, 0.2, "TE", "TE"), (4, 0.2, "WR", "WR"), (5.3, 0, "WR", "WR"),
            (-4, 0, "WR", "WR"),
            (0, -2.5, "RB", "RB"),
            (0, -1, "QB", "QB"),
        ]
    },
    "TRIPS OVER": {
        "strength": "R",
        "players": [
            (-2, 0, "LT", "OL"), (-1, 0, "LG", "OL"), (0, 0, "C", "OL"),
            (1, 0, "RG", "OL"), (2, 0, "RT", "OL"),
            (3, 0.2, "TE", "TE"), (4.2, 0.2, "WR", "WR"), (5.5, 0, "WR", "WR"),
            (-4, 0, "WR", "WR"),
            (0, -2.5, "RB", "RB"),
            (0, -1, "QB", "QB"),
        ]
    },
    # ── Trey ────────────────────────────────────────────────
    "TREY OVER": {
        "strength": "R",
        "players": [
            (-2, 0, "LT", "OL"), (-1, 0, "LG", "OL"), (0, 0, "C", "OL"),
            (1, 0, "RG", "OL"), (2, 0, "RT", "OL"),
            (3, 0.2, "TE", "TE"), (4.2, 0.2, "WR", "WR"),
            (-4, 0, "WR", "WR"),
            (0, -2.5, "RB", "RB"),
            (0, -1, "QB", "QB"),
        ]
    },
    "TREY OPEN": {
        "strength": "R",
        "players": [
            (-2, 0, "LT", "OL"), (-1, 0, "LG", "OL"), (0, 0, "C", "OL"),
            (1, 0, "RG", "OL"), (2, 0, "RT", "OL"),
            (3, 0.2, "TE", "TE"), (4.2, 0.2, "WR", "WR"),
            (-4, 0, "WR", "WR"), (-5.2, 0, "WR", "WR"),
            (0, -2.5, "RB", "RB"),
            (0, -1, "QB", "QB"),
        ]
    },
    "TREY CLOSED": {
        "strength": "R",
        "players": [
            (-2, 0, "LT", "OL"), (-1, 0, "LG", "OL"), (0, 0, "C", "OL"),
            (1, 0, "RG", "OL"), (2, 0, "RT", "OL"),
            (3, 0.2, "TE", "TE"), (4.2, 0.2, "WR", "WR"),
            (-3, 0.2, "TE", "TE"),
            (-4.5, 0, "WR", "WR"),
            (0, -2.5, "RB", "RB"),
            (0, -1, "QB", "QB"),
        ]
    },
    # ── Twins ───────────────────────────────────────────────
    "TWINS OPEN": {
        "strength": "R",
        "players": [
            (-2, 0, "LT", "OL"), (-1, 0, "LG", "OL"), (0, 0, "C", "OL"),
            (1, 0, "RG", "OL"), (2, 0, "RT", "OL"),
            (3, 0.3, "WR", "WR"), (4.5, 0, "WR", "WR"),
            (-4, 0, "WR", "WR"),
            (0, -2.5, "RB", "RB"),
            (0, -1, "QB", "QB"),
        ]
    },
    "TWINS CLOSED": {
        "strength": "R",
        "players": [
            (-2, 0, "LT", "OL"), (-1, 0, "LG", "OL"), (0, 0, "C", "OL"),
            (1, 0, "RG", "OL"), (2, 0, "RT", "OL"),
            (3, 0.2, "TE", "TE"), (4.5, 0, "WR", "WR"),
            (-3, 0.2, "TE", "TE"), (-4.5, 0, "WR", "WR"),
            (0, -2.5, "RB", "RB"),
            (0, -1, "QB", "QB"),
        ]
    },
    # ── Deuces / Empty ──────────────────────────────────────
    "DEUCES": {
        "strength": "R",
        "players": [
            (-2, 0, "LT", "OL"), (-1, 0, "LG", "OL"), (0, 0, "C", "OL"),
            (1, 0, "RG", "OL"), (2, 0, "RT", "OL"),
            (3, 0.3, "WR", "WR"), (4.5, 0, "WR", "WR"),
            (-3, 0.3, "WR", "WR"), (-4.5, 0, "WR", "WR"),
            (0, -2.5, "RB", "RB"),
            (0, -1, "QB", "QB"),
        ]
    },
    "EMPTY": {
        "strength": "R",
        "players": [
            (-2, 0, "LT", "OL"), (-1, 0, "LG", "OL"), (0, 0, "C", "OL"),
            (1, 0, "RG", "OL"), (2, 0, "RT", "OL"),
            (3, 0.3, "WR", "WR"), (4.5, 0, "WR", "WR"),
            (-3, 0.3, "WR", "WR"), (-4.5, 0, "WR", "WR"),
            (1.5, -1.2, "RB", "RB"),
            (0, -1, "QB", "QB"),
        ]
    },
    "FLEX TIGHT": {
        "strength": "R",
        "players": [
            (-2, 0, "LT", "OL"), (-1, 0, "LG", "OL"), (0, 0, "C", "OL"),
            (1, 0, "RG", "OL"), (2, 0, "RT", "OL"),
            (3, 0.2, "TE", "TE"),
            (-3, 0.2, "TE", "TE"),
            (-4.5, 0, "WR", "WR"),
            (4.5, 0, "WR", "WR"),
            (0, -2.5, "RB", "RB"),
            (0, -1, "QB", "QB"),
        ]
    },
    "UNBALANCED OVER": {
        "strength": "R",
        "players": [
            (-2, 0, "LT", "OL"), (-1, 0, "LG", "OL"), (0, 0, "C", "OL"),
            (1, 0, "RG", "OL"), (2, 0, "RT", "OL"),
            (3, 0.2, "TE", "TE"), (4, 0.2, "OT", "OL"),
            (-4.5, 0, "WR", "WR"),
            (5.5, 0, "WR", "WR"),
            (0, -2.5, "RB", "RB"),
            (0, -1, "QB", "QB"),
        ]
    },
    "QUADS TIGHT OVER": {
        "strength": "R",
        "players": [
            (-2, 0, "LT", "OL"), (-1, 0, "LG", "OL"), (0, 0, "C", "OL"),
            (1, 0, "RG", "OL"), (2, 0, "RT", "OL"),
            (3, 0.2, "TE", "TE"), (4, 0.3, "WR", "WR"),
            (5, 0.3, "WR", "WR"), (6, 0, "WR", "WR"),
            (0, -2.5, "RB", "RB"),
            (0, -1, "QB", "QB"),
        ]
    },
    "DEFAULT": {
        "strength": "R",
        "players": [
            (-2, 0, "LT", "OL"), (-1, 0, "LG", "OL"), (0, 0, "C", "OL"),
            (1, 0, "RG", "OL"), (2, 0, "RT", "OL"),
            (3, 0.2, "TE", "TE"),
            (-4.5, 0, "WR", "WR"), (4.5, 0, "WR", "WR"),
            (0, -2.5, "RB", "RB"),
            (0, -1, "QB", "QB"),
        ]
    }
}

# ── Run path definitions ──────────────────────────────────────
def get_run_path(play, direction):
    """Return list of (dx, dy) waypoints for ball carrier arrow."""
    play = str(play).upper()
    d = 1 if direction == "R" else -1

    # Inside zone
    if "ZONE" in play and "SPLIT" not in play and "OUTSIDE" not in play:
        return [(d*0.3, 1.5), (d*0.8, 2.5), (d*1.5, 4.0)]
    # Split zone
    if "SPLIT ZONE" in play:
        return [(d*0.2, 1.2), (d*0.5, 2.0), (d*0.2, 3.5)]
    # Outside zone
    if "OUTSIDE ZONE" in play or "OZ" in play:
        return [(d*1.2, 1.0), (d*2.5, 2.0), (d*3.5, 4.0)]
    # Counter
    if "CTR" in play or "COUNTER" in play:
        return [(-d*0.3, 0.8), (d*0.5, 1.8), (d*1.5, 3.5)]
    # Power
    if "POWER" in play or "PWR" in play:
        return [(d*0.3, 1.0), (d*1.0, 2.2), (d*1.5, 3.8)]
    # Sweep / Toss
    if "SWEEP" in play or "TOSS" in play:
        return [(d*1.5, 0.5), (d*3.0, 1.5), (d*4.0, 3.5)]
    # Draw
    if "DRAW" in play:
        return [(0, -0.5), (d*0.3, 1.0), (d*1.0, 3.5)]
    # QB Sneak
    if "SNEAK" in play:
        return [(0, 0.5), (0, 2.0)]
    # Boot / Waggle
    if "BOOT" in play or "WAGGLE" in play:
        return [(d*0.5, -0.5), (d*2.0, 0.5), (d*3.0, 3.0)]
    # Lead / Iso
    if "LEAD" in play or "ISO" in play or "F LEAD" in play:
        return [(d*0.2, 1.0), (d*0.5, 2.5), (d*0.8, 4.0)]
    # Default
    return [(d*0.5, 1.2), (d*1.0, 2.5), (d*1.5, 4.0)]

def get_blocking_scheme(play, direction):
    """Return blocking arrows as list of (start_x, start_y, dx, dy)."""
    play = str(play).upper()
    d = 1 if direction == "R" else -1
    arrows = []

    if "ZONE" in play:
        # Zone - OL all go same direction
        for ox in [-2,-1,0,1,2]:
            arrows.append((ox, 0.1, d*0.8, 0.6))
    elif "CTR" in play or "COUNTER" in play:
        # Counter - backside double, frontside kick + log
        arrows.append((-d*2, 0.1, -d*0.3, 0.8))  # backside kick
        arrows.append((-d*1, 0.1, d*0.5, 0.7))
        arrows.append((0, 0.1, d*0.5, 0.7))
        arrows.append((d*1, 0.1, d*0.3, 0.8))
        arrows.append((d*2, 0.1, d*0.2, 0.8))
    elif "POWER" in play:
        arrows.append((-2, 0.1, -d*0.3, 0.8))
        arrows.append((-1, 0.1, d*0.4, 0.8))
        arrows.append((0, 0.1, d*0.4, 0.8))
        arrows.append((1, 0.1, d*0.3, 0.8))
        arrows.append((2, 0.1, d*0.5, 0.8))
    else:
        # Generic - everyone fires out
        for ox in [-2,-1,0,1,2]:
            arrows.append((ox, 0.1, d*0.4+ox*0.05, 0.7))
    return arrows

# ── Draw a single run card ────────────────────────────────────
def draw_run_card(play_data, fig_size=(10,7)):
    form = str(play_data.get('OFF FORM', 'DEFAULT')).upper().strip()
    play = str(play_data.get('OFF PLAY', 'ZONE RT')).strip()
    direction = str(play_data.get('PLAY DIR', 'R')).strip()
    dn = play_data.get('DN', '')
    dist = play_data.get('DIST', '')
    hash_ = play_data.get('HASH', '')
    gnls = play_data.get('GN/LS', '')
    result = play_data.get('RESULT', '')

    if direction not in ('L','R'): direction = 'R'

    # Get formation — fuzzy match
    form_key = None
    for k in FORMATIONS:
        if k in form or form in k:
            form_key = k
            break
    if not form_key:
        form_key = "DEFAULT"

    formation = FORMATIONS[form_key]
    players = formation['players']

    # Flip formation if strength is L
    str_dir = str(play_data.get('OFF STR', 'R')).strip()
    flip = (str_dir == 'L')

    fig, ax = plt.subplots(1, 1, figsize=fig_size)
    fig.patch.set_facecolor('#0a1628')
    ax.set_facecolor('#0d1f38')

    # Field markings
    ax.set_xlim(-8, 8); ax.set_ylim(-4, 6)
    ax.axhline(y=0, color='#f0ede8', linewidth=2, alpha=0.8, zorder=1)
    ax.axhline(y=0.05, color='#2ecc71', linewidth=0.5, alpha=0.2, zorder=1)

    # Hash marks
    for x in [-1.2, 1.2]:
        ax.plot([x, x], [-0.15, 0.15], color='#f0ede8', linewidth=1.5, alpha=0.5, zorder=1)

    # Yard lines (subtle)
    for y in [2, 4]:
        ax.axhline(y=y, color='#f0ede8', linewidth=0.4, alpha=0.1, linestyle='--', zorder=1)
    for y in [-2]:
        ax.axhline(y=y, color='#f0ede8', linewidth=0.4, alpha=0.1, linestyle='--', zorder=1)

    # Colors by role
    role_colors = {
        'OL': '#1a5276',
        'TE': '#0e7060',
        'WR': '#7d6608',
        'RB': '#c0392b',
        'FB': '#8e44ad',
        'QB': '#c0392b',
    }
    role_edge = {
        'OL': '#5dade2',
        'TE': '#2ecc71',
        'WR': '#f1c40f',
        'RB': '#e74c3c',
        'FB': '#9b59b6',
        'QB': '#e74c3c',
    }

    # Draw blocking arrows first (behind players)
    if play_data.get('PLAY TYPE', 'Run') == 'Run':
        scheme = get_blocking_scheme(play, direction)
        for (sx, sy, dx, dy) in scheme:
            ex = (sx*-1 if flip else sx)
            ax.annotate('', xy=(ex+dx*(-1 if flip else 1), sy+dy),
                       xytext=(ex, sy),
                       arrowprops=dict(arrowstyle='->', color='rgba(255,255,255,0.25)',
                                      lw=1.5), zorder=2)

    # Draw players
    rb_pos = None
    qb_pos = None
    for (px, py, lbl, role) in players:
        x = -px if flip else px
        color = role_colors.get(role, '#555')
        edge  = role_edge.get(role, '#888')

        if role == 'OL':
            sq = patches.Rectangle((x-0.32, py-0.25), 0.64, 0.5,
                                    linewidth=2, edgecolor=edge,
                                    facecolor=color, zorder=5)
            ax.add_patch(sq)
            ax.text(x, py, lbl, ha='center', va='center',
                   color='#f0ede8', fontsize=6, fontweight='bold',
                   fontfamily='monospace', zorder=6)
        else:
            circ = Circle((x, py), 0.32, linewidth=2,
                          edgecolor=edge, facecolor=color, zorder=5)
            ax.add_patch(circ)
            ax.text(x, py, lbl, ha='center', va='center',
                   color='#f0ede8', fontsize=6.5, fontweight='bold',
                   fontfamily='monospace', zorder=6)

        if role == 'RB' or (role == 'FB' and rb_pos is None):
            rb_pos = (x, py)
        if role == 'QB':
            qb_pos = (x, py)

    # Draw ball carrier path
    if rb_pos and play_data.get('PLAY TYPE', 'Run') == 'Run':
        waypoints = get_run_path(play, direction)
        path_x = [rb_pos[0]]
        path_y = [rb_pos[1]]
        for (dx, dy) in waypoints:
            path_x.append(rb_pos[0] + dx)
            path_y.append(rb_pos[1] + dy)

        # Draw path line
        ax.plot(path_x[:-1], path_y[:-1], color='#e74c3c',
               linewidth=2.5, linestyle='-', zorder=7, alpha=0.9)
        # Arrow at end
        ax.annotate('', xy=(path_x[-1], path_y[-1]),
                   xytext=(path_x[-2], path_y[-2]),
                   arrowprops=dict(arrowstyle='->', color='#e74c3c',
                                  lw=2.5, mutation_scale=20), zorder=8)

    # QB handoff line (subtle)
    if qb_pos and rb_pos:
        ax.plot([qb_pos[0], rb_pos[0]], [qb_pos[1], rb_pos[1]],
               color='#f0ede8', linewidth=1, linestyle=':', alpha=0.3, zorder=4)

    # Title / play info
    ax.text(0, 5.5, f"{form}", ha='center', va='top',
           color='#f1c40f', fontsize=11, fontweight='bold',
           fontfamily='sans-serif', zorder=10)
    ax.text(0, 5.0, f"{play}", ha='center', va='top',
           color='#f0ede8', fontsize=13, fontweight='bold',
           fontfamily='sans-serif', zorder=10)

    # Info boxes
    info_left = f"DN: {dn}  DIST: {dist}  HASH: {hash_}"
    info_right = f"GN/LS: {gnls}  {result}"
    ax.text(-7.8, -3.6, info_left, ha='left', va='bottom',
           color='rgba(240,237,232,0.55)', fontsize=8,
           fontfamily='monospace', zorder=10)
    ax.text(7.8, -3.6, info_right, ha='right', va='bottom',
           color='rgba(240,237,232,0.55)', fontsize=8,
           fontfamily='monospace', zorder=10)

    # Direction indicator
    dir_x = 6.5 if direction == 'R' else -6.5
    ax.annotate('', xy=(dir_x + (0.8 if direction=='R' else -0.8), 2),
               xytext=(dir_x, 2),
               arrowprops=dict(arrowstyle='->', color='#e74c3c', lw=2.5,
                              mutation_scale=18), zorder=10)
    ax.text(dir_x + (0.4 if direction=='R' else -0.4), 2.5,
           f"{'→' if direction=='R' else '←'} {direction}",
           ha='center', color='#e74c3c', fontsize=9, fontweight='bold', zorder=10)

    # Legend
    legend_items = [('OL', '#1a5276'), ('TE', '#0e7060'), ('WR', '#7d6608'),
                    ('RB', '#c0392b'), ('QB', '#c0392b')]
    for i, (lbl, col) in enumerate(legend_items):
        cx = -7.5 + i*1.6
        circ = Circle((cx, -3.2), 0.2, facecolor=col,
                      edgecolor='#f0ede8', linewidth=1, zorder=10)
        ax.add_patch(circ)
        ax.text(cx+0.35, -3.2, lbl, va='center', color='rgba(240,237,232,0.6)',
               fontsize=7, fontfamily='monospace', zorder=10)

    ax.set_aspect('equal')
    ax.axis('off')
    plt.tight_layout(pad=0.5)
    return fig

# ── STREAMLIT UI ──────────────────────────────────────────────
st.markdown('<div style="font-family:Barlow Condensed,sans-serif;font-weight:900;font-size:56px;line-height:.95;text-transform:uppercase;color:#f0ede8;margin-bottom:8px">Run Card<span style="color:#c0392b">Generator</span></div>', unsafe_allow_html=True)
st.markdown('<div style="font-size:15px;color:rgba(240,237,232,.5);margin-bottom:24px">Upload your Hudl export and automatically generate play diagrams for every run play.</div>', unsafe_allow_html=True)
st.divider()

col1, col2, col3 = st.columns(3)
with col1: opp  = st.text_input("Opponent", placeholder="e.g. Lincoln High")
with col2: week = st.text_input("Week", placeholder="3")
with col3:
    filter_type = st.selectbox("Show plays", ["All Runs", "Runs Only", "Passes Only", "All Plays"])

st.markdown("---")
uploaded = st.file_uploader("Upload Hudl Playlist Export (.xlsx)", type=['xlsx','xls'])

if uploaded:
    df = pd.read_excel(uploaded)
    plays_raw = df[df['PLAY TYPE'].isin(['Run','Pass'])].to_dict('records')

    # Filter
    if filter_type == "Runs Only":
        plays_raw = [p for p in plays_raw if p.get('PLAY TYPE')=='Run']
    elif filter_type == "Passes Only":
        plays_raw = [p for p in plays_raw if p.get('PLAY TYPE')=='Pass']

    st.success(f"✅ Loaded {len(plays_raw)} plays")

    # Group by concept for summary
    concepts = Counter(str(p.get('OFF PLAY','')) for p in plays_raw if p.get('PLAY TYPE')=='Run')
    if concepts:
        st.markdown("**Top Run Concepts in this file:**")
        cols = st.columns(5)
        for i,(concept, count) in enumerate(concepts.most_common(5)):
            cols[i].metric(concept, f"{count} plays")

    st.divider()

    # Filter options
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        all_concepts = sorted(set(str(p.get('OFF PLAY','')) for p in plays_raw if p.get('OFF PLAY')))
        selected_concept = st.selectbox("Filter by Play Concept (optional)", ["All"] + all_concepts)
    with col_f2:
        all_forms = sorted(set(str(p.get('OFF FORM','')) for p in plays_raw if p.get('OFF FORM')))
        selected_form = st.selectbox("Filter by Formation (optional)", ["All"] + all_forms)

    filtered = plays_raw
    if selected_concept != "All":
        filtered = [p for p in filtered if str(p.get('OFF PLAY','')) == selected_concept]
    if selected_form != "All":
        filtered = [p for p in filtered if str(p.get('OFF FORM','')) == selected_form]

    st.markdown(f"**Showing {len(filtered)} plays**")

    if st.button(f"⚡ GENERATE {len(filtered)} RUN CARDS"):
        if len(filtered) == 0:
            st.warning("No plays match your filters.")
        elif len(filtered) > 100:
            st.warning(f"That's {len(filtered)} plays — showing first 50. Use filters to narrow down.")
            filtered = filtered[:50]

        progress = st.progress(0, "Drawing play diagrams...")
        zip_buf = io.BytesIO()

        with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            cols_per_row = 2
            play_groups = [filtered[i:i+cols_per_row] for i in range(0, len(filtered), cols_per_row)]

            for gi, group in enumerate(play_groups):
                cols = st.columns(cols_per_row)
                for pi, play in enumerate(group):
                    progress.progress(int((gi*cols_per_row+pi+1)/len(filtered)*100),
                                     f"Drawing play {gi*cols_per_row+pi+1} of {len(filtered)}...")
                    fig = draw_run_card(play)

                    # Show in app
                    with cols[pi]:
                        st.pyplot(fig, use_container_width=True)
                        form = str(play.get('OFF FORM','')).upper()
                        concept = str(play.get('OFF PLAY',''))
                        direction = str(play.get('PLAY DIR',''))
                        st.caption(f"**{concept}** | {form} | {direction} | DN {play.get('DN','')} & {play.get('DIST','')}")

                    # Save to zip
                    img_buf = io.BytesIO()
                    fig.savefig(img_buf, format='png', dpi=150,
                               bbox_inches='tight', facecolor=fig.get_facecolor())
                    img_buf.seek(0)
                    fname = f"Play_{gi*cols_per_row+pi+1}_{concept}_{form}_{direction}.png".replace(' ','_')
                    zf.writestr(fname, img_buf.read())
                    plt.close(fig)

        progress.progress(100, "Complete!")
        zip_buf.seek(0)
        opp_name = opp or "Opponent"
        st.download_button(
            label="📥 Download All Run Cards (ZIP)",
            data=zip_buf.getvalue(),
            file_name=f"{opp_name}_Week{week}_RunCards.zip",
            mime="application/zip"
        )

st.divider()
st.markdown('<div style="font-family:Share Tech Mono,monospace;font-size:10px;color:rgba(240,237,232,.2);text-align:center;padding:16px 0">© 2026 DEFENSIVEIQ · RUN CARD GENERATOR</div>', unsafe_allow_html=True)
