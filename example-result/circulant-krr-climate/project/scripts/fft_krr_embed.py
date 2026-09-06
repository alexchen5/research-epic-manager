#!/usr/bin/env python3
"""Iteration-3 novel solvers: RE-ABLRC (S1), SSAM-CAM (S2), ND utilities.

Honest framing (per approved plan): every component is classical (WSS
embedding, FFT/DCT spectral solves, Woodbury, FISTA, Anderson mixing, POCS);
the claim is the grid-KRR-targeted INTEGRATION only. All residuals reported
here are computed against the EXACT free-boundary operator (principal block
of the whole-sample-symmetric circulant embedding + ridge), never against
the embedded system alone.

RE-ABLRC (S1): whole-sample symmetric (2H-1)x(2W-1) [3D analog] DCT-I-class
first-column embedding (variant A: boundary-doubled mirror), exact circulant
spectral solve (floored spectrum + ridge), then a boundary-banded Woodbury
correction confined to the edge/seam band of the embedding (exact in the
limit T -> full tail; rank |T| ~ O(w*(H+W)) in 2D, w*(HW+HD+WD) in 3D).
The w-sweep {1,2,3,4} checks monotonic residual decay (fail-fast guard);
the residual acceptance cap (median <= 1e-6) and the rank budget are the
pre-registered guards (NOT-validated if cap/rank not met).

SSAM-CAM (S2): spectral-spatial alternating minimization on the masked
system (P_m K P_m^T + lam I) w = y_m (same system as the PCG reference,
T1b convention): FISTA-momentum preconditioned gradient step (floored
whole-sample-spectrum preconditioner on the FREE-boundary operator),
soft projection on the observed-cell subspace, Anderson mixing window m=5,
step schedule eta_k = 0.5/(1+k/200), iteration ceiling 500, termination =
KKT residual r_t := (P_m K P_m^T + lam I) w - y_m relative to ||y_m||.
"""
from __future__ import annotations

import time

import numpy as np
from scipy.fft import dctn, idctn, dstn, idstn

import fft_krr as fk


# ---------------------------------------------------------------------------
# ND stationary kernels (radial; formulas match fft_krr.KERNELS in 2D)
# ---------------------------------------------------------------------------
def make_nd_kernel(name, ell=4.0):
    """kfun(coords) on a distance array or tuple of per-axis arrays."""

    def base(d, _ell):
        r = np.minimum(d / _ell, 1e3)
        if name == "matern32":
            return (1.0 + r) * np.exp(-r)
        if name == "matern52":
            return (1.0 + r + r * r / 3.0) * np.exp(-r)
        return np.exp(-(d * d) / (2.0 * _ell * _ell))

    def kern(*coords):
        if len(coords) == 1:
            a = coords[0]
            if isinstance(a, (tuple, list)):
                d2 = sum(np.asarray(c) ** 2 for c in a)
            else:
                d2 = np.asarray(a) ** 2
        else:
            d2 = sum(np.asarray(c) ** 2 for c in coords)
        return base(np.sqrt(d2), ell)

    return kern


# ---------------------------------------------------------------------------
# First column + whole-sample-symmetric (variant A) embedding
# ---------------------------------------------------------------------------
def _edims(dims):
    return tuple(2 * d - 1 for d in dims)


def _prin_slice(dims):
    return tuple(slice(0, d) for d in dims)


def first_column_nd(dims, kfun):
    """First column of the ND free-boundary BTTB Gram: kfun over |lag|/axis."""
    grids = [np.arange(d) for d in dims]
    gg = np.meshgrid(*grids, indexing="ij")
    return kfun(tuple(g.ravel() for g in gg)).reshape(dims)


def embed_wss_nd(c, dims):
    """Whole-sample symmetric embedding (2d-1 per axis, boundary-doubled
    mirror). Principal-block property: leading dims-block of the embedded
    circulant equals the free ND BTTB Gram (matvec-exact)."""
    nd = len(dims)
    ce = np.zeros(_edims(dims))
    for bits in range(1 << nd):
        src, dst = [], []
        for ax, d in enumerate(dims):
            if bits & (1 << ax):
                src.append(slice(d - 1, 0, -1))
                dst.append(slice(d, 2 * d - 1))
            else:
                src.append(slice(0, d))
                dst.append(slice(0, d))
        ce[tuple(dst)] = c[tuple(src)]
    return ce


def amatvec_nd(v, dims, kfun, lam, spec0=None):
    """Exact free-boundary (K + lam I) matvec, O(N log N)."""
    v = np.asarray(v, dtype=np.float64).ravel()
    if spec0 is None:
        c = first_column_nd(dims, kfun)
        spec0 = np.fft.rfftn(embed_wss_nd(c, dims)).real
    sl = _prin_slice(dims)
    Ve = np.zeros(_edims(dims))
    Ve[sl] = v.reshape(dims)
    rr = np.fft.irfftn(np.fft.rfftn(Ve) * spec0, s=_edims(dims))
    return rr[sl].ravel() + lam * v


