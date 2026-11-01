"""Calculations and figures (English version) for the study "The Vaavu cave tragedy (Maldives, 2026)".

Usage:  python3 calculos_y_figuras_en.py <figures_folder> <maldives.geojson> > calculations_en.txt

All calculations are for educational purposes. Do NOT use them to plan real dives.
"""
import json, math, sys, os, textwrap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, FancyBboxPatch, Rectangle, FancyArrowPatch, Ellipse, ConnectionPatch
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else "figs_en"
GEO = sys.argv[2] if len(sys.argv) > 2 else "maldives.geojson"
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.titleweight": "bold", "axes.titlesize": 12})
SEA = "#cfe6f2"; LAND = "#efe6d4"; COAST = "#8a7a5c"; INK = "#1f2d3a"
DEEP = "#0b3d5c"; ACC = "#d64545"; WARN = "#f08a24"; OK = "#2f8f5b"; ROCK = "#b9a27a"; SAND = "#e6d9b0"

def save(fig, name):
    fig.savefig(f"{OUT}/{name}.png", dpi=200, bbox_inches="tight", facecolor="white"); plt.close(fig)

def es(x, d=1):
    """English number format."""
    s = f"{x:,.{d}f}"
    return s

# =====================================================================
# 1. CÁLCULOS
# =====================================================================
def P(d): return 1 + d / 10
RHO_AIR = 1.225  # g/L a 1 bar, 15 °C

print("=== 1. Pressure, partial pressures and density of AIR ===")
print(f"{'Depth (m)':>9} {'P (bar)':>8} {'ppO2':>6} {'ppN2':>6} {'dens g/L':>9} {'martinis':>8}")
for d in [0, 30, 40, 47, 50, 56.7, 60, 66, 69, 70]:
    print(f"{d:8.1f} {P(d):8.2f} {0.21*P(d):6.2f} {0.79*P(d):6.2f} {RHO_AIR*P(d):9.2f} {max(0,(d-20)/10):8.1f}")
print(f"\nMOD of air: 1.4 bar -> {10*(1.4/0.21-1):.1f} m ; 1.6 bar -> {10*(1.6/0.21-1):.1f} m")
print(f"Density 5.2 g/L on air at {10*(5.2/RHO_AIR-1):.1f} m ; 6.2 g/L at {10*(6.2/RHO_AIR-1):.1f} m")
print(f"Nitrox 28 at 60 m: ppO2 = {0.28*P(60):.2f} bar")
tmx = (0.18, 0.45, 0.37)
print(f"Trimix 18/45 at 60 m: ppO2 = {tmx[0]*P(60):.2f} bar ; END = {((tmx[2]*P(60))/0.79-1)*10:.1f} m")

print("\n=== 2. Duration of a 12 L cylinder at 200 bar (2,400 L) at 60 m ===")
GAS = 12 * 200
SACS = [("Very relaxed", 15), ("Normal", 20), ("Effort", 30), ("Stress", 45), ("Panic", 60)]
for n, s in SACS:
    print(f"{n:13s} SAC {s:2d} L/min -> {s*P(60):5.0f} L/min at 60 m -> {GAS/(s*P(60)):5.1f} min")
print(f"Rule of thirds (SAC 20): time to swim in = {GAS/3/(20*P(60)):.1f} min")

# --- Bühlmann ZH-L16C con factores de gradiente (solo divulgativo) ---
HT = [5.0, 8.0, 12.5, 18.5, 27.0, 38.3, 54.3, 77.0, 109.0, 146.0, 187.0, 239.0, 305.0, 390.0, 498.0, 635.0]
A = [1.1696, 1.0, 0.8618, 0.7562, 0.62, 0.5043, 0.441, 0.4, 0.375, 0.35, 0.3295, 0.3065, 0.2835, 0.261, 0.248, 0.2327]
B = [0.5578, 0.6514, 0.7222, 0.7825, 0.8126, 0.8434, 0.8693, 0.891, 0.9092, 0.9222, 0.9319, 0.9403, 0.9477, 0.9544, 0.9602, 0.9653]
WV, FN2 = 0.0627, 0.79

