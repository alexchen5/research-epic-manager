#!/usr/bin/env python3
"""Circulant spectral kernel ridge regression on regular grids (CPU-only).

Method (honest framing, per approved proposal + hypothesis-gate feedback):
  For a stationary kernel on a regular (Ny x Nx) grid, the Gram matrix of the
  PERIODIZED (torus) kernel is a block-circulant-with-circulant-blocks (BCCB)
  matrix determined by its first (torus) column; the KRR solve is then exact
  and closed-form in the spectral domain:
      alpha = irfft2( rfft2(y) / (rfft2(c_torus) + lam) ),   O(N log N) time,
      O(N) memory, no explicit N x N Gram matrix.
  Qualification (as pre-committed): this is EXACT for the embedded-torus
  kernel. The free-boundary stationary Gram is BTTB; the torus-vs-free kernel
  difference decays with kernel length-scale / grid-extent and is measured in
  the pilot (embedding_error_sweep: padding/ell sweeps). The FFT-preconditioned
  conjugate-gradient solve (cg_masked_solve) provides the free-boundary solve
  to tolerance in O(N log N) per iteration (T1b arm).

Also provides:
  - predict_torus: full-field prediction via spectral cross-correlation.
  - predict_box_functional: kernel-consistent linear functional (area-weighted
    box mean, e.g., Nino3.4) - O(N log N).
  - cg_masked_solve: FFT-preconditioned CG for masked/subset training.
  - fit_dense / predict_dense (free boundary) and fit_dense_torus for the
    pilot gate only (small grids).

float64 numpy only; no scikit-learn, no torch.
"""
from __future__ import annotations

import numpy as np

__all__ = [
    "KERNELS", "first_column", "torus_first_column", "embed_torus_column",
    "fit_torus", "predict_torus", "fit_dense", "fit_dense_torus",
    "predict_dense", "predict_box_functional", "cg_masked_solve",
]


# ---------------------------------------------------------------------------
# Stationary kernels on a regular grid (lags in grid units)
# ---------------------------------------------------------------------------
def _dist2(dy, dx):
    return dy * dy + dx * dx


def kernel_matern32(dy, dx, ell=4.0):
    r = np.sqrt(_dist2(dy, dx)) / ell
    r = np.minimum(r, 1e3)
    return (1.0 + r) * np.exp(-r)


def kernel_matern52(dy, dx, ell=4.0):
    r = np.sqrt(_dist2(dy, dx)) / ell
    r = np.minimum(r, 1e3)
    return (1.0 + r + r * r / 3.0) * np.exp(-r)


def kernel_rbf(dy, dx, ell=4.0):
    r2 = _dist2(dy, dx) / (2.0 * ell * ell)
    return np.exp(-r2)


def _mk(kfun, ell):
    return lambda dy, dx: kfun(dy, dx, ell)


KERNELS = {
    "matern32": lambda dy, dx: kernel_matern32(dy, dx),
    "matern52": lambda dy, dx: kernel_matern52(dy, dx),
    "rbf": lambda dy, dx: kernel_rbf(dy, dx),
}


def make_kernel(name, ell):
    raw = {"matern32": kernel_matern32, "matern52": kernel_matern52,
           "rbf": kernel_rbf}[name]
    return lambda dy, dx: raw(dy, dx, ell)


def first_column(ny, nx, kfun):
    """First column of the free-boundary BTTB Gram: kfun(|dy|,|dx|) lags."""
    dy = np.arange(ny)[:, None]
    dx = np.arange(nx)[None, :]
    return kfun(dy, dx)


def torus_first_column(ny, nx, kfun):
    """First column of the BCCB Gram of the periodized kernel."""
    iy = np.arange(ny)[:, None]
    ix = np.arange(nx)[None, :]
    dy = np.minimum(iy, ny - iy)
    dx = np.minimum(ix, nx - ix)
    return kfun(dy, dx)


