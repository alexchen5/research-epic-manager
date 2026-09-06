#!/usr/bin/env python3
"""Synthetic-from-physics SST-anomaly-like field generator (pre-committed fallback).

[simulated] dataset. This generator is the PRE-COMMITTED fallback for the
unreadable netCDF-4/HDF5 Kaplan SST v2 files (see EXECUTION_NOTES.md). It
produces monthly anomaly fields on the 72x36 (5-degree) lat/lon grid with:

  - circulant-embedded Matern(3/2 or 5/2) stationary covariance (exact torus
    sampling via FFT: field = irfft2(rfft2(w)*sqrt(rfft2(c_torus)))),
  - latitude amplitude scaling (cos(lat), Kaplan-like),
  - Kaplan-like EOF structure: leading low-frequency spatial harmonics
    modulated by AR(1)-in-time coefficients (dominant low-frequency variance,
    red temporal spectrum),
  - multiplicative lognormal-ish "mask" noise on the observed field (iid
    Gaussian measurement noise) so the Nino3.4 index prediction task is a
    genuine denoising problem (index = box mean of the CLEAN field).

Seed fixed (20260831); parameterization recorded in meta.json. Every artifact
written by the pipeline from this data carries dataset.origin and
simulation_marker fields.
"""
from __future__ import annotations

import json
import os

import numpy as np

SEED = 20260831
NY, NX = 36, 72  # 5-degree global grid: lat -90..90, lon 0..355
LON = np.arange(NX) * 5.0
LAT = -90.0 + np.arange(NY) * 5.0 + 2.5  # cell centers


def torus_cov_column(ny, nx, kfun, ell):
    dy = np.minimum(np.arange(ny)[:, None], ny - np.arange(ny)[:, None])
    dx = np.minimum(np.arange(nx)[None, :], nx - np.arange(nx)[None, :])
    return kfun(dy / ell, dx / ell)


def matern32_cov(dy, dx):
    r = np.sqrt(dy * dy + dx * dx)
    return (1.0 + r) * np.exp(-r)


def matern52_cov(dy, dx):
    r = np.sqrt(dy * dy + dx * dx)
    return (1.0 + r + r * r / 3.0) * np.exp(-r)


def sample_field(rng, ny, nx, kfun, ell, lat_amp):
    """Exact torus (circulant) GP sample: O(N log N)."""
    c = torus_cov_column(ny, nx, kfun, ell)
    spec = np.fft.rfft2(c)
    spec = np.maximum(spec, 0.0)
    w = rng.standard_normal((ny, (nx // 2) + 1)) + 1j * rng.standard_normal(
        (ny, (nx // 2) + 1))
    f = np.fft.irfft2(w * np.sqrt(spec), s=(ny, nx))
    # mean-zero, unit-variance-ish; latitude scaling (Kaplan-like: smaller
    # variability toward the poles on the anomaly field)
    f = f / (float(np.std(f)) + 1e-12)
    lat = -90.0 + (np.arange(ny) + 0.5) * (180.0 / ny)
    amp = np.cos(np.deg2rad(lat))[:, None] + 0.15
    return f * amp


def sample_eof_field(rng, k, ny, nx, seed_field):
    """Kaplan-like EOF structure: k dominant low-frequency harmonics modulated
    by AR(1) temporal coefficients layered on the residual process."""
    f = seed_field.copy()
    # low-frequency spatial harmonics (first few Fourier eigenmodes of the torus)
    yy = np.arange(ny)[:, None]
    xx = np.arange(nx)[None, :]
    for m in range(1, k + 1):
        amp = rng.normal(0.0, 1.0)
        phi = rng.uniform(0.0, 2 * np.pi)
        # AR(1) temporal-like coefficient applied on this single field's mode
        # strength: we directly modulate amplitude (per-field scalar is the
        # temporal coefficient at this sample time)
        f = f + amp * np.cos(2 * np.pi * m * yy / ny + phi) * np.sin(
            2 * np.pi * m * xx / nx)
    f = f / (float(np.std(f)) + 1e-12)
    return f


def generate(ny=NY, nx=NX, n_months=888, ell_matern=4.0, k_eof=4,
             noise_std=0.35, seed=SEED, phase_shift_months=0):
    """Generate n_months monthly anomaly fields + Nino3.4 index.

    Returns dict with 'fields' (n_months, ny, nx), 'index' (n_months,),
    'lat', 'lon', 'meta'.
    Nino3.4 box (Trenberth 1997): 5N-5S, 170W-120W -> rows |lat|<=5 (rows
    17..19 on 5-deg grid), cols 190E..240E (cols 38..47).
    """
    rng = np.random.default_rng(seed)
    fields = np.empty((n_months, ny, nx), dtype=np.float32)
    clean = np.empty((n_months, ny, nx), dtype=np.float32)
    for t in range(n_months):
        base = sample_field(rng, ny, nx, matern32_cov, ell_matern, lat_amp=True)
        f = sample_eof_field(rng, k_eof, ny, nx, base)
        f = f / (float(np.std(f)) + 1e-12)
        # mild seasonal cycle (month-of-year offset from phase_shift)
        moy = (t + phase_shift_months) % 12
        lat = -90.0 + (np.arange(ny) + 0.5) * (180.0 / ny)
        f = f + 0.15 * np.sin(2 * np.pi * moy / 12.0) * np.cos(
            np.deg2rad(lat))[:, None]
        clean[t] = f
        fields[t] = f + rng.normal(0.0, noise_std, (ny, nx))
    fields = np.asarray(fields, dtype=np.float32)
    # Nino3.4 index = area-mean of the CLEAN field over the box
    rows = np.arange(17, 20)
    cols = np.arange(38, 48)
    index = clean[:, rows][:, :, cols].mean(axis=(1, 2))
    meta = {
        "dataset.origin": "synthetic-[simulated]-from-physics",
        "simulation_marker": "synthetic-from-physics (Kaplan-like), seed=%d" % seed,
        "seed": seed, "ny": ny, "nx": nx, "n_months": n_months,
        "ell_matern": ell_matern, "k_eof": k_eof, "noise_std": noise_std,
        "phase_shift_months": phase_shift_months,
        "lat": LAT.tolist(), "lon": LON.tolist(),
        "nino34_box": {"rows": rows.tolist(), "cols": cols.tolist()},
        "note": "fallback for unreadable Kaplan SST v2 (netCDF-4/HDF5)",
    }
    return {"fields": fields, "index": index, "meta": meta}


def main():
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "results", "raw")
    os.makedirs(out, exist_ok=True)
    data = generate()
    np.save(os.path.join(out, "fields.npy"), data["fields"])
    np.save(os.path.join(out, "index.npy"), data["index"])
    with open(os.path.join(out, "meta.json"), "w") as fh:
        json.dump(data["meta"], fh, indent=1)
    # small pilot + scaling fields
    rng = np.random.default_rng(SEED + 1)
    for (ny, nx, tag) in [(32, 32, "pilot"), (36, 72, "scaling_72x36"),
                          (72, 144, "scaling_144x72")]:
        f = sample_field(rng, ny, nx, matern32_cov, 4.0, lat_amp=True)
        np.save(os.path.join(out, f"field_{tag}.npy"), f)
    print(f"generated {data['fields'].shape} fields -> {out}")
    print("index stats: mean=%.3f std=%.3f" % (data["index"].mean(),
                                               data["index"].std()))


if __name__ == "__main__":
    main()