def _seg(t, d0, d1, p):
    for i in range(16):
        k = math.log(2) / HT[i]; pi0 = (P(d0) - WV) * FN2
        r = ((P(d1) - P(d0)) / t if t > 0 else 0) * FN2
        p[i] = pi0 + r * (t - 1 / k) - (pi0 - p[i] - r / k) * math.exp(-k * t)

def _ceil(p, gf):
    return max(0, (max((p[i] - A[i] * gf) / (gf / B[i] - gf + 1) for i in range(16)) - 1) * 10)

def deco(bt, depth=60, gflo=.30, gfhi=.85, sac=20, desc=20, asc=9, stop=3):
    p = [(1 - WV) * FN2] * 16; gas = 0.0; prof = [(0, 0)]
    td = depth / desc; _seg(td, 0, depth, p); gas += sac * td * (P(0) + P(depth)) / 2
    _seg(bt - td, depth, depth, p); gas += sac * (bt - td) * P(depth); prof += [(td, depth), (bt, depth)]
    t = bt; run = 0.0
    def go(d0, d1):
        nonlocal gas, t, run
        tt = (d0 - d1) / asc; _seg(tt, d0, d1, p); gas += sac * tt * (P(d0) + P(d1)) / 2; t += tt; run += tt; prof.append((t, d1))
    first = math.ceil(_ceil(p, gflo) / stop) * stop
    go(depth, first); d = first
    while d > 0:
        nxt = d - stop if d - stop >= stop else 0
        gfn = gfhi + (gflo - gfhi) * (nxt / first) if first > 0 else gfhi
        while _ceil(p, gfn) > nxt + 1e-6:
            _seg(1, d, d, p); gas += sac * P(d); t += 1; run += 1
        prof.append((t, d)); go(d, nxt); d = nxt
    return run, gas, prof

print("\n=== 3. Decompression on air at 60 m (Bühlmann ZH-L16C, GF 30/85, SAC 20, descent 20 m/min, ascent 9 m/min) ===")
DECO = {}
for bt in (20, 30, 45):
    run, gas, prof = deco(bt); DECO[bt] = (run, gas, prof)
    print(f"Bottom time {bt} min -> ascent {run:5.0f} min ; total gas {gas:6.0f} L ; available {GAS} L ; x{gas/GAS:.1f}")
print("\nWARNING: educational calculations only. Do not use them to dive.")

# =====================================================================
# 2. FIGURAS
# =====================================================================
feats = json.load(open(GEO))["features"]

# ---- Mapa de Maldivas ----
fig, ax = plt.subplots(figsize=(4.6, 9))
ax.set_facecolor(SEA)
for f in feats:
    g = f["geometry"]; polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    mal = f["properties"]["name"] == "Maldives"
    for poly in polys:
        ring = np.array(poly[0])
        ax.add_patch(Polygon(ring, closed=True, fc=("#2f8f5b" if mal else LAND), ec=("#1f6b43" if mal else COAST), lw=0.8 if mal else 0.5))
ax.set_xlim(71.6, 74.6); ax.set_ylim(-1.0, 7.6); ax.set_aspect(1)
ax.axhline(0, color="#7a96a8", lw=0.8, ls="--"); ax.text(71.7, 0.1, "Equator", fontsize=8, color="#4a6577")
ax.plot(73.509, 4.175, "o", color=INK, ms=5); ax.text(73.6, 4.18, "Malé", fontsize=9, va="center", fontweight="bold")
ax.add_patch(Rectangle((73.3, 3.15), 0.55, 0.6, fill=False, ec=ACC, lw=1.6))
ax.text(73.9, 3.45, "VAAVU", color=ACC, fontsize=10, fontweight="bold", va="center")
ax.plot(73.5056, 3.59, "*", color=ACC, ms=12, mec="white")
ax.text(71.75, 7.2, "Indian Ocean", fontsize=9, color=DEEP, style="italic")
ax.set_title("Maldives: 26 atolls\nand the location of Vaavu", fontsize=11)
ax.set_xlabel("Longitude (°E)"); ax.set_ylabel("Latitude (°N)"); ax.grid(color="white", lw=0.5)
save(fig, "mapa_maldivas")

