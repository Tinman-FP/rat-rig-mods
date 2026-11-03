"""Shape of a tube or cable bundle stiffened by a piano wire: a discrete elastic rod of fixed length with both end
tangents clamped, under its own weight. Solved by minimising bending + gravity energy with SLSQP, segment lengths held
equal. Units mm and N; z is up. Plain numpy/scipy, so it runs in FreeCAD's Python and in the system Python.

Taken unchanged from the owner's SV08 Max INDX project (Tinman-FP/sovol-sv08-max, c3-4040-gantry/c3_elastica.py).
The shapes are what a uniform rod settles into with nothing else touching it: treat them as the nominal path, the way
the Rat Rig umbilical is set by hand on the machine.
"""
import numpy as np
from scipy.optimize import minimize

G = 9.81e-3                                   # N per g

def _bezier(A, tA, B, tB, h, n=400):
    P0, P3 = np.asarray(A, float), np.asarray(B, float)
    P1, P2 = P0 + h * np.asarray(tA, float), P3 - h * np.asarray(tB, float)
    t = np.linspace(0.0, 1.0, n)[:, None]
    return (1 - t) ** 3 * P0 + 3 * (1 - t) ** 2 * t * P1 + 3 * (1 - t) * t ** 2 * P2 + t ** 3 * P3

def _length(P):
    return float(np.linalg.norm(np.diff(P, axis=0), axis=1).sum())

def _resample(P, N):
    s = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    u = np.linspace(0.0, s[-1], N + 1)
    return np.stack([np.interp(u, s, P[:, k]) for k in range(3)], axis=1)

def _initial(A, tA, B, tB, L, N):
    lo, hi = 1.0, 4.0 * L
    for _ in range(60):                         # handle length so the Bezier is as long as the rod
        h = 0.5 * (lo + hi)
        lo, hi = (h, hi) if _length(_bezier(A, tA, B, tB, h)) < L else (lo, h)
    return _resample(_bezier(A, tA, B, tB, 0.5 * (lo + hi)), N)

def solve(A, tA, B, tB, L, EI, w_g_per_m, N=36, X0=None):
    """Nodes (N+1, 3) of a rod of length L from A (leaving along tA) to B (arriving along tB).
    EI in N mm2, weight in g/m. Returns (nodes, ok)."""
    A, B = np.asarray(A, float), np.asarray(B, float)
    tA = np.asarray(tA, float) / np.linalg.norm(tA); tB = np.asarray(tB, float) / np.linalg.norm(tB)
    ds = L / N
    if L < np.linalg.norm(B - A) + 2 * ds:
        raise ValueError(f'rod too short: {L:.0f} mm for a {np.linalg.norm(B - A):.0f} mm chord')
    X = _initial(A, tA, B, tB, L, N) if X0 is None else np.asarray(X0, float).copy()
    X[0], X[1], X[-1], X[-2] = A, A + ds * tA, B, B - ds * tB
    free = slice(2, N - 1)
    c, wn = EI / (2.0 * ds), w_g_per_m * G / 1000.0 * ds          # bending factor, weight per node (N)

    def full(v):
        Y = X.copy(); Y[free] = v.reshape(-1, 3); return Y

    def energy(v):
        Y = full(v); t = np.diff(Y, axis=0) / ds; D = np.diff(t, axis=0)
        E = c * float((D * D).sum()) + wn * float(Y[free, 2].sum())
        g = np.zeros_like(Y)                                       # dE/dY via D_i = (Y_i - 2Y_i+1 + Y_i+2) / ds
        k = 2.0 * c / ds
        g[:-2] += k * D; g[1:-1] -= 2.0 * k * D; g[2:] += k * D
        g[:, 2] += wn
        return E, g[free].ravel()

    def cons(v):
        Y = full(v); d = np.diff(Y, axis=0)
        return (d * d).sum(axis=1)[1:-1] - ds * ds                 # segments 0 and N-1 are fixed by the clamps

    def cons_jac(v):
        Y = full(v); d = np.diff(Y, axis=0); n = len(v) // 3
        J = np.zeros((N - 2, len(v)))
        for i in range(1, N - 1):                                  # segment i joins nodes i and i+1
            r = i - 1
            if 2 <= i <= N - 2:
                J[r, 3 * (i - 2):3 * (i - 2) + 3] = -2.0 * d[i]
            if 2 <= i + 1 <= N - 2:
                J[r, 3 * (i - 1):3 * (i - 1) + 3] = 2.0 * d[i]
        return J

    res = minimize(energy, X[free].ravel(), jac=True, method='SLSQP',
                   constraints=[{'type': 'eq', 'fun': cons, 'jac': cons_jac}], options={'maxiter': 600, 'ftol': 1e-9})
    Y = full(res.x)
    err = float(np.abs(np.linalg.norm(np.diff(Y, axis=0), axis=1) - ds).max())
    # With both ends on one vertical line and both tangents vertical, the loop can turn freely about that line: SLSQP
    # keeps rolling it and stops at its iteration limit, though every turned copy is the same equilibrium.
    spin = res.status == 9 and np.linalg.norm((B - A)[:2]) < 5.0 and abs(tA[2]) > 0.99 and abs(tB[2]) > 0.99
    return Y, bool((res.success or spin) and err < 0.02 * ds)