def z0_nd(y, dims, spec_used):
    """Floored+ridge embedded spectral solve of C~ z = [y; 0] (flat z)."""
    Yf = np.zeros(_edims(dims))
    Yf[_prin_slice(dims)] = y.reshape(dims)
    z = np.fft.irfftn(np.fft.rfftn(Yf) / spec_used, s=_edims(dims))
    return z.ravel()


def cinv_nd(u, dims, spec_used):
    """Apply C~^{-1} to a flat (prod(edims)) vector."""
    U = u.reshape(_edims(dims))
    return np.fft.irfftn(np.fft.rfftn(U) / spec_used, s=_edims(dims)).ravel()


def idx_sets_nd(dims):
    """Principal/tail flat index sets + seam distance of tail cells."""
    ed = _edims(dims)
    L = int(np.prod(ed))
    ind = np.arange(L)
    coords = np.unravel_index(ind, ed)
    prin = np.ones(L, dtype=bool)
    for ax in range(len(dims)):
        prin &= coords[ax] < dims[ax]
    tail = ind[~prin]
    oob = np.zeros((len(dims), len(tail)))
    for ax in range(len(dims)):
        oob[ax] = np.maximum(coords[ax][tail] - (dims[ax] - 1), 0)
    dmin = oob.max(axis=0)
    return prin, tail, dmin


def band_mask_nd(dims, w):
    """Principal cells within Chebyshev distance w of the grid boundary."""
    grids = [np.arange(d) for d in dims]
    gg = np.meshgrid(*grids, indexing="ij")
    dist = None
    for ax, g in enumerate(gg):
        dc = np.minimum(g, dims[ax] - 1 - g)
        dist = dc if dist is None else np.maximum(dist, dc)
    return dist.ravel() < w


# ---------------------------------------------------------------------------
# RE-ABLRC (S1)
# ---------------------------------------------------------------------------
def re_ablrc_nd(y, dims, kfun, lam, w, ref=None, spec0=None, spec_used=None):
    """Naive WSS solve + boundary-banded Woodbury correction at width w.

    Returns dict: alpha, alpha0, naive_res, res (relative, exact operator),
    rank (|T|), band_res, interior_res.
    """
    y = np.asarray(y, dtype=np.float64).ravel()
    if spec0 is None:
        c = first_column_nd(dims, kfun)
        spec0 = np.fft.rfftn(embed_wss_nd(c, dims)).real
    if spec_used is None:
        spec_used = np.maximum(spec0, 0.0) + lam
    L = int(np.prod(_edims(dims)))
    z0 = z0_nd(y, dims, spec_used)
    prin, tail, dmin = idx_sets_nd(dims)
    a0 = z0[prin]
    norm_y = max(float(np.linalg.norm(y)), 1e-30)
    r0 = float(np.linalg.norm(y - amatvec_nd(a0, dims, kfun, lam, spec0))) / norm_y
    out = dict(alpha=a0, alpha0=a0, naive_res=r0, res=r0, rank=0,
               band_res=float("nan"), interior_res=float("nan"), T_size=0)
    T = tail[dmin < w]
    if len(T) == 0:
        return out
    nb = len(T)
    WTT = np.empty((nb, nb))
    for j in range(nb):
        e = np.zeros(L)
        e[T[j]] = 1.0
        WTT[:, j] = cinv_nd(e, dims, spec_used)[T]
    uT = np.linalg.solve(WTT, z0[T])
    u = np.zeros(L)
    u[T] = uT
    corr = cinv_nd(u, dims, spec_used)[prin]
    alpha = a0 - corr
    r = y - amatvec_nd(alpha, dims, kfun, lam, spec0)
    res = float(np.linalg.norm(r)) / norm_y
    bcell = band_mask_nd(dims, w)  # bool over the N principal cells
    rarr = r.reshape(dims).ravel()
    band_n = np.linalg.norm(rarr[bcell])
    int_n = np.linalg.norm(rarr[~bcell])
    denom = max(band_n + int_n, 1e-30)
    out = dict(alpha=alpha, alpha0=a0, naive_res=r0, res=res, rank=int(nb),
               band_res=float(band_n / denom), interior_res=float(int_n / denom),
               T_size=int(nb))
    if ref is not None:
        rf = np.asarray(ref, dtype=np.float64).ravel()
        nref = max(float(np.linalg.norm(rf)), 1e-30)
        out["gap"] = float(np.linalg.norm(alpha - rf)) / nref
        out["gap_naive"] = float(np.linalg.norm(a0 - rf)) / nref
    return out