def embed_first_column(c, pad_frac=1.0):
    """Mirror (Toeplitz-to-circulant) embedding of the free-boundary first
    column c (ny x nx) into a BCCB first column of size (nyc, nxc).

    Principal-block property: the leading (ny x nx) block of the embedded
    circulant equals the free-boundary BTTB Gram, so T x = (C [x;0])[:N]
    exactly -- used for EXACT free-boundary MATVECs in O(N log N)
    (solving still needs CG, see cg_masked_solve).
    """
    ny, nx = c.shape
    nyc = max(ny, int(np.ceil(pad_frac * (2 * ny - 1))))
    nxc = max(nx, int(np.ceil(pad_frac * (2 * nx - 1))))
    c_ext = np.zeros((nyc, nxc))
    c_ext[:ny, :nx] = c
    c_ext[:ny, nxc - (nx - 1):] = c[:, nx - 1:0:-1]
    c_ext[nyc - (ny - 1):, :nx] = c[ny - 1:0:-1, :]
    c_ext[nyc - (ny - 1):, nxc - (nx - 1):] = c[ny - 1:0:-1, nx - 1:0:-1]
    return c_ext, nyc, nxc


def embed_torus_column(c, pad_frac=1.0):
    """Pad the torus first column c (ny x nx) into (nyc x nxc) with zeros.

    Used for the embedding/padding characterization sweeps only: a larger
    zero-padded domain makes the wrap-around images of the torus kernel more
    distant. The main method (fit_torus) needs NO padding.
    """
    ny, nx = c.shape
    nyc = max(ny, int(np.ceil(pad_frac * ny)))
    nxc = max(nx, int(np.ceil(pad_frac * nx)))
    c_ext = np.zeros((nyc, nxc))
    c_ext[:ny, :nx] = c
    return c_ext, nyc, nxc


# ---------------------------------------------------------------------------
# Exact spectral fit / predict (torus kernel)
# ---------------------------------------------------------------------------
def torus_spectrum(ny, nx, kfun, lam=0.0, floor=True):
    """rfft2 spectrum of the torus Gram, with PSD floor + ridge added.

    The torus Gram of some kernels (e.g., RBF at 36x72) has small negative
    eigenvalues (inherent to circulant embedding of a non-torus kernel). The
    standard remedy is a spectral floor at 0 applied to the kernel spectrum,
    then the ridge lam is added (lam*I adds lam to every eigenvalue), so the
    solver never divides by zero. Returns (spec_used, min_eig_raw, n_negative).
    """
    c = torus_first_column(ny, nx, kfun)
    spec_raw = np.fft.rfft2(c)
    min_eig = float(spec_raw.real.min())
    n_neg = int(np.sum(spec_raw.real < 0.0))
    spec = np.maximum(spec_raw, 0.0) if (floor and n_neg > 0) else spec_raw
    if lam > 0.0:
        spec = spec + lam  # I is BCCB: lam*I adds lam to every eigenvalue
    return spec, min_eig, n_neg


def fit_torus(y, ny, nx, kfun, lam=1e-3, return_spectrum=False):
    """Exact O(N log N) solve of (G + lam*I) alpha = y for the torus kernel."""
    y = np.asarray(y, dtype=np.float64).reshape(ny, nx)
    spec, min_eig, n_neg = torus_spectrum(ny, nx, kfun, lam=lam, floor=True)
    alpha = np.fft.irfft2(np.fft.rfft2(y) / spec, s=(ny, nx))
    if return_spectrum:
        return alpha, spec, {"min_eig_raw": min_eig, "n_negative": n_neg}
    return alpha


def predict_torus(alpha, ny, nx, kfun, spec=None):
    """Full-field prediction P = G alpha via spectral cross-correlation."""
    alpha = np.asarray(alpha, dtype=np.float64)
    if spec is None:
        spec, _min_eig, _n_neg = torus_spectrum(ny, nx, kfun, lam=0.0, floor=True)
    P = np.fft.irfft2(np.fft.rfft2(alpha) * spec, s=(ny, nx))
    return P


