"""Route check for the PTFE tubes and the head umbilical (run with FreeCAD's Python after vc12_build.py).

  VC12_CONTEXT=<stock_context.brep> VC12_INDX=<INDX FCStd>
  /Applications/FreeCAD.app/Contents/Resources/bin/python vc12_routecheck.py

For each tool on the head in turn, at every bed position of a 9 x 9 grid (front clearance line to the rear stop), its
purge spot, the end of its wipe and its own dock: the active tube and the umbilical are solved as elastic rods
(vc12_tubes) and checked against the moving gantry (head, saddle, carriage, beam, joints) and the fixed parts (docks
and parked tools, rails, coupler blocks, frame, top 3030s and the top hat). The four parked tubes are checked against
the same at every pose. Each line's first and last 15 mm (its clamp and its tool or saddle) are left out.
Reported, not counted as clashes: the gap from the umbilical to every parked tube (it must stay clear of them) and to
every tube's feed (straight up from its block to the lid), the gap from the free tubes to the other tools' feeds, and
tube-on-tube gaps (free tubes may touch, as on any multi-tool printer). Writes checks/route_report.json.
"""
import json
import os
import sys
import time

sys.path.append("/Applications/FreeCAD.app/Contents/Resources/lib")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import FreeCAD as App  # noqa: E402
import numpy as np  # noqa: E402
import Part  # noqa: E402
from FreeCAD import Vector as V  # noqa: E402

import vc12_check as K  # noqa: E402
import vc12_params as P  # noqa: E402
import vc12_tubes as T  # noqa: E402
from vc12_build import box  # noqa: E402

TOL = 0.2
T0 = time.time()


def resample(X, step=3.0):
    s = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(X, axis=0), axis=1))])
    u = np.arange(0.0, s[-1] + 1e-9, step)
    return np.stack([np.interp(u, s, X[:, k]) for k in range(3)], axis=1)


def trimmed(X):
    return resample(X)[5:-5]


def line_hits(Q, r, items):
    """Tube of radius r along points Q against (name, shape, bbox) items, 10 segments at a time."""
    out = {}
    segs = [(a, b) for a, b in zip(Q[:-1], Q[1:]) if np.linalg.norm(b - a) > 1e-6]
    for i in range(0, len(segs), 10):
        ch = segs[i:i + 10]
        pts = np.array([p for ab in ch for p in ab])
        lo, hi = pts.min(axis=0) - r, pts.max(axis=0) + r
        bb = App.BoundBox(*lo, *hi)
        cands = [(n, s) for n, s, sb in items if n not in out and bb.intersect(sb)]
        if not cands:
            continue
        sol = Part.makeCompound([Part.makeCylinder(r, float(np.linalg.norm(b - a)), V(*a), V(*(b - a))) for a, b in ch])
        for n, s in cands:
            try:
                v = sol.common(s).Volume
            except Exception:
                v = -1.0
            if v > TOL or v < 0:
                out[n] = round(v, 2)
    return out


def gap(A, B, ra, rb):
    d = A[:, None, :] - B[None, :, :]
    return float(np.sqrt((d * d).sum(-1)).min()) - ra - rb


def frame_top_and_hat():
    """Top 3030s from the frame drawing, and the owner's top hat as boxes: 50 mm walls (their inner faces on the real
    hat's centre walls and 5 mm inside its 40 mm corner walls, vc12_hat.py) and the lid in its pocket."""
    z0, z1 = P.TOP_FRONT_Z
    f = {"frame top 3030 front": box(-370, 370, -367.5, -337.5, z0, z1),
         "frame top 3030 rear": box(-370, 370, 337.5, 367.5, z0, z1),
         "frame top 3030 left": box(-400, -370, -337.5, 337.5, z0, z1),
         "frame top 3030 right": box(370, 400, -337.5, 337.5, z0, z1)}
    h = {"top hat lid": box(-415, 415, -382, 382, P.HAT_LID_Z, P.HAT_LID_Z + 4),
         "top hat wall rear": box(-415, 415, 331.7, 381.7, z1, P.HAT_LID_Z),
         "top hat wall left": box(-414.6, -364.6, -381.7, 381.7, z1, P.HAT_LID_Z),
         "top hat wall right": box(364.6, 414.6, -381.7, 381.7, z1, P.HAT_LID_Z),
         "top hat wall front": box(-415, 415, -381.7, -331.7, z1, P.HAT_LID_Z)}
    return f, h