# ---- Mapa de Vaavu ----
def dms(d, m, s): return d + m / 60 + s / 3600
isl = [("Fulidhoo", dms(3, 40, 49), dms(73, 24, 57), "hab"), ("Dhiggiri (resort)", dms(3, 38, 42), dms(73, 29, 14), "res"),
       ("Alimathaa (resort)", dms(3, 35, 37), dms(73, 29, 52), "res"), ("Thinadhoo", dms(3, 29, 15), dms(73, 32, 17), "hab"),
       ("Felidhoo (capital)", dms(3, 28, 18), dms(73, 32, 50), "hab"), ("Keyodhoo", dms(3, 27, 43), dms(73, 33, 0), "hab"),
       ("Rakeedhoo", dms(3, 18, 53), dms(73, 28, 11), "hab")]
cave = (dms(3, 35, 24), dms(73, 30, 20))
fig, ax = plt.subplots(figsize=(7.4, 8.2))
ax.set_facecolor("#a9cfe6")
rim = [(73.395, 3.69), (73.43, 3.71), (73.49, 3.66), (73.515, 3.59), (73.545, 3.50), (73.56, 3.44), (73.53, 3.37),
       (73.49, 3.30), (73.46, 3.29), (73.43, 3.36), (73.40, 3.48), (73.385, 3.60)]
ax.add_patch(Polygon([(x, y) for x, y in rim], closed=True, fc="#d8f0f7", ec="#e9d8a6", lw=7, alpha=0.95))
ax.text(73.46, 3.50, "Lagoon\n(~30–60 m)", ha="center", fontsize=9, color=DEEP, style="italic")
for n, la, lo, kind in isl:
    ax.plot(lo, la, "s" if kind == "res" else "o", color=("#7a4fbf" if kind == "res" else INK), ms=6, mec="white")
    right = lo > 73.5 and not n.startswith("Alimathaa")
    dy = 0.012 if n.startswith("Alimathaa") else 0
    ax.text(lo + (0.012 if right else -0.012), la + dy, n, fontsize=8.5, ha="left" if right else "right", va="center", color=INK)
ax.plot(cave[1], cave[0], "*", color=ACC, ms=13, mec="white", zorder=5)
ax.annotate("CAVE (Devana / Dhekunu Kandu)\n3°35′24″ N · 73°30′20″ E\nentrance ~47–58 m · interior ~60–70 m", (cave[1], cave[0]),
            (73.555, 3.63), fontsize=8.5, color=ACC, fontweight="bold", arrowprops=dict(arrowstyle="->", color=ACC, lw=1.2))
ax.annotate("", (73.56, 3.555), (73.505, 3.59), arrowprops=dict(arrowstyle="<->", color=DEEP, lw=1.4, ls="--"))
ax.text(73.545, 3.555, "channel (kandu):\ntidal currents", fontsize=7.5, color=DEEP)
ax.text(73.6, 3.40, "OPEN OCEAN\n(> 1,000 m)", fontsize=9, color=DEEP, fontweight="bold", ha="center")
ax.text(73.6, 3.30, "→ Fotteyo reef,\neasternmost point\nof the Maldives", fontsize=7.5, color=DEEP, ha="center")
ax.text(73.33, 3.70, "↑ Malé ~64 km", fontsize=8, color=INK)
km = 5 / 111.32
ax.plot([73.34, 73.34 + km], [3.26, 3.26], color=INK, lw=3); ax.text(73.34 + km / 2, 3.268, "5 km", ha="center", fontsize=8)
ax.set_xlim(73.32, 73.67); ax.set_ylim(3.24, 3.74); ax.set_aspect(1)
ax.plot([], [], "o", color=INK, label="inhabited island"); ax.plot([], [], "s", color="#7a4fbf", label="resort island")
ax.legend(loc="lower right", fontsize=8)
ax.set_title("Vaavu (Felidhu) Atoll: islands and cave\n(islands at real coordinates; reef outline approximate)", fontsize=11)
ax.set_xlabel("Longitude (°E)"); ax.set_ylabel("Latitude (°N)"); ax.grid(color="white", lw=0.4, alpha=0.6)
save(fig, "mapa_vaavu")

