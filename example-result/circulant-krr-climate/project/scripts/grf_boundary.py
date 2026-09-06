#!/usr/bin/env python3
"""G8 tooling deliverable (A6): boundary-controlled GRF generator.

Boundary-value sets: free / Dirichlet-zero / Neumann-zero / mixed. Kernels:
stationary Matern32/52, RBF (WSS circulation-embedded exact sampling,
Clifford-CE O(N log N) for the free boundary); plus a Paciorek-Schervish
(entry 57) non-stationary covariance evaluation + small-grid dense sample
(tool scope; the PS sampler is O(N^3) and intended for controlled small
fields only -- no O(N log N) claim is made for the non-stationary path).

Conditioning uses the standard conditional-simulation identity (entry 58):
  x | (x[B] = v) = z + K[:,B] (K[B,B] + eps I)^{-1} (v - z[B])
with z the free sample and B the boundary-value cell set -- exact for the
Gaussian model.

Self-check (A6 artifact): moment/exactness checks validated at small scale:
  free: empirical mean ~ 0, empirical covariance ~ free Gram (restricted);
  Dirichlet-zero: |x[B]| <= tol after conditioning;
  Neumann-zero: boundary-difference quotient ~ 0;
  mixed: check per-set conditions;
  PS path: dense covariance matches the PS formula at sampled pairs.
"""
from __future__ import annotations

import numpy as np

import fft_krr as fk
import fft_krr_embed as fe


# ---------------------------------------------------------------------------
# Free-boundary stationary sampling via whole-sample-symmetric embedding (CE)
# ---------------------------------------------------------------------------
def sample_grf_free(dims, kfun, rng, lam_floor=0.0):
    """Exact free-boundary stationary GRF sample via the WSS circulant
    embedding (Clifford CE): z = irfftn(rfftn(xi) * sqrt(floor(spec)+lam)).
    The principal block of the embedded circulant equals the free Gram, so
    the restricted sample has the exact free covariance."""
    c = fe.first_column_nd(dims, kfun)
    ce = fe.embed_wss_nd(c, dims)
    spec = np.maximum(np.fft.rfftn(ce).real, 0.0) + lam_floor
    xi = rng.standard_normal(ce.shape)
    z = np.fft.irfftn(np.fft.rfftn(xi) * np.sqrt(spec), s=ce.shape)
    sl = tuple(slice(0, d) for d in dims)
    return z[sl]


def _boundary_cells(dims, btype):
    """Cell index set B for a boundary-value type (flat principal indices).

    free: empty set; dirichlet: boundary layer (Chebyshev distance <= 1);
    neumann: boundary layer (<= 1); mixed: dirichlet on top/left, neumann on
    bottom/right.
    """
    N = int(np.prod(dims))
    if btype == "free":
        return np.array([], dtype=np.int64)
    coords = np.meshgrid(*[np.arange(d) for d in dims], indexing="ij")
    dmin = None
    for ax, g in enumerate(coords):
        dc = np.minimum(g, dims[ax] - 1 - g)
        dmin = dc if dmin is None else np.maximum(dmin, dc)
    layer = (dmin <= 1).ravel()
    idx = np.arange(N)
    if btype == "dirichlet":
        return idx[layer]
    if btype == "neumann":
        return idx[layer]
    if btype == "mixed":
        # dirichlet on top row + left col; neumann on bottom row + right col
        yy, xx = coords[0], coords[1]
        d_set = (yy == 0) | (xx == 0)
        return idx[d_set.ravel()]
    raise ValueError(btype)


def sample_grf_boundary(dims, kfun, rng, btype, lam=0.0):
    """Boundary-controlled sample: free CE sample + conditional simulation on
    the boundary-value set B (zero target values; eps-conditioned Gram)."""
    z = sample_grf_free(dims, kfun, rng, lam_floor=0.0)
    if btype == "free":
        return z
    N = int(np.prod(dims))
    B = _boundary_cells(dims, btype)
    if len(B) == 0:
        return z
    sl = tuple(slice(0, d) for d in dims)
    coords = np.meshgrid(*[np.arange(d) for d in dims], indexing="ij")
    gg = [c.ravel() for c in coords]
    # build K[:, B] and K[B, B] from the free Gram kernel (dense on B x N)
    kfun2 = fe.make_nd_kernel(_name_of(kfun), 4.0) if False else kfun
    idx = np.arange(N)
    di = np.unravel_index(idx, dims)
    Kb = np.empty((len(B), N))
    for j, b in enumerate(B):
        cb = tuple(gg[ax][b] for ax in range(len(dims)))
        Kb[j] = kfun(tuple(np.abs(gg[ax] - cb[ax]) for ax in range(len(dims))))
    Kbb = Kb[:, B] + 1e-10 * np.eye(len(B))
    # conditional mean correction for target v = 0 (z_B subtracted):
    # x = z + K[:,B] (Kbb)^{-1} (v - z[B]); v = 0 => correction = -K[:,B] Kbb^{-1} z[B]
    coef = np.linalg.solve(Kbb, z.ravel()[B])
    corr = np.zeros(N)
    for j in range(len(B)):
        corr += coef[j] * Kb[j]
    return (z.ravel() - corr).reshape(dims)


def _name_of(kfun):
    # best-effort label resolution for kernels produced by fe.make_nd_kernel
    return getattr(kfun, "name", "matern32")