def main():
    indx = K.indx_shapes()
    ctx = K.load_context()
    fixed = K.fixed_parts(indx)
    for i in range(P.INDX_TOOLS):
        s = Part.Shape()
        s.read(os.path.join(K.PARTS, f"ptfe_coupler_block_T{i}.brep"))
        fixed[f"ptfe_coupler_block_T{i}"] = s
    ftop, hat = frame_top_and_hat()
    fixed.update(ftop)
    fixed.update(hat)
    fixed.update({n: s for n, s in zip(K.CTX_NAMES, ctx)})
    fixed_items = [(n, s, s.BoundBox) for n, s in fixed.items() if s.BoundBox.ZMax > 760.0]   # tubes stay above 800
    saddle = Part.Shape()
    saddle.read(os.path.join(K.PARTS, "umbilical_saddle.brep"))

    rep = {"note": __doc__.split("\n")[0], "tube_free_length_mm": {}, "umbilical_free_length_mm": round(T.umb_length()),
           "parked": {}, "clashes": [], "not_converged": [], "umbilical_to_parked_min_gap": None,
           "umbilical_to_active_min_gap": None, "tube_contacts": 0, "tube_min_gap": None, "extremes": {}}
    parked = {}
    for i in range(P.INDX_TOOLS):
        X, ok = T.parked_nodes(i)
        parked[i] = X
        rep["tube_free_length_mm"][f"T{i}"] = round(T.tube_length(i))
        rep["parked"][f"T{i}"] = dict(top=round(float(X[:, 2].max()), 1), lowest=round(float(X[2:-4, 2].min()), 1),
                                      back_to_y=round(float(X[:, 1].max()), 1), solved=ok)
        if not ok:
            rep["not_converged"].append(f"parked T{i}")
        for n, v in line_hits(trimmed(X), P.TUBE["od"] / 2 + 0.5, [it for it in fixed_items if it[0] not in
                                                                    (f"ptfe_coupler_block_T{i}", f"parked_T{i}")]).items():
            rep["clashes"].append(dict(line=f"parked T{i}", pose="any", part=n, vol=v))
    feeds = {i: resample(T.feed_points(x))[1:] for i, x in enumerate(P.DOCK_X)}      # in the chamber: block to lid
    feeds = {i: F[F[:, 2] <= P.HAT_LID_Z + 4.0] for i, F in feeds.items()}
    r_t = P.TUBE["od"] / 2 + 0.5
    rep["parked_to_other_feeds_min_gap"] = round(min(gap(trimmed(parked[j]), feeds[k], r_t, P.TUBE["od"] / 2)
                                                     for j in parked for k in feeds if k != j), 1)
    print("parked tubes done", round(time.time() - T0), "s", flush=True)

    umb_cache, worst_up, worst_ua, tube_gaps, ext = {}, [], [], [], dict(active_low=1e9, active_top=-1e9, umb_low=1e9, umb_top=-1e9)
    worst_uf, worst_af = [], []
    for i in range(P.INDX_TOOLS):
        for hx, hy in T.head_positions(P.DOCK_X[i]):
            yg = hy - P.INDX_NOZZLE_DY
            mov = K.moving_parts(hx, yg, indx)
            sad = saddle.copy()
            sad.translate(V(hx, yg, 0))
            moving_items = [(n, s, s.BoundBox) for n, s in list(mov.items()) + [("umbilical_saddle", sad)]
                            if not n.startswith("belt_") and s.BoundBox.ZMax > 760.0]
            Xa, oka = T.tube_nodes(i, hx, hy)
            key = (round(hx, 1), round(hy, 1))
            if key not in umb_cache:
                umb_cache[key] = T.umb_nodes(hx, hy)
            Xu, oku = umb_cache[key]
            pose = dict(tool=f"T{i}", x=hx, y=hy)
            for nm, ok in (("active", oka), ("umbilical", oku)):
                if not ok:
                    rep["not_converged"].append(dict(line=nm, **pose))
            Qa, Qu = trimmed(Xa), trimmed(Xu)
            ext["active_low"] = min(ext["active_low"], float(Qa[:, 2].min()))
            ext["active_top"] = max(ext["active_top"], float(Xa[:, 2].max()))
            ext["umb_low"] = min(ext["umb_low"], float(Qu[:, 2].min()))
            ext["umb_top"] = max(ext["umb_top"], float(Xu[:, 2].max()))
            skip_a = (f"ptfe_coupler_block_T{i}", f"dock_T{i}", f"parked_T{i}", "indx_held_tool")
            for n, v in line_hits(Qa, P.TUBE["od"] / 2 + 0.5, [it for it in moving_items + fixed_items if it[0] not in skip_a]).items():
                rep["clashes"].append(dict(line="active tube", **pose, part=n, vol=v))
            if key not in rep.setdefault("_umb_done", []):
                rep["_umb_done"].append(key)
                for n, v in line_hits(Qu, P.UMB["od"] / 2, [it for it in moving_items + fixed_items
                                                            if it[0] not in ("umbilical_saddle", "umbilical_swivel")]).items():
                    rep["clashes"].append(dict(line="umbilical", **pose, part=n, vol=v))
            for j in range(P.INDX_TOOLS):                         # parked tubes against the head at this pose
                if j == i:
                    continue
                for n, v in line_hits(trimmed(parked[j]), P.TUBE["od"] / 2 + 0.5, moving_items).items():
                    rep["clashes"].append(dict(line=f"parked T{j}", **pose, part=n, vol=v))
                g = gap(Qu, trimmed(parked[j]), P.UMB["od"] / 2, P.TUBE["od"] / 2 + 0.5)
                worst_up.append((round(g, 1), f"T{j}", pose))
                tg = gap(Qa, trimmed(parked[j]), P.TUBE["od"] / 2 + 0.5, P.TUBE["od"] / 2 + 0.5)
                tube_gaps.append(tg)
            worst_ua.append((round(gap(Qu[:-8], Qa[:-8], P.UMB["od"] / 2, P.TUBE["od"] / 2 + 0.5), 1), pose))
            for k, F in feeds.items():                         # the feeds: straight up from each block to the lid
                worst_uf.append((round(gap(Qu, F, P.UMB["od"] / 2, P.TUBE["od"] / 2), 1), f"T{k}", pose))
                if k != i:
                    worst_af.append((round(gap(Qa, F, r_t, P.TUBE["od"] / 2), 1), f"T{k}", pose))
        print(f"T{i} active done, clashes so far {len(rep['clashes'])}, {round(time.time() - T0)} s", flush=True)
    rep.pop("_umb_done", None)
    worst_up.sort(key=lambda w: w[0])
    worst_ua.sort(key=lambda w: w[0])
    rep["umbilical_to_parked_min_gap"] = dict(mm=worst_up[0][0], worst=[dict(gap=g, parked=t, **p) for g, t, p in worst_up[:6]])
    rep["umbilical_to_active_min_gap"] = dict(mm=worst_ua[0][0], worst=[dict(gap=g, **p) for g, p in worst_ua[:6]])
    worst_uf.sort(key=lambda w: w[0])
    worst_af.sort(key=lambda w: w[0])
    rep["umbilical_to_feeds_min_gap"] = dict(mm=worst_uf[0][0], worst=[dict(gap=g, feed=t, **p) for g, t, p in worst_uf[:6]])
    rep["active_to_other_feeds_min_gap"] = dict(mm=worst_af[0][0], worst=[dict(gap=g, feed=t, **p) for g, t, p in worst_af[:6]])
    rep["tube_contacts"] = sum(1 for g in tube_gaps if g < 0)
    rep["tube_min_gap"] = round(min(tube_gaps), 1)
    rep["extremes"] = {k: round(v, 1) for k, v in ext.items()}
    rep["head_top_z"] = 840.5
    rep["saddle_top_z"] = round(saddle.BoundBox.ZMax, 1)
    out = os.path.join(HERE, "..", "checks", "route_report.json")
    json.dump(rep, open(out, "w"), indent=1)
    print(json.dumps({k: rep[k] for k in ("tube_free_length_mm", "umbilical_free_length_mm", "parked", "extremes",
                                          "umbilical_to_parked_min_gap", "umbilical_to_active_min_gap",
                                          "umbilical_to_feeds_min_gap", "active_to_other_feeds_min_gap",
                                          "parked_to_other_feeds_min_gap", "tube_contacts",
                                          "tube_min_gap", "not_converged")}, indent=1)[:4000])
    print("clashes:", len(rep["clashes"]), rep["clashes"][:10])


if __name__ == "__main__":
    main()