# ---- Zonas de vida ----
fig = plt.figure(figsize=(9.5, 8.6))
axL = fig.add_axes([0.07, 0.05, 0.16, 0.88]); axR = fig.add_axes([0.25, 0.05, 0.74, 0.88])
axL.set_ylim(75, 0); axL.set_xlim(0, 1)
for i in range(75): axL.axhspan(i, i + 1, color=plt.cm.Blues(0.2 + 0.75 * i / 75), lw=0)
for k, (dd, c) in enumerate([(5, "#d62828"), (15, "#f77f00"), (25, "#fcbf49"), (40, "#4caf50")]):
    axL.plot([0.12 + k * 0.17] * 2, [0, dd], color=c, lw=6, solid_capstyle="butt")
axL.axhspan(55, 75, xmin=0.55, xmax=1, color="#05121c")
axL.text(0.78, 66, "cave:\nno light", color="white", fontsize=7, ha="center")
axL.axhline(30, color=OK, ls="--", lw=1.3); axL.axhline(56.7, color=WARN, ls="--", lw=1.3)
axL.set_xticks([]); axL.set_ylabel("Depth (m)")
axR.set_xlim(0, 1); axR.set_ylim(5, 0); axR.axis("off")
zones = [(0, 10, "Shallow reef and lagoon", "Hard corals, butterflyfish and parrotfish, clownfish in their anemones, turtles. At night, at the Alimatha jetty, dozens of nurse sharks and stingrays."),
         (10, 30, "Channel wall (recreational zone · legal limit 30 m)", "Grey reef sharks facing the current, eagle rays, Napoleon wrasse, barracuda, giant trevally and mantas at cleaning stations. Soft corals and sea fans."),
         (30, 45, "Deep wall", "Less light and less hard coral. Large sea fans, black coral and sponges. Whitetip reef sharks resting on ledges."),
         (45, 58, "Mesophotic zone: cave mouth", "Faint blue light. Orange sun coral (Tubastraea) on ceilings and overhangs: it needs no light. The cave opens here (~47–58 m)."),
         (58, 75, "Inside the cave: total darkness", "Not a single photon of light. A floor of fine sand that rises with one fin kick. Cave-specific fauna according to Tochilov. Air is already past its oxygen limit (56.7 m).")]
cols = ["#e8f4fa", "#d3eaf5", "#bcdcee", "#9cc6e2", "#4f6f86"]
for i, (top, bot, title, desc) in enumerate(zones):
    y0 = i + 0.06; dark = i == 4
    axR.add_patch(FancyBboxPatch((0.03, y0), 0.95, 0.86, boxstyle="round,pad=0.01", fc=cols[i], ec="#8fb0c8"))
    axR.text(0.06, y0 + 0.12, f"{top}–{bot} m · {title}", fontsize=10.2, fontweight="bold", va="top", color="white" if dark else DEEP)
    axR.text(0.06, y0 + 0.36, textwrap.fill(desc, 88), fontsize=8.5, va="top", color="white" if dark else INK)
    fig.add_artist(ConnectionPatch((1, (top + bot) / 2), (0.03, y0 + 0.43), "data", "data", axesA=axL, axesB=axR, color="#8899aa", lw=0.8))
