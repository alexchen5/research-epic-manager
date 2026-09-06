#!/usr/bin/env python3
"""Generate the paper figures (PNG, 300 dpi) from real-data artifacts.

Loading follows the exact conventions of scripts/run_iters2.py::load_real:
raw fields may still carry NCAR sentinels (|x| > 1e30); those cells are
missing and are imputed per month with the valid-cell mean; missing_mask.npy
records them and evaluation always excludes them.

Figures:
  figs/fig1_recon.png  - 2016-01 (test window, index 1920): observed anomaly
                         field vs matern32 torus spectral reconstruction
                         (lambda = 1e-4, per T1a); missing cells highlighted.
  figs/fig2_nino34.png - Nino3.4 index: observed (index.npy) vs spectral
                         box-functional prediction (matern32, lambda = 1e-2,
                         per T2) on the test window 2016-01..2022-12.
  figs/fig3_skill.png  - T3 transfer skill vs climatology by start month x
                         lead, from T3-forecast-transfer.json start_month_skill.
"""
import json
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REAL = os.path.join(ROOT, "results", "raw", "real")
ITER = os.path.join(ROOT, "results", "iter2")
FIG = os.path.join(HERE, "figs")
os.makedirs(FIG, exist_ok=True)

sys.path.insert(0, os.path.join(ROOT, "scripts"))
import fft_krr as fk  # noqa: E402

# ---------------------------------------------------------------------------
# Load (same conventions as run_iters2.load_real)
# ---------------------------------------------------------------------------
fields = np.load(os.path.join(REAL, "fields.npy")).astype(np.float64)
index = np.load(os.path.join(REAL, "index.npy"))
meta = json.load(open(os.path.join(REAL, "meta.json")))
missing = np.abs(fields) > 1e30
fields = fields.copy()
for t in range(fields.shape[0]):
    row = fields[t]
    valid = ~missing[t]
    if valid.any():
        row[~valid] = np.nanmean(row[valid])

NY, NX = 36, 72
LAT = np.array(meta["lat"])
LON = np.array(meta["lon"])
ROWS = np.arange(17, 19)     # Nino3.4 box rows (lat +-2.5)
COLS = np.arange(38, 48)     # Nino3.4 box cols (lon 192.5..237.5E)
TRAIN_END, TEST_END = 1920, 2004
KF = fk.KERNELS["matern32"]

CMAP = "RdBu_r"
VMIN, VMAX = -3.0, 3.0

# ---------------------------------------------------------------------------
# Fig 1: reconstruction of test month 2016-01 (index 1920)
# ---------------------------------------------------------------------------
t = 1920
obs = fields[t]
rec = fk.predict_torus(fk.fit_torus(obs, NY, NX, KF, lam=1e-4), NY, NX, KF)
obs_m = np.ma.masked_where(missing[t], obs)
rec_m = np.ma.masked_where(missing[t], rec)

# Manual layout: with aspect="equal" maps, neither tight_layout() (it cannot
# manage a colorbar spanning several axes and warns "not compatible", leaving
# the colorbar misaligned) nor constrained_layout() pack the image axes
# tightly: both leave a large blank band between the suptitle and the panels.
# Compute the geometry from the map's data aspect instead, so the figure has
# exactly the height the content needs and the colorbar sits beside the right
# panel, aligned with it.
fig_w = 7.2
ar = (LON[-1] - LON[0]) / (LAT[-1] - LAT[0])
left_m, gap, cb_gap, cb_w, cb_label, right_m = 0.55, 0.20, 0.14, 0.28, 0.34, 0.02
map_w = (fig_w - left_m - gap - cb_gap - cb_w - cb_label - right_m) / 2
map_h = map_w / ar
top, supt, gap_t, title, gap_m, ticks, xlab, bottom = \
    0.03, 0.15, 0.07, 0.14, 0.03, 0.17, 0.23, 0.03
fig_h = top + supt + gap_t + title + gap_m + map_h + ticks + xlab + bottom

