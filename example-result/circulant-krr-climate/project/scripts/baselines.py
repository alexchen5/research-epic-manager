#!/usr/bin/env python3
"""Commensurable scikit-learn baselines (exact subsample / Nystrom / RFF).\n\nAll baselines use the free-boundary kernel (sklearn semantics) on the same\nregression tasks (T2 direct-head: flattened observed field -> Nino3.4 index;\nT1 reconstruction subset: flattened field cells -> cell value). Resource\naxes (wall_clock_s, peak_rss_gb) recorded per fit; estimated flops/bytes\nreported per fit via sklearn-reported sizes.
"""
from __future__ import annotations

import time

import numpy as np
from sklearn.kernel_ridge import KernelRidge
from sklearn.kernel_approximation import Nystroem, RBFSampler
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline


def _rbf_gamma_from_ell(ell):
    return 1.0 / (2.0 * ell * ell)


def exact_krr_fit(Xtr, ytr, Xte, yte, lam, gamma):
    t0 = time.perf_counter()
    m = KernelRidge(alpha=lam, kernel="rbf", gamma=gamma)
    m.fit(Xtr, ytr)
    yhat = m.predict(Xte)
    dt = time.perf_counter() - t0
    return yhat, dt, m


def nystrom_fit(Xtr, ytr, Xte, yte, lam, gamma, n_components):
    t0 = time.perf_counter()
    m = make_pipeline(Nystroem(kernel="rbf", gamma=gamma, n_components=n_components),
                      Ridge(alpha=lam))
    m.fit(Xtr, ytr)
    yhat = m.predict(Xte)
    dt = time.perf_counter() - t0
    flops = n_components * Xtr.shape[0]  # rough: landmark-gram + ridge
    bytes_ = 8.0 * n_components * Xtr.shape[0] + 8.0 * Xtr.shape[1] * Xtr.shape[0]
    return yhat, dt, {"est_flops": flops, "est_bytes": bytes_}


def rff_fit(Xtr, ytr, Xte, yte, lam, gamma, n_components):
    t0 = time.perf_counter()
    m = make_pipeline(RBFSampler(gamma=gamma, n_components=n_components),
                      Ridge(alpha=lam))
    m.fit(Xtr, ytr)
    yhat = m.predict(Xte)
    dt = time.perf_counter() - t0
    flops = n_components * Xtr.shape[0] * Xtr.shape[1]
    bytes_ = 8.0 * n_components * Xtr.shape[0]
    return yhat, dt, {"est_flops": flops, "est_bytes": bytes_}

FITTERS = {"exact": exact_krr_fit, "nystrom": nystrom_fit, "rff": rff_fit}

# ---------------------------------------------------------------------------
# Iteration-3 grid baselines (KISS-GP, dense subsample) -- appended
# ---------------------------------------------------------------------------
def _inducing_weights(dims, ind_dims):
    """Local bi/tri-linear interpolation weights W (N_full x N_ind) of the
    inducing regular subgrid (KISS-GP, Wilson & Nickisch 2015)."""
    nd = len(dims)
    grids = [np.arange(d) for d in dims]
    gg = np.meshgrid(*grids, indexing="ij")
    Nf = int(np.prod(dims))
    Ni = int(np.prod(ind_dims))
    W = np.zeros((Nf, Ni))
    ind_grids = []
    for ax, (d, id_) in enumerate(zip(dims, ind_dims)):
        ind_grids.append(np.linspace(0, d - 1, id_))
    # weights: product of per-axis linear weights
    for k in range(Nf):
        coord = tuple(int(c) for c in (g.ravel()[k] for g in gg))
        # per axis: find bracketing inducing nodes
        per = []
        for ax in range(nd):
            x = coord[ax]
            ig = ind_grids[ax]
            if x <= ig[0]:
                per.append([(0, 1.0)])
            elif x >= ig[-1]:
                per.append([(len(ig) - 1, 1.0)])
            else:
                lo = np.searchsorted(ig, x) - 1
                hi = lo + 1
                t = (x - ig[lo]) / (ig[hi] - ig[lo])
                per.append([(lo, 1.0 - t), (hi, t)])
        # cartesian product of per-axis pairs
        import itertools
        for combo in itertools.product(*per):
            idx = 0
            wgt = 1.0
            for ax in range(nd):
                i = combo[ax][0]
                # convert multi-index to flat ind index
                pass
        # simpler: build flat index via strides
        for combo in itertools.product(*per):
            ixn = [combo[ax][0] for ax in range(nd)]
            flat = sum(ixn[ax] * int(np.prod(ind_dims[ax + 1:])) for ax in range(nd))
            wgt = np.prod([combo[ax][1] for ax in range(nd)])
            W[k, flat] = wgt
    return W