fig.suptitle("What you see at each depth in the Vaavu channels", fontweight="bold", fontsize=13, y=0.985)
save(fig, "zonas_vida")

# ---- Corte de la cueva ----
fig, ax = plt.subplots(figsize=(10, 5.8))
ax.set_xlim(-25, 160); ax.set_ylim(80, -6)
for i in range(80): ax.axhspan(i, i + 1, color=plt.cm.Blues(0.25 + 0.65 * i / 80), lw=0)
ax.axhspan(-6, 0, color="#f7fbff", lw=0)
ax.add_patch(Polygon([(-25, 0), (2, 0), (5, 20), (8, 47), (8, 80), (-25, 80)], fc="#9fc3d8", ec="none", alpha=0.0))
wall = [(8, 0), (160, 0), (160, 80), (8, 80), (8, 58), (8, 47), (5, 20)]
ax.add_patch(Polygon([(5, 0), (160, 0), (160, 80), (8, 80)], fc=ROCK, ec="#7a6648"))
# cueva excavada
cav1 = Ellipse((32, 56), 40, 18, fc="#123a55", ec="#0a2333")
ax.add_patch(Polygon([(6, 48), (16, 49), (16, 60), (6, 58)], fc="#1d4f72", ec="none"))
ax.add_patch(cav1)
ax.add_patch(Polygon([(50, 54), (82, 58), (82, 64), (50, 60)], fc="#0d2a3e", ec="#0a2333"))
cav2 = Ellipse((102, 63), 44, 20, fc="#05121c", ec="#0a2333"); ax.add_patch(cav2)
ax.add_patch(Polygon([(118, 66), (150, 69), (150, 73), (117, 71)], fc="#05121c", ec="#0a2333"))
ax.add_patch(Ellipse((100, 71.5), 22, 4.5, fc=SAND, ec="#b9a77a"))
ax.text(100, 76.5, "fine sand floor", ha="center", fontsize=7.5, color=INK)
ax.text(32, 52, "1st chamber\n(some light)", ha="center", color="white", fontsize=8.5, fontweight="bold")
ax.text(66, 51.5, "tunnel ~30 m × 3 m", ha="center", color="white", fontsize=8)
ax.text(100, 60, "2nd chamber\n(no light)", ha="center", color="white", fontsize=8.5, fontweight="bold")
ax.text(134, 64.5, "blind side tunnel", ha="center", color=INK, fontsize=8, fontweight="bold")
ax.plot([146, 143, 140, 137], [71, 71.2, 70.8, 71.3], "x", color=ACC, ms=7, mew=2)
ax.text(140, 78.5, "4 victims", ha="center", color=INK, fontsize=8.5, fontweight="bold")
ax.plot(14, 54, "x", color="#ffd166", ms=8, mew=2); ax.text(-12, 70, "guide (near\nthe entrance)", color="white", fontsize=7.5, ha="center")
ax.annotate("", (8, 47), (8, 58), arrowprops=dict(arrowstyle="<->", color="white"))
ax.text(-2, 44, "mouth\n47–58 m", color="white", fontsize=8, ha="center", fontweight="bold")
ax.axhline(30, color=OK, ls="--", lw=1.3); ax.text(-24, 28.8, "30 m · legal limit in the Maldives", color="white", fontsize=8.5, fontweight="bold")
ax.axhline(56.7, color=WARN, ls="--", lw=1.3); ax.text(60, 40.8, "56.7 m · O₂ in air exceeds 1.4 bar", color="white", fontsize=8.5, fontweight="bold")
ax.annotate("", (60, 55.6), (60, 42), arrowprops=dict(arrowstyle="-", color=WARN, lw=0.8))
ax.text(-10, -2, "Channel (kandu)", fontsize=9, color=INK, fontweight="bold", ha="center")
ax.text(80, -2, "Reef wall", fontsize=9, color=INK, fontweight="bold", ha="center")
ax.set_ylabel("Depth (m)"); ax.set_xlabel("Approximate horizontal distance (m) · schematic, not exactly to scale")
ax.set_title("Schematic cross-section of the cave (based on DAN Europe and the recovery divers)")
save(fig, "corte_cueva")

