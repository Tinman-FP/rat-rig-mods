"""PTFE tubes and the head cable chain as elastic rods (vc12_elastica), for the checks and the assembly.

Tubes: one continuous PTFE tube per tool, from its filament source, down through the top hat into its coupler block on
the front top 3030 (directly above its dock), then free to the tool's push-fit. A 1.0 mm piano wire is taped along the
free length. The free length is the farthest the tool can go from its coupler (any bed position, its purge station, its
dock) plus TUBE['spare'].
Cable chain: a bought chain lying on its side (P.CHAIN), so it bends only in the horizontal plane at CHAIN_Z. It leaves
the mount on the left side wall toward +X and reaches the head's bracket travelling -X. Solved as a planar rod with no
in-plane weight; its length is the farthest head position plus CHAIN['spare'].
"""
import math
import numpy as np

import vc12_elastica as EL
import vc12_params as P

DOWN = np.array([0.0, 0.0, -1.0])
_T = math.radians(P.TUBE_TILT)
def inward(x):
    """+1 toward +X for the left tools, -1 for the right ones."""
    return 1.0 if x < 0 else -1.0


def cant(x):
    return math.radians(P.TUBE_CANT.get(P.DOCK_X.index(x), 0.0))


def tube_dir(x):
    c = cant(x)
    return np.array([inward(x) * math.sin(c) * math.cos(_T), math.cos(c) * math.cos(_T), -math.sin(_T)])
BED_X = (-255.0, -191.0, -128.0, -64.0, 0.0, 64.0, 128.0, 191.0, 255.0)
BED_Y = (-277.5, -250.0, -220.0, -180.0, -130.0, -35.0, 85.0, 207.0, P.YG_REAR_STOP + P.INDX_NOZZLE_DY)


def channel_points(x):
    """Tube centre line through the coupler block, top of the channel to the coupler boss face."""
    zs, r = P.TUBE_BEND
    h = np.array([inward(x) * math.sin(cant(x)), math.cos(cant(x)), 0.0])   # the bend turns toward this direction
    pts = [np.array([x, P.TUBE_IN_Y, zs + 12.0]), np.array([x, P.TUBE_IN_Y, zs])]
    for k in range(1, 7):
        a = math.radians(10.0 * k)
        pts.append(np.array([x, P.TUBE_IN_Y, zs]) + (r - r * math.cos(a)) * h + np.array([0.0, 0.0, -r * math.sin(a)]))
    pts.append(pts[-1] + 12.0 * tube_dir(x))
    return np.array(pts)


FEED_R = 60.0


def feed_points(x, y_end=-250.0):
    """Upstream of the block: from the top of its channel straight up through the lid and the deck's notch to
    P.FEED_TOP_Z, then over backward (R 60) and level to y_end (an outlet on the dryer's front)."""
    top = np.array([x, P.TUBE_IN_Y, P.FEED_TOP_Z])
    pts = [channel_points(x)[0] + np.array([0.0, 0.0, z]) for z in np.arange(0.0, P.FEED_TOP_Z - channel_points(x)[0][2], 15.0)]
    pts += [top + FEED_R * np.array([0.0, 1.0 - math.cos(a), math.sin(a)]) for a in np.radians(np.arange(0.0, 90.1, 10.0))]
    pts.append(np.array([x, y_end, P.FEED_TOP_Z + FEED_R]))
    return np.array(pts)


def tube_start(x):
    """Where the free tube leaves the coupler (A) and its direction."""
    return channel_points(x)[-1] + P.TUBE_FREE_FROM * tube_dir(x), tube_dir(x)


def tool_end(x, y_nozzle, parked):
    return np.array([x, y_nozzle, P.TOOL_INLET_Z[0 if parked else 1] + 12.0])   # 12 mm straight above the push-fit


def head_positions(x_own):
    """Nozzle (x, y) positions the tool reaches: the bed grid, its purge stroke and its dock."""
    i = P.DOCK_X.index(x_own)
    pts = [(x, y) for x in BED_X for y in BED_Y]
    pts += [(P.PURGE_X[i], P.PURGE_Y), (P.PURGE_X[i] + P.WIPE_X[1], P.PURGE_Y), (x_own, P.DOCK_NOZZLE_Y)]
    return pts


def chain_end(x, y_nozzle):
    return np.array([x + P.CHAIN_HEAD_D[0], y_nozzle + P.CHAIN_HEAD_D[1], P.CHAIN_Z])


CHAIN_A = np.array([P.CHAIN_MOUNT[0], P.CHAIN_MOUNT[1], P.CHAIN_Z])
CHAIN_TA = np.array([1.0, 0.0, 0.0])            # leaving the side mount into the machine
CHAIN_TB = np.array([-1.0, 0.0, 0.0])           # arriving at the head travelling -X (it leaves the head toward +X)


def rod_energy(X, ei, w):
    ds = float(np.linalg.norm(X[1] - X[0]))
    t = np.diff(X, axis=0) / ds
    D = np.diff(t, axis=0)
    return ei / (2.0 * ds) * float((D * D).sum()) + w * 9.81e-6 * ds * float(X[:, 2].sum())


def _length(A, ends, spare):
    return max(float(np.linalg.norm(e - A)) for e in ends) + spare


_LEN = {}


def tube_length(i):
    if i not in _LEN:
        x = P.DOCK_X[i]
        A, _ = tube_start(x)
        ends = [tool_end(hx, hy, False) for hx, hy in head_positions(x)] + [tool_end(x, P.DOCK_NOZZLE_Y, True)]
        _LEN[i] = _length(A, ends, P.TUBE["spare"])
    return _LEN[i]