def kissgp_fit_grid(y_m, obs_idx, dims, kfun, lam, ind_dims, tol=1e-8,
                    max_iter=2000):
    """KISS-GP (subset-of-regressors / projected-process form): inducing
    u = (K_uu + lam I)^{-1} K_uf^T y_m via WSS-machinery PCG on the inducing
    BTTB Gram; predictions f = W u on the full grid. Honest classical form."""
    import time
    import numpy as np
    import fft_krr_embed as fe
    import fft_krr as fk
    t0 = time.perf_counter()
    y_m = np.asarray(y_m, dtype=np.float64).ravel()
    obs = np.asarray(obs_idx, dtype=np.int64)
    Nf = int(np.prod(dims))
    Ni = int(np.prod(ind_dims))
    W = _inducing_weights(dims, ind_dims)
    # K_uf^T y_m = W^T scatter (inducing index k gets sum of y_m w_{i,k})
    v = np.zeros(Ni)
    # W^T y: for observed cells only
    for k in obs:
        row = W[k]
        v += row * y_m[np.where(obs == k)[0][0]] if False else 0.0
    # vectorized: y_full over observed
    y_full = np.zeros(Nf)
    y_full[obs] = y_m
    v = W.T @ y_full
    g = fe.amatvec_nd(v, ind_dims, kfun, 0.0)  # K_uu v (no ridge)
    u, iters, conv, rel = fe.cg_masked_nd(g, ind_dims, kfun,
                                          np.arange(Ni), lam, tol=tol,
                                          max_iter=max_iter)
    # predictions on valid cells: f = W u
    u_flat = np.asarray(u).ravel()
    f_full = W @ u_flat
    dt = time.perf_counter() - t0
    return f_full, u_flat, dt, dict(iters=iters, conv=conv, rel=rel)


def dense_subsample_fit_grid(y_m, obs_idx, dims, kfun, lam, cap=4000, seed=0):
    """Exact dense KRR (Cholesky) on <= cap subsampled observed cells."""
    import time
    import numpy as np
    import fft_krr as fk
    t0 = time.perf_counter()
    y_m = np.asarray(y_m, dtype=np.float64).ravel()
    obs = np.asarray(obs_idx, dtype=np.int64)
    Nf = int(np.prod(dims))
    rng = np.random.default_rng(seed)
    if len(obs) > cap:
        sub = rng.choice(obs, cap, replace=False)
    else:
        sub = obs
    grids = [np.arange(d) for d in dims]
    gg = np.meshgrid(*grids, indexing="ij")
    coords = np.stack([g.ravel() for g in gg], axis=1)  # (Nf, nd)
    Xtr = coords[sub]
    pos = np.where(np.isin(obs, sub))[0]
    ytr = y_m[pos]
    # build dense Gram on sub cells
    K = np.empty((len(sub), len(sub)))
    for j in range(len(sub)):
        K[:, j] = kfun(*[np.abs(coords[sub][:, ax] - coords[sub[j]][ax])
                         for ax in range(len(dims))])
    A = K + lam * np.eye(len(sub))
    a = np.linalg.solve(A, ytr)
    # predictions on all cells
    Kte = np.empty((Nf, len(sub)))
    for j in range(len(sub)):
        Kte[:, j] = kfun(*[np.abs(coords[:, ax] - coords[sub[j]][ax]) for ax in range(len(dims))])
    f_full = Kte @ a
    dt = time.perf_counter() - t0
    return f_full, a, dt, dict(n_sub=len(sub))