# ---- Planta de la cueva ----
fig, ax = plt.subplots(figsize=(10, 5.6))
ax.set_facecolor(ROCK); ax.set_xlim(-10, 170); ax.set_ylim(-45, 45); ax.set_aspect(1)
ax.add_patch(Rectangle((-10, -45), 14, 90, fc="#5f97bd", ec="none")); ax.text(-3, 0, "open water\n(channel)", rotation=90, ha="center", va="center", color="white", fontsize=9, fontweight="bold")
ax.add_patch(Polygon([(4, -8), (14, -10), (14, 10), (4, 8)], fc="#1d4f72"))
ax.add_patch(Ellipse((32, 0), 40, 32, fc="#123a55")); ax.text(32, 0, "1st chamber\n(cavern)", ha="center", va="center", color="white", fontsize=9, fontweight="bold")
ax.add_patch(Polygon([(50, 4), (82, 6), (82, 12), (50, 10)], fc="#0d2a3e")); ax.text(66, 15.5, "entry tunnel\n~30 m", ha="center", fontsize=8, color=INK)
ax.add_patch(Ellipse((108, 2), 52, 50, fc="#05121c"))
ax.text(110, -17, "2nd chamber\n(total darkness)", ha="center", color="white", fontsize=9, fontweight="bold")
ax.add_patch(Ellipse((90, 5), 14, 9, fc=SAND, ec="#b9a77a")); ax.text(90, 5, "sand\nmound", ha="center", va="center", fontsize=7, color=INK)
ax.add_patch(Polygon([(82, -4), (55, -8), (55, -2), (82, 1)], fc="#05121c"))
ax.text(58, -15, "blind side tunnel\n(not mapped)", ha="center", fontsize=8, color=ACC, fontweight="bold")
for x, y in [(58, -5), (61, -4.6), (64, -5.4), (67, -4.4)]: ax.plot(x, y, "x", color=ACC, ms=7, mew=2)
ax.plot(14, 2, "x", color="#ffd166", ms=8, mew=2); ax.text(16, -22, "guide, near the entrance", fontsize=7.5, color="white")
ax.annotate("", (14, 1), (18, -19), arrowprops=dict(arrowstyle="-", color="white", lw=0.7))
ax.annotate("", (128, 12), (84, 10), arrowprops=dict(arrowstyle="->", color="#7fd1ff", lw=2))
ax.text(125, 16, "in", color="#7fd1ff", fontsize=9, fontweight="bold")
ax.annotate("", (84, -2), (125, -4), arrowprops=dict(arrowstyle="->", color=ACC, lw=2, ls="--"))
ax.text(108, -7, "way back: with the sand stirred up,\nthe side opening looks like the exit", color="#ffb3b3", fontsize=7.5, ha="center")
ax.set_xticks([]); ax.set_yticks([])
ax.set_title("Plan view (schematic): why the side tunnel looks like the exit")
save(fig, "planta_cueva")

# ---- Cronología ----
ev = [("10 May", "Duke of York leaves Malé"), ("14 May 11:00", "Dive starts (planned 1 h)"), ("14 May 12:00", "Not back: search begins"),
      ("14 May", "Guide found at the mouth"), ("16 May", "Sgt Mahudhee (MNDF) dies"), ("17 May", "Finnish team arrives (DAN)"),
      ("18 May", "4 bodies found in the side tunnel"), ("19–20 May", "Bodies recovered"), ("21 May", "Lines and equipment removed"),
      ("25–26 May", "Autopsies in Italy"), ("4–5 Oct", "Expert report: anoxia in all five")]
