import streamlit as st
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Circle, FancyArrowPatch
import numpy as np
import io
import json

st.set_page_config(
    page_title="Run Card Builder — DefensiveIQ",
    page_icon="🏈",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700;800;900&family=Barlow:wght@400;500&display=swap');
html,body,[class*="css"]{font-family:'Barlow',sans-serif;background:#0a1628;color:#f0ede8;}
.stApp{background:#0a1628;}
.stButton>button{background:#c0392b!important;color:#f0ede8!important;border:none!important;
  font-family:'Barlow Condensed',sans-serif!important;font-weight:700!important;
  font-size:14px!important;letter-spacing:.1em!important;text-transform:uppercase!important;
  padding:10px 20px!important;border-radius:0!important;width:100%!important;}
.stButton>button:hover{background:#a93226!important;}
.stDownloadButton>button{background:#0e7060!important;color:#f0ede8!important;border:none!important;
  font-family:'Barlow Condensed',sans-serif!important;font-weight:700!important;
  font-size:13px!important;border-radius:0!important;width:100%!important;}
div[data-testid="stNumberInput"] input{background:#1e2d3d!important;color:#f0ede8!important;
  border:1px solid rgba(240,237,232,.15)!important;border-radius:0!important;}
div[data-testid="stTextInput"] input{background:#1e2d3d!important;color:#f0ede8!important;
  border:1px solid rgba(240,237,232,.15)!important;border-radius:0!important;}
div[data-testid="stSelectbox"] > div{background:#1e2d3d!important;border-radius:0!important;}
</style>
""", unsafe_allow_html=True)

# ── Session state init ────────────────────────────────────────
if 'players' not in st.session_state:
    st.session_state.players = []
if 'arrows' not in st.session_state:
    st.session_state.arrows = []
if 'ball_path' not in st.session_state:
    st.session_state.ball_path = []
if 'concept_name' not in st.session_state:
    st.session_state.concept_name = ""
if 'formation_name' not in st.session_state:
    st.session_state.formation_name = ""

# ── Role colors ───────────────────────────────────────────────
ROLE_COLORS = {
    'OL':  ('#1a5276', '#5dade2'),
    'TE':  ('#0e7060', '#2ecc71'),
    'WR':  ('#7d6608', '#f1c40f'),
    'RB':  ('#922b21', '#e74c3c'),
    'FB':  ('#6c3483', '#9b59b6'),
    'QB':  ('#922b21', '#e74c3c'),
    'H':   ('#0e7060', '#2ecc71'),
}
ARROW_COLORS = {
    'Block (White)':  '#ffffff',
    'Pull (Yellow)':  '#f1c40f',
    'Down Block (Green)': '#2ecc71',
    'Ball Path (Red)': '#e74c3c',
    'Pass Route (Blue)': '#5dade2',
}

# ── Draw the card ─────────────────────────────────────────────
def draw_card(players, arrows, ball_path, concept, formation, dn="", dist="", notes=""):
    fig, ax = plt.subplots(figsize=(12, 8))
    fig.patch.set_facecolor('#0a1628')
    ax.set_facecolor('#0d1f38')
    ax.set_xlim(-9, 9)
    ax.set_ylim(-4.5, 6.5)

    # Field markings
    ax.axhline(y=0, color='#f0ede8', linewidth=2.5, alpha=0.9, zorder=1)
    # Hash marks
    for x in [-1.2, 1.2]:
        ax.plot([x, x], [-0.2, 0.2], color='#f0ede8', linewidth=2, alpha=0.6, zorder=2)
    # Yard lines
    for y in [2, 4, -2]:
        ax.axhline(y=y, color='#f0ede8', linewidth=0.4, alpha=0.08, linestyle='--', zorder=1)
    # LOS label
    ax.text(8.5, 0.1, 'LOS', color='#f0ede8', fontsize=7,
            alpha=0.4, va='bottom', ha='right', fontfamily='monospace')

    # Draw arrows
    for arr in arrows:
        x1,y1,x2,y2,color,lw = arr['x1'],arr['y1'],arr['x2'],arr['y2'],arr['color'],arr.get('lw',2)
        ax.annotate('', xy=(x2,y2), xytext=(x1,y1),
                   arrowprops=dict(arrowstyle='->', color=color,
                                  lw=lw, mutation_scale=18), zorder=6)

    # Draw ball path
    if len(ball_path) >= 2:
        bx = [p[0] for p in ball_path]
        by = [p[1] for p in ball_path]
        ax.plot(bx[:-1], by[:-1], color='#e74c3c', linewidth=3, zorder=7)
        ax.annotate('', xy=(bx[-1], by[-1]), xytext=(bx[-2], by[-2]),
                   arrowprops=dict(arrowstyle='->', color='#e74c3c',
                                  lw=3, mutation_scale=22), zorder=8)

    # Draw players
    for p in players:
        x, y, lbl, role = p['x'], p['y'], p['label'], p['role']
        fc, ec = ROLE_COLORS.get(role, ('#555', '#888'))
        if role == 'OL':
            sq = patches.Rectangle((x-0.38, y-0.28), 0.76, 0.56,
                                   linewidth=2, edgecolor=ec, facecolor=fc, zorder=5)
            ax.add_patch(sq)
        else:
            circ = Circle((x, y), 0.36, linewidth=2,
                         edgecolor=ec, facecolor=fc, zorder=5)
            ax.add_patch(circ)
        ax.text(x, y, lbl, ha='center', va='center', color='#f0ede8',
               fontsize=7, fontweight='bold', fontfamily='monospace', zorder=6)

    # Title
    ax.text(0, 6.1, formation.upper(), ha='center', color='#f1c40f',
           fontsize=12, fontweight='bold', fontfamily='sans-serif', zorder=10)
    ax.text(0, 5.6, concept.upper(), ha='center', color='#f0ede8',
           fontsize=15, fontweight='bold', fontfamily='sans-serif', zorder=10)

    # Info
    info = f"DN: {dn}  DIST: {dist}"
    ax.text(-8.5, -4.1, info, ha='left', color='#888888',
           fontsize=8, fontfamily='monospace', zorder=10)
    if notes:
        ax.text(0, -4.1, notes, ha='center', color='#888888',
               fontsize=8, fontfamily='monospace', zorder=10)

    # Legend
    legend = [('OL','#1a5276'),('TE','#0e7060'),('WR','#7d6608'),
              ('RB','#922b21'),('FB','#6c3483')]
    for i,(lbl,col) in enumerate(legend):
        cx = -8 + i*1.8
        c = Circle((cx,-3.6),0.2,facecolor=col,edgecolor='#f0ede8',linewidth=1,zorder=10)
        ax.add_patch(c)
        ax.text(cx+0.35,-3.6,lbl,va='center',color='#888888',
               fontsize=7,fontfamily='monospace',zorder=10)

    ax.set_aspect('equal')
    ax.axis('off')
    plt.tight_layout(pad=0.3)
    return fig

# ── Load preset formation ─────────────────────────────────────
PRESET_FORMATIONS = {
    "Pro / Ace": [
        {'x':-2,'y':0,'label':'LT','role':'OL'},
        {'x':-1,'y':0,'label':'LG','role':'OL'},
        {'x':0, 'y':0,'label':'C', 'role':'OL'},
        {'x':1, 'y':0,'label':'RG','role':'OL'},
        {'x':2, 'y':0,'label':'RT','role':'OL'},
        {'x':3, 'y':0.2,'label':'TE','role':'TE'},
        {'x':-4.5,'y':0,'label':'WR','role':'WR'},
        {'x':4.5, 'y':0,'label':'WR','role':'WR'},
        {'x':0,  'y':-2.5,'label':'RB','role':'RB'},
        {'x':0,  'y':-1,'label':'QB','role':'QB'},
    ],
    "Trey Over": [
        {'x':-2,'y':0,'label':'LT','role':'OL'},
        {'x':-1,'y':0,'label':'LG','role':'OL'},
        {'x':0, 'y':0,'label':'C', 'role':'OL'},
        {'x':1, 'y':0,'label':'RG','role':'OL'},
        {'x':2, 'y':0,'label':'RT','role':'OL'},
        {'x':3, 'y':0.2,'label':'TE','role':'TE'},
        {'x':4.2,'y':0.2,'label':'WR','role':'WR'},
        {'x':-4, 'y':0,'label':'WR','role':'WR'},
        {'x':0,  'y':-2.5,'label':'RB','role':'RB'},
        {'x':0,  'y':-1,'label':'QB','role':'QB'},
    ],
    "Trips 1 Open": [
        {'x':-2,'y':0,'label':'LT','role':'OL'},
        {'x':-1,'y':0,'label':'LG','role':'OL'},
        {'x':0, 'y':0,'label':'C', 'role':'OL'},
        {'x':1, 'y':0,'label':'RG','role':'OL'},
        {'x':2, 'y':0,'label':'RT','role':'OL'},
        {'x':3, 'y':0.4,'label':'WR','role':'WR'},
        {'x':4.5,'y':0,'label':'WR','role':'WR'},
        {'x':5.8,'y':0,'label':'WR','role':'WR'},
        {'x':-4, 'y':0,'label':'WR','role':'WR'},
        {'x':0,  'y':-2.5,'label':'RB','role':'RB'},
        {'x':0,  'y':-1,'label':'QB','role':'QB'},
    ],
    "Deuces": [
        {'x':-2,'y':0,'label':'LT','role':'OL'},
        {'x':-1,'y':0,'label':'LG','role':'OL'},
        {'x':0, 'y':0,'label':'C', 'role':'OL'},
        {'x':1, 'y':0,'label':'RG','role':'OL'},
        {'x':2, 'y':0,'label':'RT','role':'OL'},
        {'x':3.2,'y':0.3,'label':'WR','role':'WR'},
        {'x':4.5,'y':0,'label':'WR','role':'WR'},
        {'x':-3.2,'y':0.3,'label':'WR','role':'WR'},
        {'x':-4.5,'y':0,'label':'WR','role':'WR'},
        {'x':0,  'y':-2.5,'label':'RB','role':'RB'},
        {'x':0,  'y':-1,'label':'QB','role':'QB'},
    ],
    "Empty": [
        {'x':-2,'y':0,'label':'LT','role':'OL'},
        {'x':-1,'y':0,'label':'LG','role':'OL'},
        {'x':0, 'y':0,'label':'C', 'role':'OL'},
        {'x':1, 'y':0,'label':'RG','role':'OL'},
        {'x':2, 'y':0,'label':'RT','role':'OL'},
        {'x':3.2,'y':0.3,'label':'WR','role':'WR'},
        {'x':4.5,'y':0,'label':'WR','role':'WR'},
        {'x':-3.2,'y':0.3,'label':'WR','role':'WR'},
        {'x':-4.5,'y':0,'label':'WR','role':'WR'},
        {'x':1.5,'y':-1.2,'label':'RB','role':'RB'},
        {'x':0,  'y':-1,'label':'QB','role':'QB'},
    ],
    "Blank (OL only)": [
        {'x':-2,'y':0,'label':'LT','role':'OL'},
        {'x':-1,'y':0,'label':'LG','role':'OL'},
        {'x':0, 'y':0,'label':'C', 'role':'OL'},
        {'x':1, 'y':0,'label':'RG','role':'OL'},
        {'x':2, 'y':0,'label':'RT','role':'OL'},
        {'x':0, 'y':-1,'label':'QB','role':'QB'},
    ],
}

# ─────────────────────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────────────────────
st.markdown('<div style="font-family:Barlow Condensed,sans-serif;font-weight:900;font-size:52px;line-height:.95;text-transform:uppercase;color:#f0ede8;margin-bottom:4px">Run Card<span style="color:#c0392b"> Builder</span></div>', unsafe_allow_html=True)
st.markdown('<div style="font-size:14px;color:rgba(240,237,232,.5);margin-bottom:20px">Build your play concepts. Download as cards. Build your library.</div>', unsafe_allow_html=True)
st.divider()

# ── Step 1: Name the play ─────────────────────────────────────
st.markdown("### Step 1 — Name Your Play")
c1, c2, c3, c4 = st.columns(4)
with c1: concept = st.text_input("Play Concept", placeholder="e.g. ZONE LT", value=st.session_state.concept_name)
with c2: formation = st.text_input("Formation", placeholder="e.g. TREY OVER", value=st.session_state.formation_name)
with c3: dn = st.text_input("Down", placeholder="e.g. 1")
with c4: dist = st.text_input("Distance", placeholder="e.g. 10")
notes = st.text_input("Notes (optional)", placeholder="e.g. Best vs Cover 2, needs LT to reach 5-tech")

st.session_state.concept_name = concept
st.session_state.formation_name = formation

st.divider()

# ── Step 2: Load formation ────────────────────────────────────
st.markdown("### Step 2 — Start With a Formation")
col_pre, col_load = st.columns([3,1])
with col_pre:
    preset = st.selectbox("Choose a preset formation", list(PRESET_FORMATIONS.keys()))
with col_load:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Load Formation"):
        st.session_state.players = [dict(p) for p in PRESET_FORMATIONS[preset]]
        st.session_state.arrows = []
        st.session_state.ball_path = []
        st.rerun()

st.divider()

# ── Step 3: Add/Edit Players ──────────────────────────────────
st.markdown("### Step 3 — Add Players")
with st.expander("➕ Add a Player", expanded=False):
    pc1,pc2,pc3,pc4,pc5 = st.columns(5)
    with pc1: p_role  = st.selectbox("Role", list(ROLE_COLORS.keys()))
    with pc2: p_label = st.text_input("Label", value=p_role[:2], max_chars=3)
    with pc3: p_x     = st.number_input("X position", min_value=-9.0, max_value=9.0, value=0.0, step=0.5)
    with pc4: p_y     = st.number_input("Y position", min_value=-4.0, max_value=6.0, value=0.0, step=0.5)
    with pc5:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Add Player"):
            st.session_state.players.append({'x':p_x,'y':p_y,'label':p_label,'role':p_role})
            st.rerun()

# Show current players
if st.session_state.players:
    st.markdown(f"**{len(st.session_state.players)} players on field:**")
    pcols = st.columns(6)
    for i, p in enumerate(st.session_state.players):
        with pcols[i % 6]:
            st.markdown(f"<div style='background:#1e2d3d;padding:6px 8px;margin-bottom:4px;font-size:12px'><b>{p['label']}</b> {p['role']}<br><span style='color:#888;font-size:10px'>({p['x']}, {p['y']})</span></div>", unsafe_allow_html=True)
    if st.button("🗑 Clear All Players"):
        st.session_state.players = []
        st.rerun()

st.divider()

# ── Step 4: Add Arrows ────────────────────────────────────────
st.markdown("### Step 4 — Add Blocking Arrows & Ball Path")

with st.expander("➕ Add an Arrow", expanded=False):
    ac1,ac2,ac3,ac4,ac5,ac6 = st.columns(6)
    with ac1: a_type  = st.selectbox("Arrow Type", list(ARROW_COLORS.keys()))
    with ac2: a_x1    = st.number_input("Start X", min_value=-9.0, max_value=9.0, value=0.0, step=0.5, key="ax1")
    with ac3: a_y1    = st.number_input("Start Y", min_value=-4.0, max_value=6.0, value=0.1, step=0.5, key="ay1")
    with ac4: a_x2    = st.number_input("End X",   min_value=-9.0, max_value=9.0, value=1.0, step=0.5, key="ax2")
    with ac5: a_y2    = st.number_input("End Y",   min_value=-4.0, max_value=6.0, value=0.8, step=0.5, key="ay2")
    with ac6:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Add Arrow"):
            color = ARROW_COLORS[a_type]
            lw = 3.0 if 'Ball' in a_type else (2.0 if 'Pull' in a_type else 1.5)
            st.session_state.arrows.append({
                'x1':a_x1,'y1':a_y1,'x2':a_x2,'y2':a_y2,
                'color':color,'lw':lw,'type':a_type
            })
            st.rerun()

# Ball path builder
with st.expander("🏈 Add Ball Carrier Path Points", expanded=False):
    st.markdown("Add waypoints for the ball carrier's path (connect them in order)")
    bc1,bc2,bc3 = st.columns(3)
    with bc1: bp_x = st.number_input("Path X", min_value=-9.0, max_value=9.0, value=0.0, step=0.5, key="bpx")
    with bc2: bp_y = st.number_input("Path Y", min_value=-4.0, max_value=6.0, value=2.0, step=0.5, key="bpy")
    with bc3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Add Path Point"):
            st.session_state.ball_path.append((bp_x, bp_y))
            st.rerun()
    if st.session_state.ball_path:
        st.markdown(f"Path points: {st.session_state.ball_path}")
        if st.button("Clear Path"):
            st.session_state.ball_path = []
            st.rerun()

# Show arrows
if st.session_state.arrows:
    st.markdown(f"**{len(st.session_state.arrows)} arrows:**")
    for i, a in enumerate(st.session_state.arrows):
        col_a, col_b = st.columns([4,1])
        with col_a:
            st.markdown(f"<div style='background:#1e2d3d;padding:5px 8px;margin-bottom:3px;font-size:11px'>{a['type']} ({a['x1']},{a['y1']}) → ({a['x2']},{a['y2']})</div>", unsafe_allow_html=True)
        with col_b:
            if st.button("✕", key=f"del_arrow_{i}"):
                st.session_state.arrows.pop(i)
                st.rerun()

st.divider()

# ── Step 5: Quick Templates ───────────────────────────────────
st.markdown("### Quick Templates — Common Blocking Schemes")
t1,t2,t3,t4,t5 = st.columns(5)

def add_zone_arrows(d=1):
    st.session_state.arrows = []
    for ox in [-2,-1,0,1,2]:
        st.session_state.arrows.append({'x1':ox,'y1':0.1,'x2':ox+d*0.8,'y2':0.7,'color':'#ffffff','lw':1.5,'type':'Block'})

def add_counter_arrows(d=1):
    st.session_state.arrows = []
    st.session_state.arrows.append({'x1':d*2,'y1':0.1,'x2':d*2-d*0.4,'y2':0.7,'color':'#2ecc71','lw':1.5,'type':'Down'})
    st.session_state.arrows.append({'x1':d*1,'y1':0.1,'x2':d*1-d*0.3,'y2':0.7,'color':'#2ecc71','lw':1.5,'type':'Down'})
    st.session_state.arrows.append({'x1':0,'y1':0.1,'x2':-d*0.3,'y2':0.7,'color':'#ffffff','lw':1.5,'type':'Block'})
    st.session_state.arrows.append({'x1':-d*1,'y1':0.1,'x2':d*3.0,'y2':0.9,'color':'#f1c40f','lw':2.5,'type':'Pull'})
    st.session_state.arrows.append({'x1':-d*2,'y1':0.1,'x2':d*3.5,'y2':0.5,'color':'#f1c40f','lw':2.5,'type':'Pull'})

def add_power_arrows(d=1):
    st.session_state.arrows = []
    st.session_state.arrows.append({'x1':d*2,'y1':0.1,'x2':d*2+d*0.3,'y2':0.7,'color':'#ffffff','lw':1.5,'type':'Block'})
    st.session_state.arrows.append({'x1':d*1,'y1':0.1,'x2':d*1-d*0.3,'y2':0.7,'color':'#2ecc71','lw':1.5,'type':'Down'})
    st.session_state.arrows.append({'x1':0,'y1':0.1,'x2':d*0.3,'y2':0.6,'color':'#ffffff','lw':1.5,'type':'Block'})
    st.session_state.arrows.append({'x1':-d*1,'y1':0.1,'x2':d*3.2,'y2':0.9,'color':'#f1c40f','lw':2.5,'type':'Pull'})
    st.session_state.arrows.append({'x1':-d*2,'y1':0.1,'x2':-d*2-d*0.2,'y2':0.6,'color':'#ffffff','lw':1.5,'type':'Block'})

with t1:
    if st.button("Zone Right"):
        add_zone_arrows(1); st.rerun()
with t2:
    if st.button("Zone Left"):
        add_zone_arrows(-1); st.rerun()
with t3:
    if st.button("Counter Right"):
        add_counter_arrows(1); st.rerun()
with t4:
    if st.button("Counter Left"):
        add_counter_arrows(-1); st.rerun()
with t5:
    if st.button("Power Right"):
        add_power_arrows(1); st.rerun()

st.divider()

# ── Step 6: Preview & Download ────────────────────────────────
st.markdown("### Step 6 — Preview & Download")

if st.button("⚡ PREVIEW CARD"):
    if not st.session_state.players:
        st.warning("Add some players first — use Step 2 to load a formation.")
    else:
        fig = draw_card(
            st.session_state.players,
            st.session_state.arrows,
            st.session_state.ball_path,
            concept or "PLAY CONCEPT",
            formation or "FORMATION",
            dn, dist, notes
        )
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

        # Download button
        fig2 = draw_card(
            st.session_state.players,
            st.session_state.arrows,
            st.session_state.ball_path,
            concept or "PLAY CONCEPT",
            formation or "FORMATION",
            dn, dist, notes
        )
        buf = io.BytesIO()
        fig2.savefig(buf, format='png', dpi=200, bbox_inches='tight', facecolor='#0a1628')
        buf.seek(0)
        plt.close(fig2)
        fname = f"{concept or 'card'}_{formation or 'form'}.png".replace(' ','_').upper()
        st.download_button(
            label="📥 Download Card (PNG)",
            data=buf.getvalue(),
            file_name=fname,
            mime="image/png"
        )

        # Save as JSON for future import
        card_data = {
            'concept': concept,
            'formation': formation,
            'dn': dn,
            'dist': dist,
            'notes': notes,
            'players': st.session_state.players,
            'arrows': st.session_state.arrows,
            'ball_path': st.session_state.ball_path,
        }
        json_buf = json.dumps(card_data, indent=2).encode()
        st.download_button(
            label="💾 Save Card Data (JSON — reload later)",
            data=json_buf,
            file_name=fname.replace('.PNG','.json'),
            mime="application/json"
        )

st.divider()

# ── Import saved card ─────────────────────────────────────────
st.markdown("### Load a Saved Card")
uploaded_json = st.file_uploader("Upload a saved card (.json)", type=['json'])
if uploaded_json:
    data = json.load(uploaded_json)
    st.session_state.players      = data.get('players', [])
    st.session_state.arrows       = data.get('arrows', [])
    st.session_state.ball_path    = [tuple(p) for p in data.get('ball_path', [])]
    st.session_state.concept_name = data.get('concept', '')
    st.session_state.formation_name = data.get('formation', '')
    st.success(f"Loaded: {data.get('concept','')} — {data.get('formation','')}")
    st.rerun()

st.divider()
st.markdown('<div style="font-family:Share Tech Mono,monospace;font-size:10px;color:rgba(240,237,232,.2);text-align:center;padding:16px 0">© 2026 DEFENSIVEIQ · RUN CARD BUILDER</div>', unsafe_allow_html=True)