def re_ablrc_sweep_nd(y, dims, kfun, lam, ws=(1, 2, 3, 4), w_design=None, ref=None):
    """Per-w RE-ABLRC report + monotone-decay fail-fast + rank budget."""
    c = first_column_nd(dims, kfun)
    spec0 = np.fft.rfftn(embed_wss_nd(c, dims)).real
    spec_used = np.maximum(spec0, 0.0) + lam
    out = {"w_sweep": {}, "w_design": None, "fail_fast": False, "naive_res": None}
    prev = None
    for w in ws:
        r = re_ablrc_nd(y, dims, kfun, lam, w, ref=ref, spec0=spec0, spec_used=spec_used)
        entry = {k: v for k, v in r.items() if k not in ("alpha", "alpha0")}
        out["w_sweep"][int(w)] = entry
        if prev is not None and r["res"] > prev * (1.0 + 1e-12):
            out["fail_fast"] = True
        prev = r["res"] if prev is None else min(prev, r["res"])
    out["naive_res"] = out["w_sweep"][int(ws[0])]["naive_res"]
    if w_design is not None:
        r = re_ablrc_nd(y, dims, kfun, lam, w_design, ref=ref, spec0=spec0,
                        spec_used=spec_used)
        out["w_design"] = {k: v for k, v in r.items() if k not in ("alpha", "alpha0")}
        out["w_design"]["w"] = int(w_design)
        out["alpha"] = r["alpha"]
        if len(dims) == 2:
            out["rank_budget_2d"] = int(w_design * (dims[0] + dims[1]))
        elif len(dims) == 3:
            H, W, D = dims
            out["rank_budget_3d"] = int(w_design * (H * W + H * D + W * D))
    else:
        out["alpha"] = out["w_sweep"][int(ws[-1])]["alpha"] if "alpha" in out["w_sweep"][int(ws[-1])] else None
    return out


# ---------------------------------------------------------------------------
# DCT/DST symmetric-convolution comparators (standard scipy constructions;
# residuals measured against the exact free operator, reported honestly)
# ---------------------------------------------------------------------------
def _ws_ext_nd(f, dims):
    """(2d-2)-period whole-sample extension (variant B, boundary NOT doubled)."""
    nd = len(dims)
    fe = np.zeros(tuple(2 * d - 2 for d in dims))
    base = np.asarray(f).reshape(dims)
    fe[_prin_slice(dims)] = base
    for bits in range(1, 1 << nd):
        src, dst = [], []
        for ax, d in enumerate(dims):
            if bits & (1 << ax):
                src.append(slice(d - 2, 0, -1))
                dst.append(slice(d, 2 * d - 2))
            else:
                src.append(slice(0, d))
                dst.append(slice(0, d))
        fe[tuple(dst)] = base[tuple(src)]
    return fe


def _refl_ext_nd(f, dims):
    """(2d)-half-sample reflective extension (boundary copy duplicated)."""
    nd = len(dims)
    fe = np.zeros(tuple(2 * d for d in dims))
    base = np.asarray(f).reshape(dims)
    fe[_prin_slice(dims)] = base
    for bits in range(1, 1 << nd):
        src, dst = [], []
        for ax, d in enumerate(dims):
            if bits & (1 << ax):
                src.append(slice(d - 1, None, -1))
                dst.append(slice(d, 2 * d))
            else:
                src.append(slice(0, d))
                dst.append(slice(0, d))
        fe[tuple(dst)] = base[tuple(src)]
    return fe


def dct1_solve_nd(y, dims, kfun, lam):
    """DCT-I whole-sample solve (Martucci 45, standard scipy construction):
    alpha = IDCT-I( DCT-I(y_ext) / (DCT-I(k_ext) + lam) )[principal]."""
    c = first_column_nd(dims, kfun)
    k_ext = _ws_ext_nd(c, dims)
    y_ext = _ws_ext_nd(y, dims)
    spec = dctn(k_ext, type=1, norm="ortho") + lam
    z = idctn(dctn(y_ext, type=1, norm="ortho") / spec, type=1, norm="ortho")
    return z[_prin_slice(dims)].ravel()


def dst2_solve_nd(y, dims, kfun, lam):
    """DST-II half-sample reflective solve (contrast flavor; half-sample 2H
    padding is EXPLICITLY not S1's method)."""
    c = first_column_nd(dims, kfun)
    k_ext = _refl_ext_nd(c, dims)
    y_ext = _refl_ext_nd(y, dims)
    spec = dstn(k_ext, type=2, norm="ortho") + lam
    z = idstn(dstn(y_ext, type=2, norm="ortho") / spec, type=2, norm="ortho")
    return z[_prin_slice(dims)].ravel()


