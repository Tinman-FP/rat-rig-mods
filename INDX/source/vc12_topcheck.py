"""Spool deck check (run with FreeCAD's Python after vc12_build.py).

  VC12_HAT=<Rat Rig Top Hat Modular.step>
  /Applications/FreeCAD.app/Contents/Resources/bin/python vc12_topcheck.py

Against the owner's top hat (vc12_hat.py), the lid filling its pocket up to P.LID_TOP_Z with two handles on it,
the top 3030s and the coupler blocks: the four deck feet (seated on the rim, clear of the lid), the plywood deck, and
each tube's feed from the top of its block's channel up through its lid hole and the deck's notch to the dryer. Also
the coupler blocks against the hat, the lid hole positions, the load on each foot and the deck's sag. Writes
checks/top_report.json.
"""
import json
import os
import sys

sys.path.append("/Applications/FreeCAD.app/Contents/Resources/lib")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import FreeCAD as App  # noqa: E402,F401
import numpy as np  # noqa: E402
import Part  # noqa: E402
from FreeCAD import Vector as V  # noqa: E402

import vc12_hat as H  # noqa: E402
import vc12_params as P  # noqa: E402
import vc12_tubes as T  # noqa: E402
from vc12_build import box, cyl_z, minus  # noqa: E402

PARTS = os.path.join(HERE, "..", "parts")
CORNERS = ("FR", "FL", "RR", "RL")
LID_HOLE = 6.0
PLY_DENSITY = 680.0            # kg/m3, birch plywood
PLY_E = 8000.0                 # N/mm2, along the face grain (lower bound for birch ply)
DRYER_KG = 12.25               # Sunlu S4 (4.8 kg) and S2 (1.2 kg) with five 1 kg spools (1.25 kg each)


def load(name):
    s = Part.Shape()
    s.read(os.path.join(PARTS, name + ".brep"))
    return s


def lid():
    """The lid and its foam gasket filling the hat's pocket up to P.LID_TOP_Z, with a hole straight above each block's
    channel."""
    px, py = P.HAT_POCKET
    plate = box(-px, px, -py, py, P.HAT_LID_Z, P.LID_TOP_Z)
    return minus(plate, [cyl_z(x, P.TUBE_IN_Y, LID_HOLE, P.HAT_LID_Z - 1, P.LID_TOP_Z + 1) for x in P.DOCK_X])


def handles():
    """The lid's two handles, at its left and right edges where Rat Rig fits the stock ones."""
    z = P.LID_TOP_Z
    return Part.makeCompound([box(sx * 354.0, sx * 371.0, -59.0, 59.0, z, P.LID_HANDLE_TOP) if sx > 0 else
                              box(-371.0, -354.0, -59.0, 59.0, z, P.LID_HANDLE_TOP) for sx in (1, -1)])


def deck():
    hx, hy = P.DECK_HALF
    x0, x1, yb = P.DECK_NOTCH
    d = box(-hx, hx, -hy, hy, P.DECK_Z, P.DECK_Z + P.DECK_T)
    return minus(d, [box(x0, x1, -hy - 1.0, yb, P.DECK_Z - 1.0, P.DECK_Z + P.DECK_T + 1.0)])


def frame_top():
    z0, z1 = P.TOP_FRONT_Z
    return Part.makeCompound([box(-370, 370, -367.5, -337.5, z0, z1), box(-370, 370, 337.5, 367.5, z0, z1),
                              box(-400, -370, -367.5, 367.5, z0, z1), box(370, 400, -367.5, 367.5, z0, z1)])


def tube(X, r):
    return Part.makeCompound([Part.makeCylinder(r, float(np.linalg.norm(b - a)), V(*a), V(*(b - a)))
                              for a, b in zip(X[:-1], X[1:]) if np.linalg.norm(b - a) > 1e-6])


def dist(a, b):
    return round(a.distToShape(b)[0], 2)


def overlap(a, b):
    return round(sum(a.common(s).Volume for s in b.Solids if s.BoundBox.intersect(a.BoundBox)), 3)


