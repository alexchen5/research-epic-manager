#!/usr/bin/env python3
"""Metrics + resource accounting helpers (CPU-only, stdlib + numpy)."""
from __future__ import annotations

import json
import resource
import time

import numpy as np


def rmse(y, yhat):
    y = np.asarray(y, dtype=np.float64)
    yhat = np.asarray(yhat, dtype=np.float64)
    return float(np.sqrt(np.mean((y - yhat) ** 2)))


def r2(y, yhat):
    y = np.asarray(y, dtype=np.float64)
    yhat = np.asarray(yhat, dtype=np.float64)
    ss_res = float(np.sum((y - yhat) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    if ss_tot <= 0.0:
        return float("nan")
    return float(1.0 - ss_res / ss_tot)


def split_conformal(y_cal, yhat_cal, y_test, yhat_test, alpha=0.1):
    """Split-conformal predictive interval: coverage + mean width on test."""
    y_cal = np.asarray(y_cal, dtype=np.float64)
    yh_cal = np.asarray(yhat_cal, dtype=np.float64)
    y_test = np.asarray(y_test, dtype=np.float64)
    yh_test = np.asarray(yhat_test, dtype=np.float64)
    scores = np.abs(y_cal - yh_cal)
    if len(scores) == 0:
        return float("nan"), float("nan")
    q = np.quantile(scores, np.ceil((1.0 - alpha) * (len(scores) + 1)) / len(scores))
    lo = yh_test - q
    hi = yh_test + q
    cov = float(np.mean((y_test >= lo) & (y_test <= hi)))
    width = float(np.mean(hi - lo))
    return cov, width


# ---------------------------------------------------------------------------
# Resource accounting (first-class axes, per plan): wall clock, peak RSS,
# estimated flops and bytes for the spectral operators.
# ---------------------------------------------------------------------------
def est_spectral_fit_flops(ny, nx):
    """rfft2 + irfft2 of an (ny,nx) grid ~ 2*(5*N*log2(N)) + O(N)."""
    n = ny * nx
    l = max(1.0, np.log2(n))
    return 10.0 * n * l + 3.0 * n


def est_spectral_pred_flops(ny, nx):
    n = ny * nx
    l = max(1.0, np.log2(n))
    return 5.0 * n * l + 2.0 * n


def est_spectral_bytes(ny, nx):
    """Spectrum (rfft2 output, complex128) + y + alpha + c: ~ 40*N bytes."""
    return 40.0 * ny * nx


class ResourceRecorder:
    def __init__(self, dataset_origin, simulation_marker=None, meta=None):
        self.dataset_origin = dataset_origin
        self.simulation_marker = simulation_marker
        self.meta = meta or {}
        self.t0 = time.perf_counter()
        self._peak_rss = None

    def rss_gb(self):
        r = resource.getrusage(resource.RUSAGE_SELF)
        gb = r.ru_maxrss / (1024.0 ** 2) if hasattr(r, "ru_maxrss") else float("nan")
        # ru_maxrss is KB on Linux
        if r.ru_maxrss > 0:
            gb = r.ru_maxrss / 1024.0 / 1024.0
        return gb

    def snapshot(self, elapsed=None):
        return {
            "wall_clock_s": round(elapsed if elapsed is not None
                                  else time.perf_counter() - self.t0, 3),
            "peak_rss_gb": round(self.rss_gb(), 3),
        }

    def artifact(self, arm, kernel, lam, ny, nx, extra=None):
        d = {
            "arm": arm,
            "dataset.origin": self.dataset_origin,
            "simulation_marker": self.simulation_marker,
            "kernel": kernel,
            "lambda": lam,
            "N": ny * nx,
            "estimated_flops": est_spectral_fit_flops(ny, nx),
            "estimated_bytes": est_spectral_bytes(ny, nx),
            "estimated_flops_per_fit": est_spectral_fit_flops(ny, nx),
        }
        d.update(self.snapshot())
        if extra:
            d.update(extra)
        return d


def write_json(path, data):
    with open(path, "w") as fh:
        json.dump(data, fh, indent=1, default=float)
    return path