# ---------------------------------------------------------------------------
# ND masked PCG (2D path reuses fft_krr canonical T1b machinery)
# ---------------------------------------------------------------------------
def cg_masked_nd(y, dims, kfun, obs_idx, lam, tol=1e-8, max_iter=4000):
    """PCG on (P_m K P_m^T + lam I) w = y_m; returns (alpha, iters, conv, relres)."""
    if len(dims) == 2:
        return fk.cg_masked_solve(np.asarray(y).ravel(), dims[0], dims[1], kfun,
                                  np.asarray(obs_idx, dtype=np.int64), lam=lam,
                                  tol=tol, max_iter=max_iter)
    y = np.asarray(y, dtype=np.float64).ravel()
    obs = np.asarray(obs_idx, dtype=np.int64)
    N = int(np.prod(dims))
    c = first_column_nd(dims, kfun)
    spec0 = np.fft.rfftn(embed_wss_nd(c, dims)).real
    spec_p = np.maximum(spec0, 0.0) + lam
    cinv = np.zeros_like(spec_p)
    np.divide(1.0, spec_p, out=cinv, where=np.abs(spec_p) > 1e-14)
    sl = _prin_slice(dims)

    def precond(r):
        arr = np.zeros(N)
        arr[obs] = r
        rf = np.zeros(_edims(dims))
        rf[sl] = arr.reshape(dims)
        P = np.fft.irfftn(np.fft.rfftn(rf) * cinv, s=_edims(dims))
        return P[sl].ravel()[obs]

    b = y[obs]
    x = np.zeros(len(obs))
    r = b.copy()
    z = precond(r)
    p = z.copy()
    rz = float(r @ z)
    r0 = float(np.linalg.norm(b))
    iters = 0
    conv = False
    for it in range(1, max_iter + 1):
        xf = np.zeros(N)
        xf[obs] = p
        Ap = amatvec_nd(xf, dims, kfun, lam, spec0)[obs]
        denom = float(p @ Ap)
        if denom <= 0.0 or not np.isfinite(denom):
            # rounding-level nonpositive curvature: restart the search
            # direction on the preconditioned residual (classical CG restart)
            p = z.copy()
            xf = np.zeros(N)
            xf[obs] = p
            Ap = amatvec_nd(xf, dims, kfun, lam, spec0)[obs]
            denom = float(p @ Ap)
            if denom <= 0.0 or not np.isfinite(denom):
                iters = it
                break
        a = rz / denom
        x = x + a * p
        r = r - a * Ap
        if float(np.linalg.norm(r)) <= tol * max(1.0, r0):
            conv = True
            iters = it
            break
        z = precond(r)
        rz_new = float(r @ z)
        beta = rz_new / max(rz, 1e-30)
        p = z + beta * p
        rz = rz_new
        iters = it
    alpha = np.zeros(N)
    alpha[obs] = x
    rel_res = float(np.linalg.norm(r)) / max(1.0, r0) if len(r) else float("nan")
    return alpha.reshape(dims), iters, conv, rel_res


# ---------------------------------------------------------------------------
# SSAM-CAM (S2)
# ---------------------------------------------------------------------------
def anderson_mix(hist_a, hist_g, g_cur):
    """Damped classical Anderson (AA) mixing on the last m iterates.

    Returns (alpha_mix, c_norm, ok). The normal equations use a relative
    regularization; mixes ONLY if the solution is bounded (|c| cap), else
    ok=False so the caller falls back to the plain iterate.
    """
    m = len(hist_a)
    if m < 2:
        return hist_a[-1], 0.0, False
    deltas = [(hist_a[i] - hist_a[i - 1], hist_g[i] - hist_g[i - 1])
              for i in range(1, m)]
    k = len(deltas)
    M = np.zeros((k, k))
    f = np.zeros(k)
    for i in range(k):
        dg = deltas[i][1]
        f[i] = -float(dg @ g_cur)
        for j in range(k):
            M[i, j] = float(dg @ deltas[j][1])
    if not np.all(np.isfinite(M)) or not np.all(np.isfinite(f)):
        return hist_a[-1], 0.0, False
    scale = max(float(np.max(np.abs(np.diag(M)))), 1e-30)
    try:
        c = np.linalg.solve(M + 1e-8 * scale * np.eye(k), f)
    except np.linalg.LinAlgError:
        return hist_a[-1], 0.0, False
    if not np.all(np.isfinite(c)) or float(np.max(np.abs(c))) > 1e3:
        return hist_a[-1], 0.0, False
    out = hist_a[-1].copy()
    for i in range(k):
        out += c[i] * deltas[i][0]
    return out, float(np.max(np.abs(c))), True


