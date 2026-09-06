#!/usr/bin/env python3
"""T3 forecast arm (iteration 2): frequency-domain transfer forecast.

Honest framing: NOT a new method. A per-Fourier-mode ridge (spectral filter)
mapping the current field spectrum to the h-month-ahead field spectrum,
evaluated under future-blind rolling-origin holdout against persistence,
train-only monthly climatology, and train-only AR(1) baselines.

Interface
---------
fit_transfer_modes(Y, h, lam): per-mode ridge H_h from train-only window.
forecast_field(Y_t, H, h): irfft2(H * rfft2(Y_t)) -> predicted field.
box_index(field, rows, cols): mean over the Nino3.4 box (Trenberth 1997).
evaluate_horizon(...): per-h RMSE/MAE/corr + climatology skill + year-block
bootstrap significance vs each baseline (primary), DM secondary.
"""
from __future__ import annotations

import numpy as np


def box_index(field, rows, cols):
    """Mean of field over box rows/cols (spectral box functional at Nino3.4)."""
    return float(field[np.ix_(rows, cols)].mean())


def fit_transfer_modes(Y, h, lam=1e-2):
    """Fit per-Fourier-mode ridge H_h on train window Y (n_t, ny, nx).

    For each DFT frequency f (rfft2 layout incl. Nyquist/DC conventions):
        H_f = (sum_t |Y_t(f)|^2 + lam)^-1 * sum_t conj(Y_t(f)) * Y_{t+h}(f)
    Applied modes only; DC mode left as identity (mean offset handled by
    the box functional on anomaly fields).
    Returns H (same shape as rfft2 output: (ny, nx//2+1), complex128).
    """
    n_t = Y.shape[0]
    F = np.fft.rfft2(Y)                      # (n_t, ny, nx//2+1)
    denom = np.sum(np.abs(F[:-h]) ** 2, axis=0) + lam   # (ny, nx//2+1)
    numer = np.sum(np.conj(F[:-h]) * F[h:], axis=0)     # (ny, nx//2+1)
    H = np.zeros_like(numer)
    ok = denom > 1e-12
    H[ok] = numer[ok] / denom[ok]
    H[0, 0] = 1.0 + 0.0j                      # DC: carry anomaly mean (0 by def.)
    return H


def forecast_field(Y_t, H):
    """Predicted (h-month-ahead) field for one current field Y_t (ny, nx)."""
    return np.fft.irfft2(H * np.fft.rfft2(Y_t), s=Y_t.shape).real


def predict_index_series(Y, H, h, rows, cols):
    """Rolling-origin index forecasts: idx_hat[t+h] = box_index(forecast(Y_t))."""
    n = Y.shape[0]
    out = np.full(n, np.nan)
    for t in range(n - h):
        out[t + h] = box_index(forecast_field(Y[t], H), rows, cols)
    return out


def month_climatology(Y, times):
    """Train-only monthly climatology: mean per calendar month of Y index."""
    months = (times % 12).astype(int)
    cl = np.full(12, np.nan)
    for m in range(12):
        sel = months == m
        if sel.sum() > 0:
            cl[m] = np.nanmean(Y[sel])
    return cl


def ar1_fit(Y):
    """Train-only AR(1) on the index: phi, c (no intercept bias handling)."""
    y0, y1 = Y[:-1], Y[1:]
    denom = np.sum(y0 ** 2)
    phi = np.sum(y0 * y1) / denom if denom > 0 else 0.0
    c = np.mean(y1) - phi * np.mean(y0)
    return phi, c


def metrics(y_true, y_hat):
    m = ~np.isnan(y_true) & ~np.isnan(y_hat)
    if m.sum() == 0:
        return {"n": 0, "rmse": np.nan, "mae": np.nan, "corr": np.nan}
    yt, yh = y_true[m], y_hat[m]
    rmse = float(np.sqrt(np.mean((yt - yh) ** 2)))
    mae = float(np.mean(np.abs(yt - yh)))
    corr = float(np.corrcoef(yt, yh)[0, 1]) if m.sum() > 2 and np.std(yt) > 0 and np.std(yh) > 0 else np.nan
    return {"n": int(m.sum()), "rmse": rmse, "mae": mae, "corr": corr}


def skill_score(y_true, y_hat, y_clim):
    """Climatology skill: 1 - MSE(y_hat)/MSE(y_clim) on matched non-nan."""
    m = ~np.isnan(y_true) & ~np.isnan(y_hat) & ~np.isnan(y_clim)
    if m.sum() < 2:
        return np.nan
    mse_h = np.mean((y_true[m] - y_hat[m]) ** 2)
    mse_c = np.mean((y_true[m] - y_clim[m]) ** 2)
    if mse_c <= 1e-12:
        return np.nan
    return float(1.0 - mse_h / mse_c)


def year_block_bootstrap(y_true, y_hat_a, y_hat_b, years, n_boot=2000, seed=7):
    """Year-block bootstrap of skill difference (primary significance).

    Resample TEST YEARS (blocks) with replacement; recompute MSE difference
    (A - B, i.e., negative = A better); return p-value like 2-sided fraction
    of bootstrap diffs with sign opposite to the observed diff, plus CI.
    """
    rng = np.random.default_rng(seed)
    uy = np.unique(years)
    diff = np.mean((y_true - y_hat_a) ** 2) - np.mean((y_true - y_hat_b) ** 2)
    draws = np.empty(n_boot)
    for b in range(n_boot):
        sel = rng.choice(uy, size=len(uy), replace=True)
        m = np.isin(years, sel)
        if m.sum() < 2:
            draws[b] = 0.0
            continue
        d = (np.mean((y_true[m] - y_hat_a[m]) ** 2)
             - np.mean((y_true[m] - y_hat_b[m]) ** 2))
        draws[b] = d
    if np.abs(diff) < 1e-12:
        p = 1.0
    else:
        p = float(np.mean(np.sign(draws) != np.sign(diff)))
    lo, hi = np.percentile(draws, [2.5, 97.5])
    return {"se": float(np.std(draws)), "ci95": [float(lo), float(hi)], "p": p, "obs_diff": float(diff)}