def predict_box_functional(alpha, ny, nx, kfun, src_iy, src_ix, spec=None):
    """Kernel-consistent area-weighted box mean (linear functional of alpha).

    value = sum_b w_b [G(x_b, x) alpha]_b with w_b uniform over the box.
    Computed via the spectral cross-correlation: no grid resampling.
    """
    P = predict_torus(alpha, ny, nx, kfun, spec=spec)
    return float(np.mean(P[np.ix_(src_iy, src_ix)]))


# ---------------------------------------------------------------------------
# Dense references (pilot gate only; O(N^2) memory / O(N^3) time)
# ---------------------------------------------------------------------------
def _dense_gram(ny, nx, kfun, torus=False, lam=1e-3):
    N = ny * nx
    iy, ix = np.divmod(np.arange(N)[:, None], nx)
    jy, jx = np.divmod(np.arange(N)[None, :], nx)
    if torus:
        dy = np.minimum(np.abs(iy - jy), ny - np.abs(iy - jy))
        dx = np.minimum(np.abs(ix - jx), nx - np.abs(ix - jx))
    else:
        dy = iy - jy
        dx = ix - jx
    K = kfun(dy, dx)
    K[np.diag_indices(N)] += lam
    return K


def fit_dense(y, ny, nx, kfun, lam=1e-3, torus=False):
    y = np.asarray(y, dtype=np.float64).reshape(-1)
    K = _dense_gram(ny, nx, kfun, torus=torus, lam=lam)
    return np.linalg.solve(K, y).reshape(ny, nx)


def fit_dense_torus(y, ny, nx, kfun, lam=1e-3):
    return fit_dense(y, ny, nx, kfun, lam=lam, torus=True)


def predict_dense(alpha, ny, nx, kfun, torus=False):
    N = ny * nx
    iy, ix = np.divmod(np.arange(N)[:, None], nx)
    jy, jx = np.divmod(np.arange(N)[None, :], nx)
    if torus:
        dy = np.minimum(np.abs(iy - jy), ny - np.abs(iy - jy))
        dx = np.minimum(np.abs(ix - jx), nx - np.abs(ix - jx))
    else:
        dy = iy - jy
        dx = ix - jx
    K = kfun(dy, dx)
    return (K @ alpha.reshape(-1)).reshape(ny, nx)


# ---------------------------------------------------------------------------
# Masked training via FFT-preconditioned CG (T1b; free-boundary to tolerance)
# ---------------------------------------------------------------------------
def cg_masked_solve(y, ny, nx, kfun, obs_idx, lam=1e-3, tol=1e-8,
                    max_iter=2000):
    """Solve the exact free-boundary system (K_obs + lam*I) x = y_obs with PCG.

    - matvec: EXACT free-boundary BTTB matvec via the (2N-1)-mirror circulant
      embedding (classic result: the principal block of the embedded circulant
      equals the free Toeplitz Gram, so T x = (C [x;0])[:N] exactly), applied
      on the observed subset -- O(N log N) per matvec.
    - preconditioner: spectral inverse of the floored torus (G~ + lam*I),
      restricted to the observed subset (fast, spectrally close).
    Returns (alpha_full, iters, conv) where alpha_full[obs] solves the exact
    free-boundary system to the tolerance (relative residual <= tol).
    """
    y = np.asarray(y, dtype=np.float64).reshape(-1)
    obs = np.asarray(obs_idx, dtype=np.int64)
    N = ny * nx

    # exact free-boundary matvec machinery (mirror embedding, principal block)
    c_free = first_column(ny, nx, kfun)
    c_ext, nyc, nxc = embed_first_column(c_free, 1.0)
    spec_free = np.fft.rfft2(c_ext)

    def free_gram(v_full):
        V = v_full.reshape(ny, nx)
        Vext = np.zeros((nyc, nxc))
        Vext[:ny, :nx] = V
        r = np.fft.irfft2(np.fft.rfft2(Vext) * spec_free, s=(nyc, nxc))
        return r[:ny, :nx].ravel()

    def matvec(x):
        xf = np.zeros(N)
        xf[obs] = x
        return free_gram(xf)[obs] + lam * x

    # preconditioner: (floored torus G~ + lam*I)^{-1} restricted to obs
    spec_p, _me, _nn = torus_spectrum(ny, nx, kfun, lam=lam, floor=True)
    cinv = np.zeros_like(spec_p)
    np.divide(1.0, spec_p, out=cinv, where=np.abs(spec_p) > 1e-14)

    def precond(r):
        rf = np.zeros(N)
        rf[obs] = r
        V = rf.reshape(ny, nx)
        P = np.fft.irfft2(np.fft.rfft2(V) * cinv, s=(ny, nx))
        return P.ravel()[obs]

    b = y[obs]
    x = np.zeros(len(obs))
    r = b - matvec(x)
    z = precond(r)
    p = z.copy()
    rz = float(r @ z)
    r0 = float(np.linalg.norm(b))
    iters = 0
    conv = False
    for it in range(1, max_iter + 1):
        Ap = matvec(p)
        denom = float(p @ Ap)
        if denom <= 0.0 or not np.isfinite(denom):
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
    alpha_full = np.zeros(N)
    alpha_full[obs] = x
    rel_res = float(np.linalg.norm(r)) / max(1.0, r0) if len(r) else float("nan")
    return alpha_full.reshape(ny, nx), iters, conv, rel_res