def ssam_cam_nd(y, obs_idx, dims, kfun, lam, tol=1e-6, max_iter=500,
                m_anderson=5, return_trace=False):
    """Spectral-spatial AM on (P_m K P_m^T + lam I) w = y_m; KKT termination.

    Spectral step: FISTA momentum + floored whole-sample-spectrum precond on
    the free operator. Spatial step: soft projection on the observed-cell
    subspace (off-obs coefficients decay softly; no hard clamp). Anderson
    mixing on the residual sequence (window m). eta_k = 0.5/(1+k/200).
    """
    y = np.asarray(y, dtype=np.float64).ravel()
    obs = np.asarray(obs_idx, dtype=np.int64)
    N = int(np.prod(dims))
    c = first_column_nd(dims, kfun)
    spec0 = np.fft.rfftn(embed_wss_nd(c, dims)).real
    spec_p = np.maximum(spec0, 0.0) + lam
    cinv = np.zeros_like(spec_p)
    np.divide(1.0, spec_p, out=cinv, where=np.abs(spec_p) > 1e-14)
    sl = _prin_slice(dims)
    ed = _edims(dims)

    def spectral_dir(g_full):
        Ge = np.zeros(ed)
        Ge[sl] = g_full.reshape(dims)
        P = np.fft.irfftn(np.fft.rfftn(Ge) * cinv, s=ed)
        return P[sl].ravel()

    def masked_resid(alpha):
        return amatvec_nd(alpha, dims, kfun, lam, spec0)[obs] - y[obs]

    b = y[obs]
    r0 = max(float(np.linalg.norm(b)), 1e-30)
    alpha = np.zeros(N)
    alpha_prev = alpha.copy()
    hist_a = []
    hist_g = []
    rel_trace = []
    iters = 0
    conv = False
    restarts = 0
    for k in range(1, max_iter + 1):
        almax = float(np.max(np.abs(alpha))) if np.all(np.isfinite(alpha)) \
            else float("inf")
        if not np.isfinite(almax) or almax > 1e8:
            alpha = alpha_prev
            restarts += 1
            continue
        g = masked_resid(alpha)
        rel = float(np.linalg.norm(g)) / r0
        rel_trace.append(rel)
        eta = 0.5 / (1.0 + (k - 1) / 200.0)
        if not np.isfinite(rel) or rel > 1e12:
            alpha = alpha_prev
            restarts += 1
            continue
        if rel <= tol:
            conv = True
            iters = k
            break
        mom = (k - 1) / (k + 2.0) if k > 1 else 0.0
        yk = alpha + mom * (alpha - alpha_prev)
        g_full = np.zeros(N)
        g_full[obs] = g
        d_full = spectral_dir(g_full)
        alpha_new = yk - eta * d_full
        # spatial step: soft projection on the observed subspace
        alpha_off = alpha_new.copy()
        alpha_off[obs] = 0.0
        alpha_new = alpha_new - 0.99 * alpha_off
        if not np.all(np.isfinite(alpha_new)) or \
                float(np.max(np.abs(alpha_new))) > 1e8:
            alpha_new = alpha_prev
            restarts += 1
        hist_a.append(alpha_new.copy())
        g_new = masked_resid(alpha_new)
        hist_g.append(g_new.copy())
        if len(hist_a) > m_anderson:
            hist_a.pop(0)
            hist_g.pop(0)
        if len(hist_a) > 1:
            alpha_mix, cnorm, ok = anderson_mix(hist_a, hist_g, g_new)
            if ok:
                g_mix = masked_resid(alpha_mix)
                rel_mix = float(np.linalg.norm(g_mix)) / r0
                rel_new = float(np.linalg.norm(g_new)) / r0
                if np.isfinite(rel_mix) and rel_mix <= rel_new * 1.05 + 1e-30:
                    alpha_new = alpha_mix
                    g_new = g_mix
                    hist_a[-1] = alpha_new.copy()
                    hist_g[-1] = g_new.copy()
                else:
                    hist_a.clear()
                    hist_g.clear()
        alpha_prev = alpha
        alpha = alpha_new
        iters = k
    rel_trace.append(float(np.linalg.norm(masked_resid(alpha))) / r0)
    rel_res = rel_trace[-1]
    out = dict(alpha=alpha, iters=iters, conv=conv, rel_res=rel_res,
               restarts=restarts)
    if return_trace:
        out["trace"] = rel_trace
    return out


# ---------------------------------------------------------------------------
# Self-check: matvec exactness + full-tail correction exactness vs dense
# ---------------------------------------------------------------------------
def selfcheck():
    rng = np.random.default_rng(0)
    ok = True
    for dims in [(16, 16), (8, 8, 8)]:
        N = int(np.prod(dims))
        for kname in ["matern32", "rbf"]:
            kfun = make_nd_kernel(kname)
            y = rng.standard_normal(N)
            lam = 1e-3
            # dense free Gram
            idx = np.arange(N)
            grids = [np.arange(d) for d in dims]
            gg = np.meshgrid(*grids, indexing="ij")
            G = np.empty((N, N))
            coords = np.unravel_index(idx, dims)
            for j in range(N):
                cj = tuple(g.ravel()[j] for g in gg)
                G[:, j] = kfun(tuple(np.abs(c.ravel() - cj[ax]).ravel()
                                     for ax, c in enumerate(gg))).ravel()
            A = G + lam * np.eye(N)
            a_star = np.linalg.solve(A, y)
            spec0 = np.fft.rfftn(embed_wss_nd(first_column_nd(dims, kfun), dims)).real
            err_mv = np.linalg.norm(amatvec_nd(y, dims, kfun, lam, spec0) - A @ y) \
                / np.linalg.norm(A @ y)
            # naive + full-tail correction (exact in limit)
            prin, tail, _ = idx_sets_nd(dims)
            spec_used = np.maximum(spec0, 0.0) + lam
            z0 = z0_nd(y, dims, spec_used)
            a0 = z0[prin]
            L = int(np.prod(_edims(dims)))
            WTT = np.empty((len(tail), len(tail)))
            for j in range(len(tail)):
                e = np.zeros(L)
                e[tail[j]] = 1.0
                WTT[:, j] = cinv_nd(e, dims, spec_used)[tail]
            uT = np.linalg.solve(WTT, z0[tail])
            u = np.zeros(L)
            u[tail] = uT
            corr = cinv_nd(u, dims, spec_used)[prin]
            alpha = a0 - corr
            err_corr = np.linalg.norm(alpha - a_star) / np.linalg.norm(a_star)
            print(f"selfcheck dims={dims} {kname}: matvec_err={err_mv:.2e} "
                  f"corr_err={err_corr:.2e}")
            ok = ok and err_mv < 1e-10 and err_corr < 1e-9
    return ok