def chain_length():
    if "chain" not in _LEN:
        ends = [chain_end(hx, hy) for x in P.DOCK_X for hx, hy in head_positions(x)]
        _LEN["chain"] = _length(CHAIN_A, ends, P.CHAIN["spare"])
    return _LEN["chain"]


def _solve(A, tA, B, tB, L, ei, w):
    """As the SV08 routing: a planar or symmetric start can stall, so retry from guesses bowed sideways."""
    X, ok = EL.solve(A, tA, B, tB, L, ei, w)
    for bow in ((30.0, 0.0, 0.0), (-30.0, 0.0, 0.0), (0.0, 30.0, 0.0), (0.0, -30.0, 0.0), (0.0, 0.0, 40.0),
                (40.0, 40.0, 20.0), (-40.0, 40.0, 20.0), (0.0, 80.0, 40.0)):
        if ok:
            break
        X0 = EL._initial(A, tA, B, tB, L, 36)
        X0[2:-2] += np.outer(np.sin(np.linspace(0.0, math.pi, len(X0) - 4)), bow)
        X, ok = EL.solve(A, tA, B, tB, L, ei, w, X0=X0)
    return X, ok


def tube_nodes(i, x_noz, y_noz, parked=False):
    A, tA = tube_start(P.DOCK_X[i])
    return _solve(A, tA, tool_end(x_noz, y_noz, parked), DOWN, tube_length(i), P.TUBE["ei"], P.TUBE["g_per_m"])


def parked_nodes(i):
    return tube_nodes(i, P.DOCK_X[i], P.DOCK_NOZZLE_Y, parked=True)


def chain_nodes(x_noz, y_noz):
    """Centreline of the cable chain (flat, at CHAIN_Z) with the head's nozzle at (x_noz, y_noz)."""
    return _solve(CHAIN_A, CHAIN_TA, chain_end(x_noz, y_noz), CHAIN_TB, chain_length(), P.CHAIN["ei"], 0.0)


def chain_links(X):
    """The chain as its links: one box per pitch along the centreline, 23.4 tall and 15 across (for the assembly)."""
    import Part
    from FreeCAD import Vector as V
    s = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(X, axis=0), axis=1))])
    pitch, t, h = P.CHAIN["pitch"], P.CHAIN["thick"], P.CHAIN["tall"]
    out = []
    for u in np.arange(pitch / 2, s[-1], pitch):
        c = np.array([np.interp(u, s, X[:, k]) for k in range(3)])
        a = np.array([np.interp(max(u - pitch / 2, 0), s, X[:, k]) for k in range(3)])
        b = np.array([np.interp(min(u + pitch / 2, s[-1]), s, X[:, k]) for k in range(3)])
        ang = float(np.degrees(np.arctan2(b[1] - a[1], b[0] - a[0])))
        bx = Part.makeBox(pitch - 0.6, t, h, V(-(pitch - 0.6) / 2, -t / 2, -h / 2))
        bx.rotate(V(0, 0, 0), V(0, 0, 1), ang)
        bx.translate(V(*c))
        out.append(bx)
    return Part.makeCompound(out)


def chain_section(X, step=4.0):
    """The chain as a solid for clash checks: a box per segment plus a post at each node, 15 across and 23.4 tall."""
    import Part
    from FreeCAD import Vector as V
    t, h = P.CHAIN["thick"], P.CHAIN["tall"]
    out = []
    for a, b in zip(X[:-1], X[1:]):
        L = float(np.linalg.norm(b - a))
        if L < 1e-6:
            continue
        bx = Part.makeBox(L, t, h, V(0, -t / 2, -h / 2))
        bx.rotate(V(0, 0, 0), V(0, 0, 1), float(np.degrees(np.arctan2(b[1] - a[1], b[0] - a[0]))))
        bx.translate(V(*a))
        out.append(bx)
        out.append(Part.makeCylinder(t / 2, h, V(b[0], b[1], b[2] - h / 2)))
    return Part.makeCompound(out)


def pipe(X, r):
    """One smooth solid tube through the nodes (for the assembly); falls back to cylinders and balls."""
    import Part
    from FreeCAD import Vector as V
    try:
        curve = Part.BSplineCurve()
        curve.interpolate([V(*p) for p in X])
        path = Part.Wire([curve.toShape()])
        t0 = curve.tangent(curve.FirstParameter)[0]
        ring = Part.Wire([Part.makeCircle(r, V(*X[0]), t0)])
        solid = path.makePipeShell([ring], True, True)
        if solid.isValid() and solid.Volume > 0:
            return solid
    except Exception:
        pass
    parts = []
    for a, b in zip(X[:-1], X[1:]):
        d = b - a
        L = float(np.linalg.norm(d))
        if L > 1e-6:
            parts.append(Part.makeCylinder(r, L, V(*a), V(*(d / L))))
    for p in X[1:-1]:
        parts.append(Part.makeSphere(r, V(*p)))
    return Part.makeCompound(parts)


if __name__ == "__main__":
    for i in range(P.INDX_TOOLS):
        X, ok = parked_nodes(i)
        print(f"T{i}: free tube {tube_length(i):.0f} mm; parked shape top Z {X[:, 2].max():.0f}, lowest Z "
              f"{X[2:-4, 2].min():.0f}, reaches back to Y {X[:, 1].max():.0f}, solved {ok}")
    print(f"cable chain length {chain_length():.0f} mm")