fig, ax = plt.subplots(figsize=(10, 4.8)); ax.axis("off"); ax.set_xlim(0, len(ev) + 0.5); ax.set_ylim(-3.4, 3.4)
ax.plot([0.3, len(ev) + 0.2], [0, 0], color=DEEP, lw=3)
for i, (d, t) in enumerate(ev):
    x = i + 0.7; up = i % 2 == 0; y = 1.4 if up else -1.4
    c = ACC if ("Mahudhee" in t or "anoxia" in t) else (OK if "found in" in t else DEEP)
    ax.plot(x, 0, "o", color=c, ms=10, mec="white"); ax.plot([x, x], [0, y * 0.75], color="#8899aa", lw=1)
    ax.text(x, y, f"{d}\n" + textwrap.fill(t, 15), ha="center", va="bottom" if up else "top", fontsize=7.8, color=INK,
            bbox=dict(fc="white", ec=c, boxstyle="round,pad=0.3"))
ax.set_title("Timeline of the accident and the recovery (2026)")
save(fig, "cronologia")

# ---- Gases ----
d = np.linspace(0, 80, 321); Pd = 1 + d / 10
fig, axs = plt.subplots(1, 3, figsize=(12, 4.2))
for a in axs: a.axvspan(47, 70, color="#05121c", alpha=0.12); a.grid(alpha=0.3); a.set_xlabel("Depth (m)")
axs[0].plot(d, 0.21 * Pd, color=ACC, lw=2.2, label="Air"); axs[0].plot(d, 0.28 * Pd, color=WARN, lw=1.6, ls="--", label="Nitrox 28 (unconfirmed)")
axs[0].plot(d, 0.18 * Pd, color=OK, lw=2, label="Trimix 18/45"); axs[0].axhline(1.4, color="#555", ls="--"); axs[0].axhline(1.6, color="#555", ls=":")
axs[0].text(1, 1.43, "1.4 bar", fontsize=8); axs[0].text(1, 1.63, "1.6 bar", fontsize=8)
axs[0].set_ylabel("ppO₂ (bar)"); axs[0].set_title("Oxygen"); axs[0].legend(fontsize=7.5, loc="upper left")
axs[1].plot(d, 0.79 * Pd, color=ACC, lw=2.2, label="Air"); axs[1].plot(d, 0.37 * Pd, color=OK, lw=2, label="Trimix 18/45")
axs[1].set_ylabel("ppN₂ (bar)"); axs[1].set_title("Nitrogen (narcosis)"); axs[1].legend(fontsize=7.5, loc="upper left")
rho_t = 0.18 * 1.429 + 0.45 * 0.1786 + 0.37 * 1.2506
axs[2].plot(d, RHO_AIR * Pd, color=ACC, lw=2.2, label="Air"); axs[2].plot(d, rho_t * Pd, color=OK, lw=2, label="Trimix 18/45")
axs[2].axhline(5.2, color="#555", ls="--"); axs[2].axhline(6.2, color="#555", ls=":")
axs[2].text(1, 5.35, "5.2 g/L", fontsize=8); axs[2].text(1, 6.35, "6.2 g/L", fontsize=8)
axs[2].set_ylabel("Density (g/L)"); axs[2].set_title("Density (work of breathing)"); axs[2].legend(fontsize=7.5, loc="upper left")
axs[0].text(58.5, 0.15, "cave", fontsize=8, ha="center")
fig.suptitle("What happens to the breathing gas in the cave (dark band: 47–70 m)", fontweight="bold"); fig.tight_layout()
save(fig, "gases")