# ---------------------------------------------------------------------------
# Iteration-4 F1: DST2-class exact Woodbury-center band solver (arm A1-F1)
# ---------------------------------------------------------------------------
# Operator equation (proposal-iter4-v4 F1_operator_equation):
#   M = K_emb + lam I   (whole-sample-symmetric (2d-1)-per-axis first-column
#   embedding of the free BTTB; principal block matvec-exact for the free
#   operator; spectral domain solve, spectrum floored at 0 with n_neg
#   disclosed)
#   WTT u_T = z0[T],  WTT = M^{-1}[T,T],  T = boundary band index set
#   (tail cells with seam/Chebyshev oob distance < w; measured nb = |T|)
#   alpha = a0 - M^{-1}u   (u = u_T on T, zero elsewhere; spectral map-back)
#   residuals measured on the EXACT free operator only: amatvec_nd.
# The map-back is EXACT (in exact arithmetic) when T = the full tail
# (block-inverse identity M_pp^{-1} = B_pp - B_pt B_tt^{-1} B_tp); band
# truncation leaves far-tail coupling, measured per row. Dense center:
# O(nb^3) time / O(N + nb^2) memory; cond(WTT) measured per grid (SPD
# post-floor+ridge, principal submatrix property -- never assumed).
# ---------------------------------------------------------------------------
def embed_wss_dst2(c, dims):
    """Whole-sample-symmetric (2d-1)-per-axis first-column embedding in the
    DST2-class reading (plan-iter4 glossary: the iteration-4 embedding is the
    DST2-class form; same (2d-1) WSS matrix that is matvec-exact on the free
    BTTB principal block; diagonalized in its symmetric-boundary spectral
    domain). Aliased to embed_wss_nd for traceability."""
    return embed_wss_nd(c, dims)


def dst2_exact_band_nd(y, dims, kfun, lam, w, ref=None, spec0=None,
                       spec_used=None, measure_support=True):
    """F1: DST2-class embedding solve + EXACT Woodbury-center band solve.

    Returns dict: alpha, alpha0, naive_res, res (relative, exact operator),
    nb (|T|), cond_wtt, support s / w_s / coverage, band/interior residual
    fractions, gap/gap_naive vs ref when given.
    """
    y = np.asarray(y, dtype=np.float64).ravel()
    if spec0 is None:
        c = first_column_nd(dims, kfun)
        spec0 = np.fft.rfftn(embed_wss_dst2(c, dims)).real
    if spec_used is None:
        spec_used = np.maximum(spec0, 0.0) + lam
    L = int(np.prod(_edims(dims)))
    z0 = z0_nd(y, dims, spec_used)
    prin, tail, dmin = idx_sets_nd(dims)
    a0 = z0[prin]
    norm_y = max(float(np.linalg.norm(y)), 1e-30)
    r0 = float(np.linalg.norm(y - amatvec_nd(a0, dims, kfun, lam, spec0))) / norm_y
    out = dict(alpha=a0, alpha0=a0, naive_res=r0, res=r0, rank=0, T_size=0,
               nb=0, cond_wtt=None, band_res=float("nan"),
               interior_res=float("nan"), support_s=0, support_w_s=0.0,
               support_s_threshold=0.0, coverage=0.0)
    T = tail[dmin < w]
    if len(T) == 0:
        return out
    nb = len(T)
    WTT = np.empty((nb, nb))
    for j in range(nb):
        e = np.zeros(L)
        e[T[j]] = 1.0
        WTT[:, j] = cinv_nd(e, dims, spec_used)[T]
    # SPD post-floor+ridge -> symmetric center; cond measured via eig ratio
    try:
        ev = np.linalg.eigvalsh(0.5 * (WTT + WTT.T))
        cond_wtt = float(ev[-1] / max(ev[0], 1e-300)) if ev[0] > 1e-300 else None
    except np.linalg.LinAlgError:
        cond_wtt = None
    uT = np.linalg.solve(WTT, z0[T])
    u = np.zeros(L)
    u[T] = uT
    corr = cinv_nd(u, dims, spec_used)[prin]
    alpha = a0 - corr
    r = y - amatvec_nd(alpha, dims, kfun, lam, spec0)
    res = float(np.linalg.norm(r)) / norm_y
    bcell = band_mask_nd(dims, w)  # bool over the N principal cells
    rarr = r.reshape(dims).ravel()
    band_n = np.linalg.norm(rarr[bcell])
    int_n = np.linalg.norm(rarr[~bcell])
    denom = max(band_n + int_n, 1e-30)
    out.update(alpha=alpha, res=res, rank=int(nb), T_size=int(nb), nb=int(nb),
               cond_wtt=cond_wtt, band_res=float(band_n / denom),
               interior_res=float(int_n / denom))
    if measure_support:
        # support of the tail coupling: S = {cells: |H_r| > 1e-6*max|H_r|}
        # with H_r the uncorrected coupling field (residual of the naive
        # embedded solve on the EXACT free operator).
        Hr = y - amatvec_nd(a0, dims, kfun, lam, spec0)
        maxr = float(np.max(np.abs(Hr)))
        thr = 1e-6 * max(1e-30, maxr)
        S = np.abs(Hr.reshape(dims)) > thr
        s = int(S.sum())
        gridsd = [np.arange(d) for d in dims]
        ggm = np.meshgrid(*gridsd, indexing="ij")
        d_bnd = None
        for ax, g in enumerate(ggm):
            dc = np.minimum(g, dims[ax] - 1 - g)
            d_bnd = dc if d_bnd is None else np.maximum(d_bnd, dc)
        w_s = float(d_bnd.ravel()[S.ravel()].max()) if s else 0.0
        out.update(support_s=s, support_w_s=w_s, support_s_threshold=thr,
                   coverage=float(s / max(len(T), 1)))
    if ref is not None:
        rf = np.asarray(ref, dtype=np.float64).ravel()
        nref = max(float(np.linalg.norm(rf)), 1e-30)
        out["gap"] = float(np.linalg.norm(alpha - rf)) / nref
        out["gap_naive"] = float(np.linalg.norm(a0 - rf)) / nref
    return out