def main():
    hat = H.hat()
    L, hd, dk, ft = lid(), handles(), deck(), frame_top()
    feet = {c: load(f"deck_foot_{c}") for c in CORNERS}
    blocks = [load(f"ptfe_coupler_block_T{i}") for i in range(P.INDX_TOOLS)]
    rep = {"note": __doc__.split("\n")[0], "hat": "owner's hat as it sits (vc12_hat.py)",
           "from_owner": {"lid_top_above_rim_mm": round(P.LID_TOP_Z - P.HAT_RIM_Z, 2),
                                      "handle_height_mm": round(P.LID_HANDLE_TOP - P.LID_TOP_Z, 2)},
           "feet": {}, "feeds": {},
           "blocks_to_hat_mm": {}}

    for c, f in feet.items():
        bottom = [x for x in f.Faces if x.Surface.TypeId == "Part::GeomPlane" and abs(x.BoundBox.ZMax - P.HAT_RIM_Z) < 1e-3
                  and abs(x.BoundBox.ZMin - P.HAT_RIM_Z) < 1e-3 and x.normalAt(0, 0).z < -0.999]
        rep["feet"][c] = dict(overlap_with_hat_mm3=overlap(f, hat), seated_on_rim_gap_mm=dist(f, hat),
                              bearing_area_mm2=round(sum(x.Area for x in bottom)), to_lid_mm=dist(f, L),
                              to_handles_mm=dist(f, hd), to_frame_mm=dist(f, ft))
    rep["deck"] = dict(size_mm=[2 * P.DECK_HALF[0], 2 * P.DECK_HALF[1], P.DECK_T],
                       notch_mm=[P.DECK_NOTCH[1] - P.DECK_NOTCH[0], P.DECK_NOTCH[2] + P.DECK_HALF[1]],
                       to_handles_mm=dist(dk, hd), to_lid_mm=dist(dk, L), to_hat_mm=dist(dk, hat),
                       overlap_with_feet_mm3=sum(overlap(dk, f) for f in feet.values()),
                       on_feet_gap_mm=min(dist(dk, f) for f in feet.values()))

    for i, x in enumerate(P.DOCK_X):
        X = T.feed_points(x)
        Q = X[1:]                                            # past the channel's mouth (its first 15 mm)
        tb = tube(Q, P.TUBE["od"] / 2)
        others = Part.makeCompound([b for j, b in enumerate(blocks) if j != i])
        rep["feeds"][f"T{i}"] = dict(
            to_hat_mm=dist(tb, hat), to_lid_mm=dist(tb, L), to_deck_mm=dist(tb, dk),
            to_feet_mm=min(dist(tb, f) for f in feet.values()), to_handles_mm=dist(tb, hd), to_frame_top_mm=dist(tb, ft),
            to_other_blocks_mm=dist(tb, others), to_own_block_mm=dist(tb, blocks[i]),
            lid_hole_from_lid_left_edge_mm=round(x + P.HAT_POCKET[0], 1),
            lid_hole_from_lid_front_edge_mm=round(P.TUBE_IN_Y + P.HAT_POCKET[1], 1),
            straight_up_mm=round(P.FEED_TOP_Z - X[0][2], 1))
        rep["blocks_to_hat_mm"][f"T{i}"] = dist(blocks[i], hat)

    hx, hy = P.DECK_HALF
    ply_kg = (2 * hx * 2 * hy - (P.DECK_NOTCH[1] - P.DECK_NOTCH[0]) * (P.DECK_NOTCH[2] + hy)) * P.DECK_T * 1e-9 * PLY_DENSITY
    feet_kg = sum(f.Volume for f in feet.values()) * 1.30e-6
    total_n = (ply_kg + feet_kg + DRYER_KG) * 9.81
    worst_area = min(v["bearing_area_mm2"] for v in rep["feet"].values())
    # plate on four corner points: centre sag 0.025 q a^4 / D for an even load; doubled for a dryer that sits
    # mostly in the middle (its own footprint, not a point)
    a = 2 * min(hx, hy)
    D = PLY_E * P.DECK_T ** 3 / (12 * (1 - 0.3 ** 2))
    q = (DRYER_KG + ply_kg) * 9.81 / (2 * hx * 2 * hy)
    rep["load"] = dict(deck_kg=round(ply_kg, 1), feet_kg=round(feet_kg, 2), dryer_allowance_kg=DRYER_KG,
                       per_foot_N=round(total_n / 4, 1), foot_pressure_MPa=round(total_n / 4 / worst_area, 3),
                       deck_sag_mm=round(2 * 0.025 * q * a ** 4 / D, 1))
    out = os.path.join(HERE, "..", "checks", "top_report.json")
    json.dump(rep, open(out, "w"), indent=1)
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
