#!/usr/bin/env python3
"""Forest plot of the headline effect sizes in plasma_geophysics.json.

Usage: python3 -I omega/plasma_geophysics_plot.py <out.png>
"""
import json, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(ROOT, "evidence_vault", "11_PLASMA_GEOPHYSICS", "plasma_geophysics.json")))
gt1, nt1 = d["T1_faults"]; gt2, nt2 = d["T2_geomagnetic"]
t3 = {x["label"].split("_")[0]: x for x in d["T3_prequake"]}

rows = [  # (section, label, est, lo, hi)
    ("Near an active fault (<= 25 km)", "US, orb vs craft, by state",
     *[nt1["tests"]["orb_vs_craft|25km|MH_by_region"][k] for k in ("MH_OR",)], *nt1["tests"]["orb_vs_craft|25km|MH_by_region"]["CI95"]),
    ("Near an active fault (<= 25 km)", "US West only, by state",
     nt1["tests"]["orb_vs_craft|25km|west_of_104W|MH_by_state"]["MH_OR"], *nt1["tests"]["orb_vs_craft|25km|west_of_104W|MH_by_state"]["CI95"]),
    ("Near an active fault (<= 25 km)", "France, orb vs craft, by dept",
     gt1["tests"]["orb_vs_craft|25km|MH_by_region"]["MH_OR"], *gt1["tests"]["orb_vs_craft|25km|MH_by_region"]["CI95"]),
    ("Near an active fault (<= 25 km)", "France, unexplained vs identified orbs",
     gt1["tests"]["unexplainedCD_orb_vs_identifiedAB_orb|25km|MH_by_region"]["MH_OR"],
     *gt1["tests"]["unexplainedCD_orb_vs_identifiedAB_orb|25km|MH_by_region"]["CI95"]),
    ("Geomagnetic storm day (Kp >= 5)", "US, orb vs craft, by year",
     nt2["tests"]["orb_vs_craft|storm_day|MH_by_year"]["MH_OR"], *nt2["tests"]["orb_vs_craft|storm_day|MH_by_year"]["CI95"]),
    ("Geomagnetic storm day (Kp >= 5)", "US north of 45N, by year",
     nt2["tests"]["orb_vs_craft_lat>=45N|storm_day|MH_by_year"]["MH_OR"], *nt2["tests"]["orb_vs_craft_lat>=45N|storm_day|MH_by_year"]["CI95"]),
    ("Geomagnetic storm day (Kp >= 5)", "France, orb vs craft, by year",
     gt2["tests"]["orb_vs_craft|storm_day|MH_by_year"]["MH_OR"], *gt2["tests"]["orb_vs_craft|storm_day|MH_by_year"]["CI95"]),
    ("Geomagnetic storm day (Kp >= 5)", "France, unexplained vs identified orbs",
     gt2["tests"]["unexplainedCD_orb_vs_identifiedAB_orb|storm_day|MH_by_year"]["MH_OR"],
     *gt2["tests"]["unexplainedCD_orb_vs_identifiedAB_orb|storm_day|MH_by_year"]["CI95"]),
]
for key, lab in (("cascadia", "Cascadia M3+, 100 km"), ("oklahoma", "Oklahoma M3+, 100 km"),
                 ("new", "New Madrid M2.5+, 100 km"), ("california", "California M5+, 150 km")):
    x = t3[key]["pre_MH_by_year"]
    rows.append(("1-14 days before a nearby quake", lab, x["MH_OR"], *x["CI95"]))
did = d["T3b_oklahoma_DiD"]
rows.append(("Oklahoma induced-quake surge", "OK vs neighbours, 2010-13 vs 2000-08", did["ratio_of_OR"], *did["CI95"]))

INK, INK2, GRID, MARK, SURF = "#191919", "#666666", "#e6e6e6", "#257de0", "#ffffff"
fig, ax = plt.subplots(figsize=(8.2, 7.6), dpi=200)
fig.patch.set_facecolor(SURF); ax.set_facecolor(SURF)
y = 0; ticks, labels = [], []; last = None
for sec, lab, est, lo, hi in rows:
    if sec != last:
        y -= 0.6
        ax.text(0.27, y, sec, fontsize=9.5, fontweight="bold", color=INK, va="center")
        y -= 1; last = sec
    ax.plot([lo, hi], [y, y], color=MARK, lw=2, solid_capstyle="round")
    ax.plot(est, y, "o", color=MARK, ms=8, mec=SURF, mew=2)
    ax.text(1.02, y, f"{est:.2f} [{lo:.2f}, {hi:.2f}]", fontsize=8, color=INK2, va="center", ha="left", transform=ax.get_yaxis_transform())
    ticks.append(y); labels.append(lab); y -= 1
ax.axvline(1, color=INK2, lw=1, ls=(0, (3, 3)))
ax.set_xscale("log"); ax.set_xlim(0.25, 5.5); ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
ax.set_xticks([0.25, 0.5, 1, 2, 4]); ax.set_xticklabels(["0.25", "0.5", "1", "2", "4"], color=INK2, fontsize=8)
ax.set_yticks(ticks); ax.set_yticklabels(labels, fontsize=8.5, color=INK)
ax.set_ylim(y + 0.4, 0.2)
ax.tick_params(length=0)
ax.grid(axis="x", color=GRID, lw=0.8); ax.set_axisbelow(True)
for s in ax.spines.values(): s.set_visible(False)
ax.set_xlabel("Odds ratio, orb reports vs control reports (log scale). Above 1 = orbs more exposed.", fontsize=8.5, color=INK2)
fig.suptitle("No robust link between orb reports and faults, storms or earthquakes", x=0.02, ha="left",
             fontsize=12, fontweight="bold", color=INK)
fig.text(0.02, 0.935, "Stratified odds ratios with 95% cluster-bootstrap intervals. Controls come from the same reporting system.",
         fontsize=8.5, color=INK2)
fig.tight_layout(rect=(0, 0, 0.86, 0.93))
fig.savefig(sys.argv[1], facecolor=SURF)
print("wrote", sys.argv[1])