def dst2_exact_sweep_nd(y, dims, kfun, lam, ws=(1, 2, 3, 4), w_design=None,
                        ref=None):
    """Per-w F1 report + monotone-decay fail-fast (iteration-3 convention)."""
    c = first_column_nd(dims, kfun)
    spec0 = np.fft.rfftn(embed_wss_dst2(c, dims)).real
    spec_used = np.maximum(spec0, 0.0) + lam
    out = {"w_sweep": {}, "w_design": None, "fail_fast": False,
           "naive_res": None}
    prev = None
    for w in ws:
        r = dst2_exact_band_nd(y, dims, kfun, lam, w, ref=ref, spec0=spec0,
                               spec_used=spec_used, measure_support=False)
        entry = {k: v for k, v in r.items() if k not in ("alpha", "alpha0")}
        out["w_sweep"][int(w)] = entry
        if prev is not None and r["res"] > prev * (1.0 + 1e-12):
            out["fail_fast"] = True
        prev = r["res"] if prev is None else min(prev, r["res"])
    out["naive_res"] = out["w_sweep"][int(ws[0])]["naive_res"]
    if w_design is not None:
        r = dst2_exact_band_nd(y, dims, kfun, lam, w_design, ref=ref,
                               spec0=spec0, spec_used=spec_used,
                               measure_support=True)
        out["w_design"] = {k: v for k, v in r.items()
                           if k not in ("alpha", "alpha0")}
        out["w_design"]["w"] = int(w_design)
        out["alpha"] = r["alpha"]
    return out


def full_support_diag_nd(y, dims, kfun, lam, ref=None, nb_cap=None,
                         spec0=None, spec_used=None):
    """F1 diagnostic: exact center solve with T = FULL TAIL, capped at the
    cgroup-permitted center size (nb_cap; honest not-completed wording lives
    in the caller). Returns the same dict shape as dst2_exact_band_nd with
    support measurements."""
    y = np.asarray(y, dtype=np.float64).ravel()
    if spec0 is None:
        c = first_column_nd(dims, kfun)
        spec0 = np.fft.rfftn(embed_wss_dst2(c, dims)).real
    if spec_used is None:
        spec_used = np.maximum(spec0, 0.0) + lam
    L = int(np.prod(_edims(dims)))
    z0 = z0_nd(y, dims, spec_used)
    prin, tail, dmin = idx_sets_nd(dims)
    a0 = z0[prin]
    norm_y = max(float(np.linalg.norm(y)), 1e-30)
    r0 = float(np.linalg.norm(y - amatvec_nd(a0, dims, kfun, lam, spec0))) / norm_y
    T = tail
    if nb_cap is not None and len(T) > nb_cap:
        # dmin is already indexed over the tail cells (idx_sets_nd), so sort
        # it directly; keep the nearest tail cells so the solve stays bounded,
        # and let the caller mark the row not-completed as full support when
        # nb > nb_cap
        keep = np.argsort(dmin, kind="stable")[:nb_cap]
        T = tail[keep]
    nb = len(T)
    WTT = np.empty((nb, nb))
    for j in range(nb):
        e = np.zeros(L)
        e[T[j]] = 1.0
        WTT[:, j] = cinv_nd(e, dims, spec_used)[T]
    try:
        ev = np.linalg.eigvalsh(0.5 * (WTT + WTT.T))
        cond_wtt = float(ev[-1] / max(ev[0], 1e-300)) if ev[0] > 1e-300 else None
    except np.linalg.LinAlgError:
        cond_wtt = None
    uT = np.linalg.solve(WTT, z0[T])
    u = np.zeros(L)
    u[T] = uT
    corr = cinv_nd(u, dims, spec_used)[prin]
    alpha = a0 - corr
    r = y - amatvec_nd(alpha, dims, kfun, lam, spec0)
    res = float(np.linalg.norm(r)) / norm_y
    out = dict(alpha=alpha, alpha0=a0, naive_res=r0, res=res, nb=int(nb),
               T_size=int(nb), rank=int(nb), cond_wtt=cond_wtt,
               tail_total=int(len(tail)))
    if ref is not None:
        rf = np.asarray(ref, dtype=np.float64).ravel()
        nref = max(float(np.linalg.norm(rf)), 1e-30)
        out["gap"] = float(np.linalg.norm(alpha - rf)) / nref
        out["gap_naive"] = float(np.linalg.norm(a0 - rf)) / nref
    return out