fig = plt.figure(figsize=(fig_w, fig_h))
y_top = 1 - (top + supt + gap_t + title + gap_m) / fig_h
y_bot = y_top - map_h / fig_h
x0 = left_m / fig_w
x1 = (left_m + map_w) / fig_w
x2 = (left_m + map_w + gap) / fig_w
x3 = (left_m + 2 * map_w + gap) / fig_w
xc = (left_m + 2 * map_w + gap + cb_gap) / fig_w
ax0 = fig.add_axes([x0, y_bot, x1 - x0, map_h / fig_h])
ax1 = fig.add_axes([x2, y_bot, x3 - x2, map_h / fig_h])
cax = fig.add_axes([xc, y_bot, cb_w / fig_w, map_h / fig_h])

im0 = ax0.imshow(obs_m, cmap=CMAP, vmin=VMIN, vmax=VMAX,
                 aspect="equal", extent=[LON[0], LON[-1], LAT[0], LAT[-1]])
ax0.set_title("Observed anomalies (missing in white)")
ax0.set_xlabel("Longitude"); ax0.set_ylabel("Latitude")
im1 = ax1.imshow(rec_m, cmap=CMAP, vmin=VMIN, vmax=VMAX,
                 aspect="equal", extent=[LON[0], LON[-1], LAT[0], LAT[-1]])
ax1.set_title("matern32 torus reconstruction")
ax1.set_xlabel("Longitude")
cb = fig.colorbar(im1, cax=cax)
cb.set_label("SST anomaly ($^\\circ$C)")
fig.suptitle("2016-01 (test-window month)", y=1 - (top + supt / 2) / fig_h,
             fontsize=10)
fig.savefig(os.path.join(FIG, "fig1_recon.png"), dpi=300,
            bbox_inches="tight")
plt.close(fig)

# ---------------------------------------------------------------------------
# Fig 2: Nino3.4 index, observed vs spectral functional (test window)
# ---------------------------------------------------------------------------
pred = np.array([fk.predict_box_functional(
    fk.fit_torus(fields[t], NY, NX, KF, lam=1e-2), NY, NX, KF, ROWS, COLS)
    for t in range(TRAIN_END, TEST_END)])
te = np.arange(TRAIN_END, TEST_END)
months = np.array([np.datetime64("1856-01") + np.timedelta64(int(m), "M")
                   for m in te])

fig, ax = plt.subplots(figsize=(7.2, 2.5))
ax.plot(months, index[te], "k-", lw=1.2, label="Observed Nino3.4 index")
ax.plot(months, pred, "C0--", lw=1.2, label="Spectral functional prediction")
ax.set_xlabel("Test window (2016-01 .. 2022-12)")
ax.set_ylabel("Nino3.4 anomaly ($^\\circ$C)")
ax.legend(loc="lower left", fontsize=8, frameon=False)
ax.grid(alpha=0.25)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig2_nino34.png"), dpi=300, bbox_inches="tight")
plt.close(fig)

# ---------------------------------------------------------------------------
# Fig 3: T3 transfer skill by start month x lead (from artifacts)
# ---------------------------------------------------------------------------
d = json.load(open(os.path.join(ITER, "T3-forecast-transfer.json")))
ORIG = {"origin-month-0": "Jan", "origin-month-3": "Apr",
        "origin-month-5": "Jun", "origin-month-9": "Oct", "all": "all"}
HS = ["1", "3", "6", "12"]
rows = [ORIG[k] for k in ORIG]
M = np.array([[d["horizons"][h]["start_month_skill"][k]["skill"]
               for h in HS] for k in ORIG])

fig, ax = plt.subplots(figsize=(4.6, 2.9))
im = ax.imshow(M, cmap=CMAP, vmin=-1.0, vmax=1.0, aspect="auto")
ax.set_xticks(range(len(HS))); ax.set_xticklabels([f"h={h}" for h in HS])
ax.set_yticks(range(len(rows))); ax.set_yticklabels(rows)
for i in range(M.shape[0]):
    for j in range(M.shape[1]):
        ax.text(j, i, f"{M[i, j]:.2f}", ha="center", va="center",
                fontsize=8, color="k")
ax.set_title("T3 transfer skill vs climatology (84 test months)")
ax.set_xlabel("Lead"); ax.set_ylabel("Start month")
cb = fig.colorbar(im, fraction=0.046, pad=0.04)
cb.set_label("Skill = 1 - RMSE$^2$ / clim-RMSE$^2$")
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig3_skill.png"), dpi=300, bbox_inches="tight")
plt.close(fig)

print("wrote:", sorted(os.listdir(FIG)))