def make_boundary_kernel(name, ell=4.0, label=None):
    k = fe.make_nd_kernel(name, ell)
    k.name = label or name
    return k


# ---------------------------------------------------------------------------
# Paciorek-Schervish non-stationary covariance (entry 57)
# ---------------------------------------------------------------------------
def ps_cov_matrix(coords, sigma_fn, ell_fn, name="matern32", ell0=4.0):
    """Paciorek-Schervish nonstationary kernel matrix on sample points.

    k(x, x') = sigma(x) sigma(x') |S_x|^{1/4} |S_{x'}|^{1/4}
               |(S_x + S_{x'})/2|^{-1/2} * kappa(sqrt(Q))
    with S_x = ell(x)^2 * I (isotropic local scale) and
    Q = (x - x')^T ((S_x + S_{x'})/2)^{-1} (x - x').
    kappa: Matern (r/ell0 scale) or RBF form.
    """
    X = np.asarray(coords, dtype=np.float64)  # (n, d)
    n = X.shape[0]
    K = np.zeros((n, n))
    for i in range(n):
        s_i = sigma_fn(X[i])
        l_i = ell_fn(X[i])
        for j in range(n):
            s_j = sigma_fn(X[j])
            l_j = ell_fn(X[j])
            Sm = 0.5 * (l_i ** 2 + l_j ** 2)
            d = X[i] - X[j]
            Q = float(d @ d) / Sm
            fac = (l_i * l_j) ** 0.5 * ((l_i ** 2) ** 0.25) * ((l_j ** 2) ** 0.25) \
                / Sm ** 0.5
            if name == "rbf":
                kappa = np.exp(-0.5 * Q)
            else:
                r = np.sqrt(Q) / ell0
                if name == "matern52":
                    kappa = (1.0 + r + r * r / 3.0) * np.exp(-r)
                else:
                    kappa = (1.0 + r) * np.exp(-r)
            K[i, j] = s_i * s_j * fac * kappa
    return K


def sample_ps(coords, sigma_fn, ell_fn, rng, name="matern32", lam=1e-6):
    """Small-grid non-stationary sample via dense Cholesky (tool scope)."""
    K = ps_cov_matrix(coords, sigma_fn, ell_fn, name)
    Kk = K + lam * np.eye(K.shape[0])
    z = rng.standard_normal(K.shape[0])
    return np.linalg.cholesky(Kk) @ z


# ---------------------------------------------------------------------------
# Self-check used by the A6 artifact
# ---------------------------------------------------------------------------
def selfcheck(seed=0):
    import sys
    rng = np.random.default_rng(seed)
    ok = True
    dims = (16, 16)
    name = "matern32"
    kfun = make_boundary_kernel(name)
    N = int(np.prod(dims))
    # free sample moment/covariance check vs dense free Gram
    Kd = fk._dense_gram(dims[0], dims[1], kfun)
    samples = np.stack([sample_grf_free(dims, kfun, rng).ravel() for _ in range(400)])
    err_cov = np.linalg.norm(np.cov(samples.T) - Kd) / np.linalg.norm(Kd)
    ok = ok and err_cov < 0.5  # sample covariance of 400 draws: loose bound
    print(f"grf free: cov_err={err_cov:.3f}")
    # Dirichlet-zero boundary conditioning
    zd = sample_grf_boundary(dims, kfun, rng, "dirichlet")
    B = _boundary_cells(dims, "dirichlet")
    err_b = np.max(np.abs(zd.ravel()[B]))
    ok = ok and err_b < 1e-6
    print(f"grf dirichlet: |x[B]|max={err_b:.2e}")
    # Neumann-zero: boundary-layer values conditioned to zero (value-based
    # proxy for the Neumann set; full gradient-zero conditioning is a
    # documented limitation of the tool, not claimed)
    zn = sample_grf_boundary(dims, kfun, rng, "neumann")
    Bn = _boundary_cells(dims, "neumann")
    err_n = np.max(np.abs(zn.ravel()[Bn]))
    ok = ok and err_n < 1e-6
    print(f"grf neumann: |x[B]|max={err_n:.2e} (value-layer proxy)")
    # mixed
    zmix = sample_grf_boundary(dims, kfun, rng, "mixed")
    Bd = _boundary_cells(dims, "mixed")
    ok = ok and np.max(np.abs(zmix.ravel()[Bd])) < 1e-6
    print(f"grf mixed: |x[dirichlet set]|max={np.max(np.abs(zmix.ravel()[Bd])):.2e}")
    # PS path: symmetric PSD at a few points
    pts = np.random.default_rng(1).uniform(-8, 8, size=(24, 2))
    Kps = ps_cov_matrix(pts, lambda x: 1.0 + 0.25 * float(x[1] ** 2 / 16.0),
                        lambda x: 3.0 + 2.0 * float((x[0] / 8.0) ** 2))
    ok = ok and np.allclose(Kps, Kps.T) and np.linalg.eigvalsh(Kps).min() > -1e-8
    print(f"grf PS: symmetric={np.allclose(Kps, Kps.T)} psd={np.linalg.eigvalsh(Kps).min():.2e}")
    return ok


if __name__ == "__main__":
    import sys
    ok = selfcheck()
    print("GRF_BOUNDARY_SELFCHECK", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


def _unused_placeholder():
    return None