# ---------------------------------------------------------------------------
# Iteration-4 F2: preconditioned Anderson mixing on the masked Gram
# (arm A2-F2): shared system (P_m K P_m^T + lam I) w = y_m; randomized
# Nystrom preconditioner (Frangella-Tropp-Udell 71) + Anderson window m = 5
# (A5-essential evidence), KKT termination, iteration ceiling 500.
# ---------------------------------------------------------------------------
def ssam_nystrom_nd(y, obs_idx, dims, kfun, lam, k_sketch=64, tol=1e-6,
                    max_iter=500, m_anderson=5, seed=0, return_trace=False):
    """Preconditioned Anderson mixing: updates w -= eta * P_nystrom(g) with
    Anderson(m) mixing on (w, g) pairs; returns (alpha, iters, conv, rel_res,
    restarts, setup_s)."""
    y = np.asarray(y, dtype=np.float64).ravel()
    obs = np.asarray(obs_idx, dtype=np.int64)
    N = int(np.prod(dims))
    c = first_column_nd(dims, kfun)
    spec0 = np.fft.rfftn(embed_wss_nd(c, dims)).real
    sl = _prin_slice(dims)
    ed = _edims(dims)

    def A_masked(w):
        """(P_m K P_m^T + lam I) w on the observed subspace."""
        full = np.zeros(N)
        full[obs] = w
        return amatvec_nd(full, dims, kfun, lam, spec0)[obs]

    # randomized Nystrom sketch: S (n_obs x k); B = A S; C = S^T B
    t0 = time.perf_counter()
    n_obs = len(obs)
    rng = np.random.default_rng(seed)
    k = int(min(k_sketch, n_obs))
    S = rng.standard_normal((n_obs, k)) / np.sqrt(k)
    B = np.empty((n_obs, k))
    for j in range(k):
        B[:, j] = A_masked(S[:, j])
    C = S.T @ B
    # eigen-decompose C (k x k); truncate spurious/negative eigenvalues
    ev, Q = np.linalg.eigh(0.5 * (C + C.T))
    emax = float(ev[-1])
    keep = ev > max(1e-12 * max(emax, 1.0), 0.0)
    kk = int(keep.sum())
    if kk == 0:
        kk = 1
        keep[-1] = True
    Q = Q[:, keep]
    ev = ev[keep]
    # W = B Q Lambda^{-1/2}: approximate eigenvectors of the masked Gram
    W = B @ (Q / np.sqrt(np.maximum(ev, 1e-30)))
    G = np.eye(kk) + (W.T @ W) / lam  # Woodbury k x k factor
    setup_s = time.perf_counter() - t0

    def precond(g):
        """(W W^T + lam I)^{-1} g via Woodbury."""
        z = g / lam
        t = np.linalg.solve(G, W.T @ g)
        return z - (W @ t) / lam

    b = y[obs]
    r0 = max(float(np.linalg.norm(b)), 1e-30)
    w = np.zeros(n_obs)
    hist_a = []
    hist_g = []
    rel_trace = []
    restarts = 0
    conv = False
    iters = 0
    for kk_ in range(1, max_iter + 1):
        g = A_masked(w) - b
        rel = float(np.linalg.norm(g)) / r0
        rel_trace.append(rel)
        if not np.isfinite(rel) or rel > 1e12:
            restarts += 1
            w = np.zeros(n_obs)
            hist_a.clear()
            hist_g.clear()
            continue
        if rel <= tol:
            conv = True
            iters = kk_
            break
        eta = 1.0 / (1.0 + (kk_ - 1) / 40.0)
        d = precond(g)
        w_new = w - eta * d
        hist_a.append(w_new.copy())
        hist_g.append(A_masked(w_new) - b)
        if len(hist_a) > m_anderson:
            hist_a.pop(0)
            hist_g.pop(0)
        if len(hist_a) > 1:
            w_mix, cnorm, ok = anderson_mix(hist_a, hist_g, hist_g[-1])
            if ok:
                g_mix = A_masked(w_mix) - b
                rel_mix = float(np.linalg.norm(g_mix)) / r0
                rel_new = float(np.linalg.norm(hist_g[-1])) / r0
                if np.isfinite(rel_mix) and rel_mix <= rel_new * 1.05 + 1e-30:
                    w_new = w_mix
                    hist_g[-1] = g_mix
                    hist_a[-1] = w_new.copy()
                else:
                    hist_a.clear()
                    hist_g.clear()
        w = w_new
        iters = kk_
    rel_res = float(np.linalg.norm(A_masked(w) - b)) / r0
    alpha = np.zeros(N)
    alpha[obs] = w
    out = dict(alpha=alpha, iters=iters, conv=conv, rel_res=rel_res,
               restarts=restarts, setup_s=setup_s, k_sketch=int(k),
               k_effective=int(kk))
    if return_trace:
        out["trace"] = rel_trace
    return out


if __name__ == "__main__":
    import sys
    ok = selfcheck()
    print("SELFCHECK", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)