# ---- Autonomía ----
fig, ax = plt.subplots(figsize=(8.5, 4.2))
mins = [GAS / (s * P(60)) for _, s in SACS]; labels = [f"{n}\n(SAC {s})" for n, s in SACS]
bars = ax.bar(labels, mins, color=[OK, "#5b8fb0", WARN, "#e0662f", ACC])
for b, m in zip(bars, mins): ax.text(b.get_x() + b.get_width() / 2, m + 0.4, f"≈ {es(m,0)} min", ha="center", fontsize=9, fontweight="bold")
ax.axhline(GAS / 3 / (20 * P(60)), color=INK, ls="--", label="rule of thirds (SAC 20): < 6 min to swim in"); ax.legend(loc="upper right", fontsize=8.5)
ax.set_ylabel("Minutes of air"); ax.set_ylim(0, 27)
ax.set_title("How long does a 12 L cylinder at 200 bar last at 60 m?")
save(fig, "autonomia")

# ---- Descompresión: gas necesario vs disponible ----
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.3), gridspec_kw={"width_ratios": [1, 1.35]})
bts = [20, 30, 45]; need = [DECO[b][1] for b in bts]
bb = a1.bar([f"{b} min\non the bottom" for b in bts], need, color=[WARN, "#e0662f", ACC])
a1.axhline(GAS, color=OK, lw=2.5, label="gas available: 2,400 L"); a1.legend(loc="upper left", fontsize=8.5)
for b, n in zip(bb, need): a1.text(b.get_x() + b.get_width() / 2, n + 300, f"{es(n,0)} L\n(×{es(n/GAS,1)})", ha="center", fontsize=8.5)
a1.set_ylabel("Total gas required (surface litres)"); a1.set_ylim(0, 17500); a1.set_title("Gas required versus gas available")
for b, c in zip(bts, [WARN, "#e0662f", ACC]):
    pr = DECO[b][2]; a2.plot([p[0] for p in pr], [p[1] for p in pr], color=c, lw=2, label=f"{b} min at 60 m → ascent {es(DECO[b][0],0)} min")
a2.set_ylim(65, -3); a2.set_xlabel("Time (min)"); a2.set_ylabel("Depth (m)"); a2.grid(alpha=0.3); a2.legend(fontsize=8)
a2.set_title("Decompression profiles on air")
fig.suptitle("Bühlmann ZH-L16C, GF 30/85, SAC 20 L/min · educational only, do NOT use to dive", fontsize=9, y=0.02)
fig.tight_layout(rect=(0, 0.04, 1, 1))
save(fig, "deco_gas")

# ---- Cadena de errores ----
fig, ax = plt.subplots(figsize=(10, 3.5)); ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(0, 3.2)
steps = ["Cave dive\nnot declared", "47–70 m with a\n30 m legal limit", "Air,\nnot trimix", "A single\n12 L cylinder", "No\nguideline",
         "No cave\ntraining", "Sand + darkness\n+ unmapped tunnel", "Blind tunnel and\nair exhausted", "Anoxia"]
cols = ["#e9eef3"] * 6 + [ACC, WARN, INK]
pos = [(0.1 + i * 2.0, 1.85) for i in range(5)] + [(8.1 - i * 2.0, 0.25) for i in range(4)]
for i, (s_, c) in enumerate(zip(steps, cols)):
    x, y = pos[i]
    ax.add_patch(FancyBboxPatch((x, y), 1.7, 0.95, boxstyle="round,pad=0.04", fc=c, ec="#8899aa"))
    ax.text(x + 0.85, y + 0.475, s_, ha="center", va="center", fontsize=8.5, color="white" if c in (ACC, INK, WARN) else INK, fontweight="bold")
    if i < len(steps) - 1:
        x2, y2 = pos[i + 1]
        if y2 == y:
            a, b = ((x + 1.74, y + .475), (x2 - .04, y + .475)) if x2 > x else ((x - .04, y + .475), (x2 + 1.74, y + .475))
        else:
            a, b = (x + .85, y - .05), (x2 + .85, y2 + .99)
        ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=14, color="#556", lw=1.3))
ax.set_title("The chain of errors (Swiss cheese model)")
save(fig, "cadena_errores")
print("\nFigures generated in:", OUT)