def predict_masked_free(alpha_full, mask_idx, ny, nx, kfun):
    """Exact free-boundary prediction at masked cells: K(masked, all) alpha."""
    c_free = first_column(ny, nx, kfun)
    c_ext, nyc, nxc = embed_first_column(c_free, 1.0)
    spec_free = np.fft.rfft2(c_ext)
    A = np.zeros((nyc, nxc))
    A[:ny, :nx] = alpha_full
    P = np.fft.irfft2(np.fft.rfft2(A) * spec_free, s=(nyc, nxc))
    return P.ravel()[np.asarray(mask_idx, dtype=np.int64)]


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    ny = nx = 32
    y = rng.standard_normal((ny, nx))
    for kname in KERNELS:
        kf = KERNELS[kname]
        a1 = fit_torus(y, ny, nx, kf, lam=1e-3)
        # floored dense reference (same PSD-projected torus Gram as the solve)
        N = ny * nx
        c_first_v = torus_first_column(ny, nx, kf)
        spec_psd = np.maximum(np.fft.rfft2(c_first_v), 0.0) + 1e-3
        G_psd_dense = np.fft.irfft2(spec_psd, s=(ny, nx))
        rows, cols = np.indices((N, N))
        iy, ix = np.divmod(rows, nx)
        jy, jx = np.divmod(cols, nx)
        cy = np.minimum(np.abs(iy - jy), ny - np.abs(iy - jy))
        cx = np.minimum(np.abs(ix - jx), nx - np.abs(ix - jx))
        G_d = np.fft.irfft2(spec_psd, s=(ny, nx))[cy % ny, cx % nx]
        a2 = np.linalg.solve(G_d, y.ravel()).reshape(ny, nx)
        err = float(np.max(np.abs(a1 - a2)))
        ok = err < 1e-6 * float(np.max(np.abs(a2)))
        a3 = fit_dense(y, ny, nx, kf, lam=1e-3)
        gap = float(np.max(np.abs(a1 - a3)))
        # CG free-boundary check vs dense free solve
        obs = np.arange(ny * nx)
        a_cg, iters, conv, rel_res = cg_masked_solve(y.ravel(), ny, nx, kf, obs, lam=1e-3,
                                                  tol=1e-8, max_iter=4000)
        err_cg = float(np.max(np.abs(a_cg - a3)))
        print(f"{kname}: torus vs dense-torus err={err:.3e} {'PASS' if ok else 'FAIL'}"
              f" | torus-vs-free gap={gap:.3e}"
              f" | CG-free vs dense-free err={err_cg:.3e} iters={iters} conv={conv}")
